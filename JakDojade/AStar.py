from funcs import *


# ------------------- Unified A* Algorithm -------------------
def a_star(adjacency, start_station, end_station, start_time, station_coords, mode="TIME"):
    """
    Unified A* search for a route from start_station to end_station.

    Parameters:
      - mode: "TIME" minimizes travel time (in seconds) with a transfer penalty of 2 minutes;
              "TRANSFERS" minimizes transfers by adding a penalty of 30 minutes (1800 s) for transfers.
    Returns the end Node (with final arrival time and parent pointers) so that the path can be reconstructed.
    """
    mode = mode.upper()
    if mode == "TIME":
        transfer_penalty = 0  # 2 minutes penalty for transferring

    elif mode == "TRANSFERS":
        transfer_penalty = 1800  # 30 minutes penalty for transferring

    else:
        raise ValueError("Unknown mode: choose 'TIME' or 'TRANSFERS'")

    heuristic_fn = lambda s: heuristic(s, station_coords, end_station)

    # Initialize start node.
    start_node = Node(start_station, g=start_time, arrival_time=start_time, parent=None, edge=None)
    start_node.current_line = None
    start_node.h = heuristic_fn(start_station)
    start_node.f = start_node.g + start_node.h
    open_list = [start_node]
    closed_list = []

    while open_list:
        current = min(open_list, key=lambda node: node.f)
        if current.station_name == end_station:
            return current  # Goal reached

        open_list.remove(current)
        closed_list.append(current)

        for (nbr, new_cost, new_arrival, edge_info) in get_neighbors(current, adjacency, transfer_penalty):
            tentative_cost = new_cost
            neighbor_in_open = next((n for n in open_list if n.station_name == nbr), None)
            neighbor_in_closed = next((n for n in closed_list if n.station_name == nbr), None)

            if neighbor_in_open is None and neighbor_in_closed is None:
                neighbor = Node(nbr, g=tentative_cost, arrival_time=new_arrival, parent=current, edge=edge_info)
                # Set current_line: if current.current_line is None, assign candidate line; else propagate if same, else update.
                if current.current_line is None:
                    neighbor.current_line = edge_info[0]
                else:
                    neighbor.current_line = current.current_line if current.current_line == edge_info[0] else edge_info[
                        0]
                neighbor.h = heuristic_fn(nbr)
                neighbor.f = neighbor.g + neighbor.h
                open_list.append(neighbor)
            else:
                existing = neighbor_in_open if neighbor_in_open is not None else neighbor_in_closed
                if tentative_cost < existing.g:
                    existing.g = tentative_cost
                    existing.arrival_time = new_arrival
                    existing.parent = current
                    existing.edge = edge_info
                    existing.h = heuristic_fn(nbr)
                    existing.f = existing.g + existing.h
                    if neighbor_in_closed is not None:
                        closed_list.remove(existing)
                        open_list.append(existing)
    return None


