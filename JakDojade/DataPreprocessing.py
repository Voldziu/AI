

import pandas as pd
from funcs import *
import pickle

csv_file_name = "connection_graph.csv"

def data_preprocessing(csv_filename):
    df = pd.read_csv(csv_filename)

    df['departure_time'] = df['departure_time'].apply(parse_time)
    df['arrival_time'] = df['arrival_time'].apply(parse_time)
    #print(df[['departure_time','arrival_time']])

    return df





if __name__ == "__main__":
    df = data_preprocessing(csv_file_name)
    adjacency, station_coords = build_adjacency(df)
    with open("graph.pickle", "wb") as f:
        pickle.dump((adjacency, station_coords), f)