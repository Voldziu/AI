
import random
from AStar import *
import pickle
from funcs import *

import random


def get_neighbors_tabu_slice(solution: [int], slice_size: int):
    """

    """
    neighbors = []
    n = len(solution)
    for i in range(n - 1):
        for j in range(i + 1, n):
            neighbor = solution.copy()
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            move = (i, j)
            neighbors.append((move, neighbor))

    if slice_size >= len(neighbors):
        return neighbors
    else:
        neighbors= random.sample(neighbors, slice_size)
        return neighbors


def tabu_search_alg(init_solution, cost_fn, step_limit, op_limit, tabu_size, epsilon):
    """
    Tabu Search for the Traveling Salesman Problem.

    Parameters:
      cities: list of integers representing cities.
      cost_fn: an abstract cost function that takes a solution (list of ints) and returns a numeric cost.
               (For example, the cost can be the total travel time or the number of transfers.)
      step_limit: maximum number of overall iterations.
      op_limit: number of inner-loop iterations per outer-loop iteration.
      tabu_size: maximum number of moves to store in the tabu list.
      epsilon: aspiration threshold; a tabu move is allowed if the candidate solution’s cost is lower than the current solution’s cost by at least epsilon.

    """
    solution_cache ={}
    def cache_cost(solution):
        solution_tuple = tuple(solution)
        if solution_tuple in solution_cache:
            return solution_cache[solution_tuple]
        else:
            cost = cost_fn(solution)
            solution_cache[solution_tuple] = cost
            return cost

    # Step 1: k = 0
    k = 0
    # Step 2: Generate a random initial solution s.
    current = init_solution.copy()
    random.shuffle(current)
    # Step 3: Set best (global) solution s* = s.
    best_solution = current.copy()

    best_cost = cost_fn(best_solution)

    solution_cache[tuple(best_solution)] = best_cost

    # Step 4: Initialize the Tabu list T as an empty list.
    tabu_list = []

    while k < step_limit:

        i = 0
        current_cost = cache_cost(current)
        while i < op_limit:
            # Step 8: Determine the neighborhood N(s) using simple swap moves.
            neighborhood = get_neighbors_tabu_slice(current,slice_size=10)
            candidate = None
            candidate_move = None
            candidate_cost = float('inf')
            current_cost = cache_cost(current)
            # Evaluate each neighbor:
            for move, neighbor in neighborhood:
                c = cache_cost(neighbor)
                # If the move is tabu (i.e. present in tabu_list) and does not satisfy aspiration, skip it.
                if move in tabu_list and c >= current_cost - epsilon:
                    continue
                if c < candidate_cost:
                    candidate = neighbor.copy()
                    candidate_move = move
                    candidate_cost = c

            # Step 10: Update Tabu list with the chosen move.
            tabu_list.append(candidate_move)
            if len(tabu_list) > tabu_size:
                tabu_list.pop(0)
            # Step 11: If candidate improves current solution, update current.
            if candidate_cost < current_cost:
                current = candidate.copy()

            i += 1
            k += 1
        # Step 15: If the current solution is better than the best known, update best_solution.
        if current_cost < best_cost:
            best_solution = current.copy()
            best_cost = current_cost
    return best_solution, best_cost


def tabu_search(start_station,stations_string,start_time,mode="TIME"):
    route_cache = {}
    transfer_penalty = 0
    if mode == "TIME":
        transfer_penalty = 0  # 0 minutes penalty for transferring

    elif mode == "TRANSFERS":
        transfer_penalty = 1800  # 30 minutes penalty for transferring

    with open("graph.pickle", "rb") as f:
        adjacency, station_coords = pickle.load(f)

    station_names = stations_string.split(";")
    n = len(station_names)
    init_solution = list(range(n))
    random.shuffle(init_solution)
    cost_fn = lambda candidate_solution,min_wait: costAStar(
    route_cache,adjacency, start_time, start_station,station_names, station_coords, candidate_solution,transfer_penalty,min_wait
)

    best_solution, best_cost = tabu_search_alg(
        init_solution=init_solution,
        cost_fn= lambda candidate_solution: cost_fn(candidate_solution,120),
        step_limit=100,
        op_limit= 30,
        tabu_size=10*n,
        epsilon=120,


    )

    return best_solution,best_cost,route_cache




def costAStar(route_cache,adjacency,start_time,start_station,station_names,station_coords,candidate_solution:[int],transfer_penalty,min_wait):
    sorted_station_names = []
    for idx in candidate_solution:
        sorted_station_names.append(station_names[idx]) #in between station names (no start-end station)

    station_names = sorted_station_names

    cost =0
    num_of_inbetween_stations = len( station_names)

    end_node = a_star_cached_print_stats(route_cache,adjacency, start_station=start_station, end_station=station_names[0],
                                  start_time=start_time, station_coords=station_coords,transfer_penalty=transfer_penalty,min_wait=min_wait,start_node=None)

    connection_cost, arrival =end_node.total, end_node.arrival_time

    cost += connection_cost

    for i in range(num_of_inbetween_stations-1):
        #print(f"Polaczenie: {i}")
        end_node = a_star_cached_print_stats(route_cache,adjacency,start_station=station_names[i],end_station=station_names[i+1],start_time=arrival,station_coords=station_coords,transfer_penalty=transfer_penalty,min_wait=min_wait,start_node=end_node)
        connection_cost, arrival = end_node.total, end_node.arrival_time
        cost+=connection_cost
    cost +=connection_cost
    end_node = a_star_cached_print_stats(route_cache, adjacency, start_station=station_names[-1],
                                  end_station=start_station, start_time=arrival, station_coords=station_coords
                                  ,transfer_penalty=transfer_penalty,min_wait=min_wait,start_node=end_node)

    #print("koniec")

    connection_cost, arrival = end_node.total, end_node.arrival_time

    cost += connection_cost
    #print(f"Current cost: {cost}")
    return cost


def decode_and_print_solution(route_cache, start_station, stations_string, solution,
                              start_time):
    """

    """

    # Decode the solution into route order.
    station_list = stations_string.split(";")
    keys = route_cache.keys()
    print(station_list)
    print(solution)
    route_order = [start_station]
    for idx in solution:
        route_order.append(station_list[idx])
    # Close the cycle: return to start_station.
    route_order.append(start_station)
    print("Full route order:")
    print(" -> ".join(route_order))

    # For each leg, retrieve the cached route and print its itinerary.
    current_time = start_time
    total_cost = 0
    end_node = None
    for i in range(len(route_order) - 1):
        s = route_order[i]
        t = route_order[i + 1]
        key = (s, t, current_time,end_node)
        print(f"\nLeg {i + 1}: {s} -> {t} start_time: {current_time}")
        #print(key)
        if key in route_cache:
            end_node = route_cache[key]
            next_departure_time = end_node.arrival_time

            # Retrieve detailed route:
            itinerary = reconstruct_path(end_node)
            grouped = group_segments(itinerary)
            print_grouped_schedule(current_time,grouped)
            # Assume that cost for this leg is stored in end_node.total.
            leg_cost = end_node.total
            print(f"  Leg cost: {leg_cost} s")
            total_cost += leg_cost
            # Update current_time for the next leg (if needed).
            current_time = next_departure_time
        else:
            print("  [No cached route found for this leg]")

        # for key in keys:
        #     station,_,_,_ = key
        #     if( end_node and station==end_node.station_name):
        #         print(key)
    print(f"\nTotal route cost: {total_cost} s (~{total_cost / 60:.1f} min)")


if __name__=="__main__":
    with open("graph.pickle", "rb") as f:
        adjacency, station_coords = pickle.load(f)

    START_TIME_STR = "06:40:00"
    START_TIME = parse_time(START_TIME_STR)
    mode = 'TIME'




    #start_station = "Stalowa"
    start_station= "KRZYKI"
    #stations_string = "most Grunwaldzki;Kochanowskiego;Wiśniowa;PL. JANA PAWŁA II"
    #stations_string = "GRABISZYŃSKA (Cmentarz);ZOO;Urząd Wojewódzki (Muzeum Narodowe);most Grunwaldzki;Kochanowskiego;Wiśniowa;PL. JANA PAWŁA II"
    #stations_string = "GRABISZYŃSKA (Cmentarz);Fiołkowa;FAT;Hutmen;Bzowa (Centrum Historii Zajezdnia)"
    #stations_string = "Kliniki - Politechnika Wrocławska;BISKUPIN;Stalowa;Krucza;rondo Św. Ojca Pio;most Grunwaldzki;SĘPOLNO"
    stations_string = "Tarczyński Arena (Lotnicza);Niedźwiedzia;Bujwida;PARK POŁUDNIOWY;Na Niskich Łąkach;BISKUPIN"

    #N = 10
    #start_station, stations_string = prepare_n_stations_for_search(adjacency,N)


    best_solution, best_cost,route_cache = tabu_search(start_station,stations_string,START_TIME,mode="TIME")

    decode_and_print_solution(
                                route_cache=route_cache,
                                start_station=start_station,
                                stations_string=stations_string,
                                solution=best_solution,
                                start_time=START_TIME,



                              )

    print(start_station)
    print(stations_string)
    print(best_solution)
    print(best_cost)









