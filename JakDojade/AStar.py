import math
import pickle
from funcs import *


# ------------------- Unified A* Algorithm -------------------

def a_star_proper(start_station,end_station,start_time,mode="TIME"):
    with open("graph.pickle", "rb") as f:
        adjacency, station_coords = pickle.load(f)

    mode = mode.upper()
    transfer_penalty = 0
    if mode == "TIME":
        transfer_penalty = 0  # 0 minutes penalty for transferring

    elif mode == "TRANSFERS":
        transfer_penalty = 1800  # 30 minutes penalty for transferring

    return a_star(adjacency,start_station,end_station,start_time,station_coords,transfer_penalty,min_wait=120)
def a_star(adjacency, start_station, end_station, start_time, station_coords,transfer_penalty,min_wait,start_node=None):
    """
    Unified A* search for a route from start_station to end_station.

    Parameters:
      - mode: "TIME" minimizes travel time (in seconds) with a transfer penalty of 2 minutes;
              "TRANSFERS" minimizes transfers by adding a penalty of 30 minutes (1800 s) for transfers.
    Returns the end Node (with final arrival time and parent pointers) so that the path can be reconstructed.
    """




    heuristic_fn = lambda s: heuristic(s, station_coords, end_station)


    # Initialize start node.
    if start_node is None:
        start_node = Node(start_station, g=0,total=0, arrival_time=start_time, parent=None, edge=None,current_line=None)
    else:
        new_start_node = Node(start_station,g=0,total=0,arrival_time=start_node.arrival_time,parent=None,edge=None,current_line=start_node.current_line)
        new_start_node.parent_station_name = start_node.parent.station_name

        start_node = new_start_node

    start_node.h = heuristic_fn(start_station)
    start_node.f = start_node.total + start_node.h
    open_list = [start_node]
    closed_list = []

    while open_list:
        current = min(open_list, key=lambda node: node.f)
        if current.station_name == end_station:
            return current  # Goal reached

        open_list.remove(current)
        closed_list.append(current)
        #print(current)
        #print(open_list)
        #print(adjacency[start_station])
        # print(closed_list)
        # print(len(open_list))
        neighbors = get_neighbors(current, adjacency, transfer_penalty,min_wait=min_wait)
        #print(neighbors)
        for (nbr, edge_cost, new_total, new_arrival, edge_info)  in neighbors:
            #print(nbr, edge_cost, new_total, new_arrival, edge_info)
            tentative_total = new_total

            candidate_line = edge_info[0]
            parent_station_name = edge_info[3]


            neighbor_in_open = next(
                (n for n in open_list if n.station_name == nbr and n.current_line == candidate_line and n.parent_station_name  == parent_station_name), None)
            neighbor_in_closed = next(
                (n for n in closed_list if n.station_name == nbr and n.current_line == candidate_line  and n.parent_station_name  == parent_station_name), None)



            if neighbor_in_open is None and neighbor_in_closed is None:
                neighbor = Node(nbr, g=edge_cost, total=tentative_total, h=heuristic_fn(nbr), parent=current,
                                edge=edge_info, arrival_time=new_arrival)
                #print(f"neighbor: {neighbor}")
                if current.current_line is None:
                    neighbor.current_line = edge_info[0]
                else:
                    neighbor.current_line = current.current_line if current.current_line == edge_info[0] else edge_info[
                        0]

                neighbor.f = neighbor.total + neighbor.h
                open_list.append(neighbor)
            else:
                existing = neighbor_in_open if neighbor_in_open is not None else neighbor_in_closed
                tentative_f = tentative_total + heuristic_fn(nbr)

                if tentative_f < existing.total+existing.h:
                    #print(f"existing:{existing}")
                    existing.g = edge_cost
                    existing.total= tentative_total
                    existing.arrival_time = new_arrival
                    existing.parent = current
                    existing.edge = edge_info
                    existing.h = heuristic_fn(nbr)
                    existing.f = existing.total + existing.h
                    if neighbor_in_closed is not None:
                        closed_list.remove(existing)
                        open_list.append(existing)
    return None






def a_star_cached(route_cache,adjacency, start_station, end_station, start_time, station_coords,transfer_penalty,min_wait,start_node=None):
    key = (start_station, end_station, start_time,start_node)
    if key in route_cache:
        print("Cache hit")
        node = route_cache[key]
        return node
    end_node = a_star(adjacency, start_station, end_station, start_time, station_coords,transfer_penalty=transfer_penalty,min_wait=min_wait,start_node=start_node)
    route_cache[key] = end_node
    return end_node




def a_star_cached_print_stats(route_cache,adjacency, start_station, end_station, start_time, station_coords,transfer_penalty,min_wait,start_node=None):
    end_node = a_star_cached(route_cache,adjacency, start_station, end_station, start_time, station_coords,transfer_penalty=transfer_penalty,min_wait=min_wait,start_node=start_node)
    #print(f"end_node= {end_node}")
    print_whole_stats(end_node,
                      start_station=start_station,
                      end_station=end_station,
                      start_time=start_time,
                      )

    return end_node
