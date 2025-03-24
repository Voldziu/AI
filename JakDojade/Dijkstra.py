from funcs import *

from funcs import *  # This imports your parse_time, format_time, haversine, Node, etc.
import heapq
from bisect import bisect_left
from collections import defaultdict


import heapq

def dijkstra(
    adjacency,
    start_station,
    end_station,
    start_time,
    min_wait=120
):
    """
    Dijkstra algorithm that matches A* behavior (but no heuristic).
    It uses station+line+parent to keep states distinct.
    """



    start_node = Node(
        station_name=start_station,
        g=0,                # cost of the edge leading here
        total=0,            # total cost from start
        h=0,                # no heuristic in Dijkstra
        parent=None,
        edge=None,
        arrival_time=start_time,
        current_line=None
    )

    open_heap = []
    heapq.heappush(open_heap, (start_node.total, start_node))


    best_map = {}
    key = (start_node.station_name, start_node.current_line, "")
    best_map[key] = start_node
    nodes =0
    edges =0
    while open_heap:
        _, current = heapq.heappop(open_heap)


        if current.station_name == end_station:
            return nodes,edges,current


        ckey = (current.station_name, current.current_line, current.parent_station_name)
        if current.total > best_map[ckey].total:
            continue


        neighbors = get_neighbors(
            current,
            adjacency,
            transfer_penalty=0,
            min_wait=min_wait
        )
        for (nbr_station, edge_cost, new_total, new_arrival, edge_info) in neighbors:

            candidate_line = edge_info[0]
            candidate_parent_station_name = edge_info[3]

            # Build a new node for the neighbor
            neighbor_node = Node(
                station_name=nbr_station,
                g=edge_cost,
                total=new_total,
                h=0,            # no heuristic
                            # not used
                parent=current,
                edge=edge_info,
                arrival_time=new_arrival,
                current_line=None,  # assigned below
            )
            # If parent had no line, we adopt the new line. Otherwise see if it changes.
            if current.current_line is None:
                neighbor_node.current_line = candidate_line
            else:
                neighbor_node.current_line = (
                    current.current_line if current.current_line == candidate_line
                    else candidate_line
                )

            neighbor_node.parent_station_name = current.station_name

            # Check if this is our best path to (nbr_station, line, parent_station).
            nkey = (
                neighbor_node.station_name,
                neighbor_node.current_line,
                neighbor_node.parent_station_name
            )
            if nkey not in best_map or neighbor_node.total < best_map[nkey].total:
                best_map[nkey] = neighbor_node
                heapq.heappush(open_heap, (neighbor_node.total, neighbor_node))

            edges+=1

        nodes+=1
    return nodes,edges,None

