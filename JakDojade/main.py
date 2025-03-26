from funcs import *
from DataPreprocessing import *
from AStar import a_star, a_star_proper
from Dijkstra import dijkstra
from printing import *
import time
csv_file_name = "connection_graph.csv"


if __name__ == "__main__":
    with open("graph.pickle", "rb") as f:
        adjacency, station_coords = pickle.load(f)
    START_STATION = 'Wilczyce - Borowa'
    END_STATION = 'Rynek'
    # START_STATION = 'Stalowa'
    # END_STATION = 'pl. Legionów'
    START_TIME_STR = "23:20:00"
    START_TIME = parse_time(START_TIME_STR)

    calc_start_time = time.time()

    nodes,edges,end_node = dijkstra(adjacency,START_STATION, END_STATION, START_TIME)
    #nodes,edges,end_node = a_star_proper(START_STATION, END_STATION, START_TIME,mode="TRANSFERS")


    print_whole_stats(end_node,
                      start_station=START_STATION,
                      end_station=END_STATION,
                      start_time=START_TIME,
                      )

    calc_end_time = time.time()


    elapsed = calc_end_time- calc_start_time

    print(f"Calculation time: {elapsed} s")
    print(f"Nodes visited: {nodes}")
    print(f"Edges visited: {edges}")


