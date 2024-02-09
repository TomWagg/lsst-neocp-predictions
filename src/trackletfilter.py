from astropy.coordinates import angular_separation
import numpy as np

DEG_TO_RAD = np.pi / 180
DEG_TO_AS = 3600
DAY_TO_MIN = 1440

def ensure_min_obs(df, min_obs=3):
    """Ensure that there are at least `min_obs` observations for each object in the dataframe"""
    # calculate the number of observations for each object
    group_sizes = df.groupby("ObjID").size()

    # if the dataframe is already indexed by ObjID then we can just use that
    if "ObjID" in df.columns:
        df.set_index("ObjID", inplace=True)

    # drop any objects that don't have enough observations
    df.drop(group_sizes[group_sizes < min_obs].index, inplace=True)
    df.reset_index(inplace=True)
    
    return df

def filter_observations(df, min_obs=2, min_arc=1, max_time=90):
    """Filter out any observations that don't meet the criteria"""    
    # first remove any that don't show up at least min_obs times
    df = ensure_min_obs(df, min_obs=min_obs)
    
    # store a new column that tracks the number of observations
    df["n_obs"] = df["ObjID"].map(df["ObjID"].value_counts())
    
    # remove any objects that don't have a minimum arc length or time between tracklets
    df = filter_tracklets(df, min_arc=min_arc, max_time=max_time)
    return df
        
def filter_tracklets(df, min_arc=1, max_time=90):
    # create a mask based on min arc length, max time between shortest pair
    mask = df.groupby(["ObjID", "night"]).apply(_filter_tracklets_applier, min_arc, max_time)

    # re-index to match the mask
    df_multiindex = df.set_index(["ObjID", "night"]).sort_index()

    # get matching items from the original df and then reset the index to what it was
    df = df_multiindex.loc[mask[mask].index].reset_index()

    return df


def _filter_tracklets_applier(df, min_arc=1, max_time=90):
    """Apply the filter_tracklets function to a group of tracklets (for df.groupby().apply())"""
    sep = angular_separation(df["AstRA(deg)"].iloc[0] * DEG_TO_RAD,
                             df["AstDec(deg)"].iloc[0] * DEG_TO_RAD,
                             df["AstRA(deg)"].iloc[-1] * DEG_TO_RAD,
                             df["AstDec(deg)"].iloc[-1] * DEG_TO_RAD) / DEG_TO_RAD * DEG_TO_AS
    t = df["FieldMJD_TAI"].diff().min() * DAY_TO_MIN
    return (sep > min_arc) & (t < max_time)
