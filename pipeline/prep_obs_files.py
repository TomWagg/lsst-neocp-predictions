import pandas as pd
import os
from multiprocessing import Pool

import sys
sys.path.append("../src")

import trackletfilter

def prune_night_file(night, path="/epyc/projects/neocp-predictions/output/synthetic_obs"):
    df = pd.read_hdf(os.path.join(path, f"night_{night:04d}.h5"), key="df")
    df = df.sort_values(["ObjID", "FieldMJD_TAI"])
    df.reset_index(inplace=True, drop=True)
    
    filtered_df = trackletfilter.filter_observations(df, min_obs=3, min_arc=1, max_time=90)
    filtered_df.to_hdf(os.path.join(path, f"filtered_night_{night:04d}.h5"), key="df")

if __name__ == "__main__":
    nights = range(1, 366)
    with Pool(20) as p:
        p.map(prune_night_file, nights)