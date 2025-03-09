from funcs import *
from AStar import a_star
from Dijkstra import dijkstra

csv_file_name = "connection_graph.csv"


if __name__ == "__main__":
    adjacency,station_coords = build_adjacency(csv_file_name)
    START_STATION = "Stalowa"
    END_STATION = "Psie Pole (Rondo Lotników Polskich)"
    START_TIME_STR = "20:00:00"
    START_TIME = parse_time(START_TIME_STR)



    end_node = dijkstra(adjacency,START_STATION,END_STATION,START_TIME)
    #end_node = a_star(adjacency,START_STATION,END_STATION,START_TIME,station_coords,mode="TIME")

    if end_node is None:
        print("There's no connection between those stations.")
        sys.exit(1)


    path = reconstruct_path(end_node)
    if not path:
        print("No connection (parent invalid)")
        sys.exit(1)



    # Group consecutive segments by line
    grouped_path = group_segments(path)

    print(f"\t\t=== Route from {START_STATION} to {END_STATION}  ===\n")
    print_grouped_schedule(grouped_path)

    # Print total travel time
    total_travel_time = end_node.arrival_time - START_TIME
    print("\n=== Final cost ===", file=sys.stderr)
    print(
        f"Final travel time: {total_travel_time} s "
        f"(~{total_travel_time / 60:.1f} min)",
        file=sys.stderr
    )
