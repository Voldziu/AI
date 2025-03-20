from funcs import *

from funcs import *  # This imports your parse_time, format_time, haversine, Node, etc.
import heapq
from bisect import bisect_left
from collections import defaultdict


def dijkstra(adjacency, start_station, end_station, start_time, penalty=120):
    """
    Dijkstra algorithm implementation using get_neighbors.

    Parameters:
      - adjacency: dict mapping start_stop -> list of (dep_time, arr_time, line, next_stop)
      - start_station: starting station name.
      - end_station: target station name.
      - start_time: time (in seconds after midnight) when you are at the start.
      - penalty: transfer penalty in seconds (e.g. 120 for 2 minutes).

    Returns:
      The final (goal) Node with final arrival_time, accumulated cost (total), and parent pointers,
      so that the route can be reconstructed. Returns None if no path is found.

    Note: In this implementation the accumulated cost ("total") is computed edge‐wise:
         For an edge from station A to B,
            edge_cost = (B.arr_time - candidate.dep_time) [if no transfer]
                     = (B.arr_time - candidate.dep_time) + penalty [if transferring]
         And new_total = current.total + edge_cost.
         We assume the start node has total = 0.
    """
    best_nodes = {}
    # Initialize the start node. Set total=0 and use start_time as the arrival_time (feasibility base).
    start_node = Node(start_station, g=0, total=0, h=0, parent=None, edge=None, arrival_time=start_time)
    start_node.current_line = None
    best_nodes[start_station] = start_node

    # Open list is a min-heap based on the accumulated cost (total). No heuristic is used.
    open_list = [start_node]

    while open_list:
        current = heapq.heappop(open_list)
        # If we've reached the goal, return current.
        if current.station_name == end_station:
            return current

        # (Optional) Skip if a better cost is already known.
        if current.total > best_nodes[current.station_name].total:
            continue

        # Use unified get_neighbors to generate neighbor information.
        for (nbr, edge_cost, new_total, new_arrival, edge_info) in get_neighbors(current, adjacency, penalty):
            # Only consider the candidate if its departure is feasible (already ensured in get_neighbors).
            if nbr not in best_nodes or new_total < best_nodes[nbr].total:
                new_node = Node(nbr, g=edge_cost, total=new_total, h=0, parent=current, edge=edge_info,
                                arrival_time=new_arrival)
                # Set current_line: if no ride yet, assign candidate line; else, if same then keep, else update.
                if current.current_line is None:
                    new_node.current_line = edge_info[0]
                else:
                    new_node.current_line = current.current_line if current.current_line == edge_info[0] else edge_info[
                        0]
                best_nodes[nbr] = new_node
                heapq.heappush(open_list, new_node)

    return None
