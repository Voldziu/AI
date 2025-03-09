from funcs import *






# ----- Main a_star Function that Chooses the Mode -----
def a_star(adjacency,start_station, end_station,start_time,station_coords, mode="TIME"):
    """
    A* search for a route from start_station to end_station.

    Parameters:
      - mode: "time" minimizes travel time (seconds), "transfers" minimizes the number of transfers.

    Returns the end Node (with final arrival time and parent pointers).
    """
    if mode == "TIME":
        return a_star_time(start_station, end_station, adjacency, station_coords, start_time)
    elif mode == "TRANSFERS":
        return a_star_transfers(start_station, end_station, adjacency, station_coords, start_time)
    else:
        raise ValueError("Unknown mode: choose 'time' or 'transfers'")


# ----- A* algorithm  -----
def a_star_time(start_station, end_station, adjacency, station_coords, start_time):
    """
    A* search for fastest route (minimal travel time).
    The cost is measured in seconds (arrival time).
    """
    start_node = Node(start_station,g=start_time, arrival_time=start_time, parent=None, edge=None)
    start_node.f = start_node.g + heuristic(start_station, station_coords, end_station)
    open_list = [start_node]
    closed_list = []

    while open_list:
        # Select node with lowest f
        current = min(open_list, key=lambda node: node.f)
        if current.station_name == end_station:
            return current  # Goal reached

        open_list.remove(current)
        closed_list.append(current)

        for (nbr_stop, new_cost, new_arrival, edge_info) in get_neighbors(current, adjacency,mode="TIME"):
            tentative_cost = new_cost
            # Check if neighbor exists in open or closed (by station name)
            neighbor_in_open = next((n for n in open_list if n.station_name == nbr_stop), None)
            neighbor_in_closed = next((n for n in closed_list if n.station_name == nbr_stop), None)

            if neighbor_in_open is None and neighbor_in_closed is None:
                neighbor = Node(nbr_stop, g=tentative_cost, arrival_time=new_arrival, parent=current, edge=edge_info)
                neighbor.f = neighbor.g + heuristic(nbr_stop, station_coords, end_station)
                open_list.append(neighbor)
            else:
                existing = neighbor_in_open if neighbor_in_open is not None else neighbor_in_closed
                if tentative_cost < existing.g:
                    existing.g = tentative_cost
                    existing.arrival_time = new_arrival
                    existing.parent = current
                    existing.edge = edge_info
                    existing.f = existing.g + heuristic(nbr_stop, station_coords, end_station)
                    if neighbor_in_closed is not None:
                        closed_list.remove(existing)
                        open_list.append(existing)
    return None


# ----- A* for "transfers" mode -----
def a_star_transfers(start_station, end_station, adjacency, station_coords, start_time):
    """
    A* search for a route minimizing the number of transfers.
    The cost (g) is the number of transfers (an integer), and we track actual arrival times.
    The heuristic is 0 (i.e. uniform-cost search in terms of transfers).

    Returns the goal Node (which contains the final arrival time and parent pointer)
    so that the path can be reconstructed.
    """
    # Start with 0 transfers; arrival_time is start_time.
    start_node = Node(start_station, g=0, h=0, parent=None, edge=None, arrival_time=start_time)
    start_node.current_line = None  # No line chosen yet.
    start_node.f = start_node.g  # heuristic = 0
    open_list = [start_node]
    closed_list = []

    while open_list:
        current = min(open_list, key=lambda node: node.f)
        if current.station_name == end_station:
            return current  # Goal reached

        open_list.remove(current)
        closed_list.append(current)

        for (nbr_stop, new_cost, new_arrival, edge_info) in get_neighbors(current, adjacency, mode="TRANSFERS"):
            new_line = edge_info[0]
            tentative_cost = new_cost  # new_cost already includes transfer count

            # Check if a neighbor with the same station and same current line exists.
            neighbor_in_open = next((n for n in open_list
                                     if n.station_name == nbr_stop and getattr(n, "current_line", None) == new_line),
                                    None)
            neighbor_in_closed = next((n for n in closed_list
                                       if n.station_name == nbr_stop and getattr(n, "current_line", None) == new_line),
                                      None)

            if neighbor_in_open is None and neighbor_in_closed is None:
                neighbor = Node(nbr_stop, g=tentative_cost, h=0, parent=current, edge=edge_info,
                                arrival_time=new_arrival)
                neighbor.current_line = new_line
                neighbor.f = neighbor.g  # heuristic = 0
                open_list.append(neighbor)
            else:
                existing = neighbor_in_open if neighbor_in_open is not None else neighbor_in_closed
                # Update if a route with a lower transfer count is found,
                # or if transfer count is equal and arrival is earlier.
                if tentative_cost < existing.g or (
                        tentative_cost == existing.g and new_arrival < existing.arrival_time):
                    existing.g = tentative_cost
                    existing.arrival_time = new_arrival
                    existing.parent = current
                    existing.edge = edge_info
                    existing.current_line = new_line
                    existing.f = existing.g  # heuristic = 0
                    if neighbor_in_closed is not None:
                        closed_list.remove(existing)
                        open_list.append(existing)
    return None





