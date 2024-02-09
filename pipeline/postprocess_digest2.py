import pandas as pd
import sys
sys.path.append("/epyc/projects/neocp-predictions/src/")
import trackletfilter
from multiprocessing import Pool
import os

def create_final_file(night, path="/epyc/projects/neocp-predictions/output/"):
    if not os.path.isfile(os.path.join(path, f"digest2_output/night_{night:04d}.filtered.dat")):
        print("No digest2 file found for night {night:04d}")
        return
    else:
        print(f"Processing night {night:04d}")
    
    digest2_df = pd.read_csv(os.path.join(path, f"digest2_output/night_{night:04d}.filtered.dat"),
                                delim_whitespace=True).dropna()
    digest2_df.drop_duplicates(subset="Desig.", inplace=True)
    df = pd.read_hdf(os.path.join(path, f"synthetic_obs/filtered_night_{night:04d}.h5"), key="df")

    digest2_df["hex_id"] = digest2_df["Desig."]
    digest2_df.set_index("hex_id", inplace=True)
    
    df["scores"] = df["hex_id"].map(digest2_df["NEO"])
    df["ang_vel"] = df["hex_id"].map(df.groupby("hex_id").apply(trackletfilter.tracklet_speed))
    
    df.to_hdf(os.path.join(path, f"synthetic_obs/filtered_night_{night:04d}_with_scores.h5"), key="df")

if __name__ == "__main__":
    with Pool(20) as p:
        p.map(create_final_file, range(366))