import numpy as np
import pandas as pd
import os
from multiprocessing import Pool

import sys
sys.path.append("../src")

import trackletfilter
import magnitudes

def prune_night_file(night, path="/epyc/projects/neocp-predictions/output/synthetic_obs"):
    file_path = os.path.join(path, f"night_{night:04d}.h5")
    try:
        if os.path.isfile(file_path):
            # load the file and sort
            df = pd.read_hdf(file_path, key="df")
            df = df.sort_values(["ObjID", "FieldMJD_TAI"])
            df.reset_index(inplace=True, drop=True)
        
            # filter the tracklets and adjust filter dtype
            fdf = trackletfilter.filter_observations(df, min_obs=3, min_arc=1, max_time=90)
            fdf["optFilter"] = fdf["optFilter"].astype("str")

            # add object type and v_mag
            ot = np.repeat("unknown", len(fdf))
            for start, obj_type in zip(["S0", "S1", "CEN", "SL", "St5", "ST", "SS"],
                                    ["neo", "mba", "centaur", "comet", "trojan", "tno", "sdo"]):
                ot[fdf["ObjID"].str.startswith(start)] = obj_type
            fdf["obj_type"] = ot
            fdf["v_mag"] = magnitudes.convert_colour_mags(fdf["observedTrailedSourceMag"].values,
                                                                  out_colour="V",
                                                                  in_colour=fdf["optFilter"].values)
            
            # compute the angular velocity of each tracklet
            fdf["ang_vel"] = fdf["hex_id"].map(fdf.groupby("hex_id").apply(trackletfilter.tracklet_speed))

            # save the file
            fdf.to_hdf(os.path.join(path, f"filtered_night_{night:04d}.h5"), key="df")
        print(night, "done")
    except:
        print(night, "failed")

if __name__ == "__main__":
    nights = range(366)
    # nights = np.load("/epyc/projects/neocp-predictions/output/ten_year_target_nights.npy", allow_pickle=True)
    with Pool(30) as p:
        p.map(prune_night_file, nights)
