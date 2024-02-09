import pandas as pd
from astropy.coordinates import Angle
from astropy.time import Time
from os.path import isfile, join

def create_digest2_input(night,
                         in_path="/epyc/projects/neocp-predictions/output/synthetic_obs/",
                         out_path="/epyc/projects/neocp-predictions/output/digest2_output/"):

    file_path = join(in_path, f"filtered_night_{night:04d}.h5")

    # check if file exists, in case there's no data, write out an empty file
    if not isfile(file_path):
        with open(out_path + "night_{:04d}.obs".format(night), "w") as obs_file:
            pass
        return
    
    # read in the data
    nightly_obs = pd.read_hdf(file_path, key="df")
    
    if isfile(out_path + "night_{:04d}.obs".format(night)):
        print(f"Skipping night {night} because it already exists")
        return

    # convert RA and Dec to hourangles and MJD to regular dates
    ra_degrees = Angle(nightly_obs["AstRA(deg)"], unit="deg").hms
    dec_degrees = Angle(nightly_obs["AstDec(deg)"], unit="deg").hms
    datetimes = Time(nightly_obs["FieldMJD_TAI"], format="mjd").datetime

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
        lines[i] += "{:4.0f} {:02.0f} {:08.5f} ".format(t.year, t.month, t.day + nightly_obs.iloc[i]["FieldMJD_TAI"] % 1.0)

        # convert RA to HH MM SS.ddd
        lines[i] += "{:02.0f} {:02.0f} {:06.3f}".format(ra_degrees.h[i], ra_degrees.m[i], ra_degrees.s[i])

        # convert Dec to sHH MM SS.dd
        lines[i] += "{:+03.0f} {:02.0f} {:05.2f}".format(dec_degrees.h[i], abs(dec_degrees.m[i]), abs(dec_degrees.s[i]))

        # leave some blank columns
        lines[i] += " " * 9

        # add the magnitude and filter (right aligned)
        lines[i] += "{:04.1f}  {}".format(nightly_obs.iloc[i]["observedTrailedSourceMag"], nightly_obs.iloc[i]["optFilter"])

        # add some more spaces and an observatory code
        lines[i] += " " * 5 + "I11" + "\n"

    # write that to a file
    with open(out_path + "night_{:04d}.obs".format(night), "w") as obs_file:
        obs_file.writelines(lines)
