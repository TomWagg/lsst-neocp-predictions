import numpy as np
import pandas as pd
import os
from multiprocessing import Pool

import sys
sys.path.append("../src")

import trackletfilter

def prune_night_file(night, path="/epyc/projects/neocp-predictions/output/synthetic_obs"):
    file_path = os.path.join(path, f"night_{night:04d}.h5")
    try:
        if os.path.isfile(file_path):
            df = pd.read_hdf(file_path, key="df")
            df = df.sort_values(["ObjID", "FieldMJD_TAI"])
            df.reset_index(inplace=True, drop=True)
        
            filtered_df = trackletfilter.filter_observations(df, min_obs=3, min_arc=1, max_time=90)
            filtered_df.to_hdf(os.path.join(path, f"filtered_night_{night:04d}.h5"), key="df")
        print(night, "done")
    except:
        print(night, "failed")

if __name__ == "__main__":
    nights = range(366)
    # nights = np.load("/epyc/projects/neocp-predictions/output/ten_year_target_nights.npy", allow_pickle=True)
    with Pool(30) as p:
        p.map(prune_night_file, nights)
