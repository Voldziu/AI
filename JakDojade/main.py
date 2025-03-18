from funcs import *
from DataPreprocessing import *
from AStar import a_star
from Dijkstra import dijkstra

csv_file_name = "connection_graph.csv"


if __name__ == "__main__":
    with open("graph.pickle", "rb") as f:
        adjacency, station_coords = pickle.load(f)
    START_STATION = 'Przyjaźni'
    END_STATION = 'Piastowska'
    # START_STATION = 'Stalowa'
    # END_STATION = 'pl. Legionów'
    START_TIME_STR = "19:00:00"
    START_TIME = parse_time(START_TIME_STR)

    end_node = a_star(adjacency, START_STATION, END_STATION, START_TIME, station_coords, mode="TIME")

    print_whole_stats(end_node,
                      start_station=START_STATION,
                      end_station=END_STATION,
                      start_time_str=START_TIME_STR,
                      )



