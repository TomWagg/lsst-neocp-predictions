import numpy as np
import pandas as pd
import difi
import time
import os

def create_findable_obs_tables(min_nights=3, detection_window=15, nights=range(366),
                               out_path="../output/findable_obs_year_1.h5"):
    print("Let the games begin...")
    start = time.time()

    # get all of the observations
    obs_dfs = np.array([None for _ in nights])
    for i, night in enumerate(nights):
        file_path = f"../output/synthetic_obs/filtered_night_{night:04d}_with_scores_trimmed.h5"
        if os.path.exists(file_path):
            obs_dfs[i] = pd.read_hdf(file_path)[["FieldMJD_TAI", "night", "hex_id"]].sort_values("FieldMJD_TAI")

    obs_dfs = obs_dfs[obs_dfs != None]
    all_obs = pd.concat(obs_dfs)
    all_obs["obs_id"] = np.arange(len(all_obs))
    all_obs.reset_index(inplace=True)

    print(f"Obs file done, {time.time() - start:1.1f}s elapsed")
    obs_done = time.time()

    # run difi
    _, findable_obs, _ = difi.analyzeObservations(
        observations=all_obs,
        classes=None,
        metric="nightly_linkages",
        column_mapping={"obs_id": "obs_id", "truth": "hex_id", "night": "night", "time": "FieldMJD_TAI"}
    )

    print(f"Difi done, {time.time() - obs_done:1.1f}s elapsed")
    difi_done = time.time()

    # hack around difi to check if the window is actually satisfied and on which night it is first detected
    findable_obs["night_detected"] = np.zeros(len(findable_obs)).astype(int)
    findable_obs["actually_findable"] = np.repeat(True, len(findable_obs))

    for ind, row in findable_obs.iterrows():
        obs_nights = np.unique(all_obs.loc[row["obs_ids"]]["night"].values)
        diff_nights = np.diff(obs_nights)
        window_sizes = np.array([sum(diff_nights[i:i + min_nights - 1])
                                for i in range(len(diff_nights) - min_nights + 2)])

        # record whether any are short enough
        if np.any(window_sizes <= detection_window):
            detection_obs_ind = np.arange(len(window_sizes))[window_sizes <= detection_window][0] + min_nights - 1
            findable_obs.loc[ind, "night_detected"] = obs_nights[detection_obs_ind]
        else:
            findable_obs.loc[ind, "night_detected"] = -1
            findable_obs.loc[ind, "actually_findable"] = False

    findable_obs = findable_obs[findable_obs["actually_findable"]].set_index("hex_id")["night_detected"]
    findable_obs.to_hdf(out_path, key="df")

    print(f"All done! {time.time() - difi_done:1.1f}s elapsed since difi")
    print(f"\nIt took {time.time() - start:1.1f}s in total.")

    return findable_obs


if __name__ == "__main__":
    create_findable_obs_tables()