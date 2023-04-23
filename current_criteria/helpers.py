import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile


def get_specific_neo_score(path, file_name):
    if file_name.endswith(".filtered.dat"):
        if isfile(path + file_name):
            with open(path + file_name, "r") as f:
                ignore_me = f.readline().rstrip() == ""
            if not ignore_me:
                df = pd.read_csv(path + file_name, delim_whitespace=True).dropna()
                return df["NEO"].values, df["Desig."].values

    return None, None


def get_neo_scores(path, night=None):
    if night is None:
        neo_scores = np.array([])
        ids = np.array([])
        files = listdir(path)

        for file_name in files:
            neo, ID = get_specific_neo_score(path, file_name)
            if neo is not None:
                neo_scores = np.concatenate((neo_scores, neo))
                ids = np.concatenate((ids, ID))
    else:
        neo_scores, ids = get_specific_neo_score(path, f"night_{night:03d}.filtered.dat")
    return neo_scores, ids
