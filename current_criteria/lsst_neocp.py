import pandas as pd
from astropy.coordinates import Angle, SkyCoord
from astropy.time import Time
import astropy.units as u
import numpy as np
from os import listdir
from os.path import isfile
import argparse
import time
from multiprocessing import Pool
from itertools import repeat
import subprocess


def print_time_delta(start, end, label):
    delta = end - start
    print(f"  {int(delta // 60):02d}m{int(delta % 60):02d}s - ({label})")


f2n = np.load("/gscratch/dirac/tomwagg/the-sky-is-falling/current_criteria/f2n.npy", allow_pickle=True)


def find_first_file(night_range):
    for night in night_range:
        for i, f in enumerate(f2n):
            if night in f:
                return i


def find_last_file(night_range):
    file = None
    for night in night_range:
        for i, f in enumerate(f2n):
            if night in f:
                file = i
    return file


def split_observations(obs, n_cores=28):
    """Split observations over many cores but keep groups of tracklets together so that they get masked
    correctly!

    Parameters
    ----------
    obs : `pandas.DataFrame`
        Observation table
    n_cores : `int`, optional
        Number of cores to split over, by default 28

    Returns
    -------
    split_obs : `list`
        List of dataframes with length `n_cores` and each with size approximately `len(obs) / n_cores`
    """
    indices = np.array([None for _ in range(n_cores - 1)])
    i, cursor, dx = 0, 0, len(obs) // n_cores
    ids = obs["ObjID"].values

    while i < n_cores - 1:
        cursor += dx

        # break early if we go beyond the bounds of the array
        if cursor > len(ids) - 1:
            indices = indices[:-1]
            break

        # keep incrementing until the ObjID is not the same (to avoid breaking tracklets)
        while ids[cursor] == ids[cursor + 1]:
            cursor += 1
        indices[i] = cursor
        i += 1

    return np.split(obs, indices)


def filter_observations(df, min_obs=2, min_arc=1, max_time=90):
    # create a mask based on min # of obs, min arc length, max time between shortest pair
    mask = df.groupby(["ObjID", "night"]).apply(filter_tracklets, min_obs, min_arc, max_time)

    # re-index to match the mask
    df_multiindex = df.set_index(["ObjID", "night"]).sort_index()

    # get matching items from the original df and then reset the index to what it was
    df = df_multiindex.loc[mask[mask].index].reset_index()
    return df


def filter_tracklets(df, min_obs=2, min_arc=1, max_time=90):
    init = SkyCoord(ra=df["AstRA(deg)"].iloc[0], dec=df["AstDec(deg)"].iloc[0], unit="deg")
    final = SkyCoord(ra=df["AstRA(deg)"].iloc[-1], dec=df["AstDec(deg)"].iloc[-1], unit="deg")

    return np.logical_and.reduce((len(df) >= min_obs,
                                  init.separation(final).to(u.arcsecond).value > min_arc,
                                  df["FieldMJD"].diff().min() * 1440 < max_time))


def create_digest2_input(in_path="/data/epyc/projects/jpl_survey_sim/10yrs/detections/march_start_v2.1/S0/",
                         out_path="neo/", night_zero=60217, start_night=0, final_night=31, timeit=False,
                         min_obs=2, min_arc=1, max_time=90, s3m_path="../catalogues/s3m_initial.h5",
                         n_cores=28):

    print(f"Doing digest2 stuff for nights {start_night} to {final_night}")

    if timeit:
        start = time.time()

    # convert all S3M IDs to hex so they fit
    s3m = pd.read_hdf(s3m_path)
    hex_ids = np.array([f'{num:07X}' for num in np.arange(len(s3m.index.values))])
    s3m_to_hex7 = dict(zip(s3m.index.values, hex_ids))

    if timeit:
        print_time_delta(start, time.time(), label="S3M Mapping Creation")
        start = time.time()

    night, file = start_night, find_first_file(range(start_night, final_night))
    files = sorted(listdir(in_path[0])) if isinstance(in_path, list) else sorted(listdir(in_path))
    columns_to_keep = ["ObjID", "FieldMJD", "AstRA(deg)", "AstDec(deg)", "filter",
                       "MaginFilter", "AstrometricSigma(mas)", "PhotometricSigma(mag)"]

    # flags for whether to move on to the next file and whether to append or not
    next_file = True
    append = False
    nightly_obs = None

    # in case there's no data, write out an empty file
    if file is None:
        with open(out_path + "night_{:03d}.obs".format(night), "w") as obs_file:
            pass
        return


    # loop until all of the nights have been read in
    while night < final_night:
        # if reading the next file
        if next_file:
            if isfile(out_path + f"filtered_visit_{file:03d}.h5"):
                df = pd.read_hdf(out_path + f"filtered_visit_{file:03d}.h5", key="df")
                next_file = False

                if timeit:
                    print_time_delta(start, time.time(), label=f"Already exists! Reading file {file}")
                    start = time.time()
            else:
                # convert hdf to pandas and trim the columns to only keep relevant ones
                if isinstance(in_path, str):
                    df = pd.read_hdf(in_path + files[file])
                    df = df[columns_to_keep]
                else:
                    dfs = [None for i in range(len(in_path))]
                    for i in range(len(in_path)):
                        dfs[i] = pd.read_hdf(in_path[i] + files[file])
                        dfs[i] = dfs[i][columns_to_keep]
                    df = pd.concat(dfs)

                # create night column relative to night_zero
                df["night"] = (df["FieldMJD"] - 0.5).astype(int)
                df["night"] -= night_zero
                next_file = False

                df["hex_id"] = np.array([s3m_to_hex7[df["ObjID"].iloc[i]] for i in range(len(df))])

                if timeit:
                    print_time_delta(start, time.time(), label=f"Reading file {file}")
                    start = time.time()

                # sort by the object and then the time
                df = df.sort_values(["ObjID", "FieldMJD"])

                # drop any S3M objects that got replaced by the hybrid catalogue
                delete_s3m_ids = np.load("/gscratch/dirac/tomwagg/the-sky-is-falling/current_criteria/delete_s3m_ids.npy",
                                         allow_pickle=True)
                df.set_index("ObjID", inplace=True)
                df.drop(delete_s3m_ids, inplace=True, errors="ignore")
                df.reset_index(inplace=True)

                # mask out any bad tracklet groups
                # if more than one core is available then split the dataframe up and parallelise
                if n_cores > 1:
                    df_split = split_observations(df, n_cores=n_cores)

                    # update n_cores in case it is an off-by-one issue
                    n_cores = len(df_split)
                    pool = Pool(n_cores)
                    df = pd.concat(pool.starmap(filter_observations, zip(df_split,
                                                                         repeat(min_obs, n_cores),
                                                                         repeat(min_arc, n_cores),
                                                                         repeat(max_time, n_cores))))
                    pool.close()
                    pool.join()
                else:
                    df = filter_observations(df, min_obs=min_obs, min_arc=min_arc, max_time=max_time)

                if timeit:
                    print_time_delta(start, time.time(), label=f"Filtered visit file {file}")
                    start = time.time()

                # write the new file back out
                df.to_hdf(out_path + f"filtered_visit_{file:03d}.h5", key="df")

                if timeit:
                    print_time_delta(start, time.time(), label=f"Wrote file {file}")
                    start = time.time()

        if not isfile(out_path + "night_{:03d}.obs".format(night)) or append:
            # get only the rows on this night
            nightly_obs = df[df["night"] == night]

            # convert RA and Dec to hourangles and MJD to regular dates
            ra_degrees = Angle(nightly_obs["AstRA(deg)"], unit="deg").hms
            dec_degrees = Angle(nightly_obs["AstDec(deg)"], unit="deg").hms
            datetimes = Time(nightly_obs["FieldMJD"], format="mjd").datetime

            # match to 80 column format: https://www.minorplanetcenter.net/iau/info/OpticalObs.html
            # each line stars with 5 spaces
            lines = [" " * 5 for i in range(len(nightly_obs))]
            for i in range(len(nightly_obs)):
                # convert ID to its hex representation
                lines[i] += nightly_obs.iloc[i]["hex_id"]

                # add two spaces and a C (the C is important for some reason)
                lines[i] += " " * 2 + "C"

                # convert time to HH MM DD.ddddd format
                t = datetimes[i]
                lines[i] += "{:4.0f} {:02.0f} {:08.5f} ".format(t.year, t.month, t.day + nightly_obs.iloc[i]["FieldMJD"] % 1.0)

                # convert RA to HH MM SS.ddd
                lines[i] += "{:02.0f} {:02.0f} {:06.3f}".format(ra_degrees.h[i], ra_degrees.m[i], ra_degrees.s[i])

                # convert Dec to sHH MM SS.dd
                lines[i] += "{:+03.0f} {:02.0f} {:05.2f}".format(dec_degrees.h[i], abs(dec_degrees.m[i]), abs(dec_degrees.s[i]))

                # leave some blank columns
                lines[i] += " " * 9

                # add the magnitude and filter (right aligned)
                lines[i] += "{:04.1f}  {}".format(nightly_obs.iloc[i]["MaginFilter"], nightly_obs.iloc[i]["filter"])

                # add some more spaces and an observatory code
                lines[i] += " " * 5 + "I11" + "\n"

            # write that to a file
            with open(out_path + "night_{:03d}.obs".format(night), "a" if append else "w") as obs_file:
                obs_file.writelines(lines)
            append = False
        else:
            print(f"skipping obs creation for night {night} because it already exists")

        if timeit:
            print_time_delta(start, time.time(), label=f"Writing observations for night {night}")
            start = time.time()

        # if we've exhausted the file then move on
        if night >= df["night"].max():
            file += 1
            next_file = True

            # append obs next time
            append = True
        # if the file is still going then move to the next night
        else:
            if nightly_obs is None:
                nightly_obs = df[df["night"] == night]
            print(str(len(nightly_obs)) + " observations in night " + str(night))
            night += 1


def create_bash_script(out_path="neo/", start_night=0, final_night=31,
                       digest2_path="/data/epyc/projects/hybrid-sso-catalogs/digest2/", cpu_count=32):
    bash = ""
    loop_it = final_night > start_night + 1

    if loop_it:
        bash += "for NIGHT in " + " ".join([f"{i:03d}" for i in range(start_night, final_night)]) + "\n"
        bash += "do\n"
    else:
        bash += f"NIGHT={start_night:03d}\n"

    bash += 'echo "Now running night $NIGHT through digest2..."\n' + '\t' if loop_it else ''
    bash += f"time {digest2_path}digest2 -p {digest2_path} -c {digest2_path}MPC.config --cpu {cpu_count}"
    bash += f" {out_path}night_$NIGHT.obs > {out_path}night_$NIGHT.dat" + "\n"
    bash += f"grep -a -v tracklet {out_path}night_$NIGHT.dat > {out_path}night_$NIGHT.filtered.dat \n"

    if loop_it:
        bash += "done\n"

    return bash


def main():

    parser = argparse.ArgumentParser(description='Run digest2 on LSST mock observations')
    parser.add_argument('-i', '--in-path',
                        default="/data/epyc/projects/jpl_survey_sim/10yrs/detections/march_start_v2.1/S0/",
                        type=str, help='Path to the folder containing mock observations')
    parser.add_argument('-o', '--out-path', default="neo/", type=str,
                        help='Path to folder in which to place output')
    parser.add_argument('-S', '--s3m-path', default="../catalogues/s3m_initial.h5",
                        type=str, help='Path to S3m file')
    parser.add_argument('-d', '--digest2-path', default="/data/epyc/projects/hybrid-sso-catalogs/digest2/",
                        type=str, help='Path to digest2 folder')
    parser.add_argument('-z', '--night-zero', default=60217, type=int,
                        help='MJD value for the first night')
    parser.add_argument('-s', '--start-night', default=0, type=int,
                        help='First night to run through digest2')
    parser.add_argument('-f', '--final-night', default=31, type=int,
                        help='Last night to run through digest2')
    parser.add_argument('-mo', '--min-obs', default=2, type=int,
                        help='Minimum number of observations per night')
    parser.add_argument('-ma', '--min-arc', default=1, type=int,
                        help='Minimum arc length in arcseconds')
    parser.add_argument('-mt', '--max-time', default=90, type=int,
                        help='Maximum time between shortest pair of tracklets in night')
    parser.add_argument('-c', '--cpu-count', default=32, type=int,
                        help='How many CPUs to use for the digest2 calculations')
    parser.add_argument('-M', '--mba', action="store_true",
                        help="Replace in_path and out_path with defaults for MBAs")
    parser.add_argument('-Mh', '--mba-hyak', action="store_true",
                        help="Replace in_path and out_path with defaults for MBAs whilst on Hyak")
    parser.add_argument('-Nh', '--neo-hyak', action="store_true",
                        help="Replace in_path and out_path with defaults for NEOs whilst on Hyak")
    parser.add_argument('-t', '--timeit', action="store_true",
                        help="Whether to time the code and print it out")
    args = parser.parse_args()

    if args.mba:
        args.in_path = ["/data/epyc/projects/jpl_survey_sim/10yrs/detections/march_start_v2.1/S1_{:02d}/".format(i) for i in range(14)]
        args.out_path = "mba/"

    if args.mba_hyak:
        args.in_path = [f'/gscratch/dirac/tomwagg/simulated_obs/S1_{i:02d}/' for i in range(14)]
        args.out_path = "/gscratch/dirac/tomwagg/the-sky-is-falling/current_criteria/mba/"

    if args.neo_hyak:
        args.in_path = "/gscratch/dirac/tomwagg/simulated_obs/S0/"
        args.out_path = "/gscratch/dirac/tomwagg/the-sky-is-falling/current_criteria/neo/"

    print(f"Creating digest2 files for nights {args.start_night} to {args.final_night} in {args.out_path}")

    create_digest2_input(in_path=args.in_path, out_path=args.out_path, timeit=args.timeit,
                         night_zero=args.night_zero, start_night=args.start_night,
                         final_night=args.final_night, min_obs=args.min_obs, min_arc=args.min_arc,
                         max_time=args.max_time, s3m_path=args.s3m_path, n_cores=args.cpu_count)

    script = create_bash_script(out_path=args.out_path, start_night=args.start_night,
                                final_night=args.final_night, digest2_path=args.digest2_path,
                                cpu_count=args.cpu_count)
    start = time.time()
    subprocess.call(script, shell=True)
    print_time_delta(start, time.time(), "total digest2 run")
    print("Hurrah!")


if __name__ == "__main__":
    main()
