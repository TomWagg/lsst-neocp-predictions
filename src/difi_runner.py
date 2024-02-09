import difi

import pandas as pd
import numpy as np

import argparse

NIGHT_ZERO = 60217
f2n = np.load("/epyc/projects/neocp-predictions/current_criteria/f2n.npy", allow_pickle=True)

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

def night_found(obs_ids, observations, column_mapping):
    return np.unique(observations.loc[obs_ids][column_mapping["night"]].values)[2]


def cla():
    parser = argparse.ArgumentParser(description='Run difi on a window of MBA observations')
    parser.add_argument('-s', '--start', default=0, type=int,
                        help='Start night of window')
    parser.add_argument('-w', '--window', default=15, type=int,
                        help='Length of detection window')
    parser.add_argument('-b', '--base', default="/data/epyc/projects/jpl_survey_sim/10yrs/v3.0/detections/", type=str,
                        help='Path to MBA folder')
    parser.add_argument('-o', '--out', default="./", type=str, help='Path to output folder')

    args = parser.parse_args()

    window_range = range(args.start, args.start + args.window)
    start_file = find_first_file(window_range)
    end_file = find_last_file(window_range)

    file_range = range(start_file, end_file + 1)

    mba_paths = [args.base + f"S1_{i:02d}/" for i in range(14)]
    all_mba_obs = [pd.read_hdf(mba_paths[i] + f"visit-{int(file * 1e4):07}.h5")
                   for file in file_range
                   for i in range(14)]

    obs = pd.concat(all_mba_obs)
    obs["night"] = (obs["FieldMJD"] - 0.5).astype(int) - NIGHT_ZERO
    obs.sort_values("FieldMJD", inplace=True)

    # drop any S3M objects that got replaced by the hybrid catalogue
    delete_s3m_ids = np.load("/gscratch/dirac/tomwagg/the-sky-is-falling/current_criteria/delete_s3m_ids.npy",
                                allow_pickle=True)
    obs.set_index("ObjID", inplace=True)
    obs.drop(delete_s3m_ids, inplace=True, errors="ignore")
    obs.reset_index(inplace=True)

    observations = obs[["ObjID", "night", "FieldMJD"]]
    observations.reset_index(drop=True, inplace=True)
    observations["obs_id"] = observations.index.values

    observations = observations[(observations["night"] >= args.start)
                                & (observations["night"] < args.start + args.window)]

    column_mapping = {
        "obs_id": "obs_id",
        "truth": "ObjID",
        "time": "FieldMJD",
        "night": "night"
    }

    all_truths, findable_obs, summary = difi.analyzeObservations(observations=observations,
                                                                 metric="nightly_linkages",
                                                                 column_mapping=column_mapping)

    findable_obs["night_found"] = findable_obs["obs_ids"].apply(night_found,
                                                                observations=observations,
                                                                column_mapping=column_mapping)

    np.save(args.out + f"difi_MBAs_ids_{args.start:04d}.npy", findable_obs["ObjID"].values.astype("a9"))
    np.save(args.out + f"difi_MBAs_nfs_{args.start:04d}.npy", findable_obs["night_found"].values.astype(int))

if __name__ == "__main__":
    cla()
