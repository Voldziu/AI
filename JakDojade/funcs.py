import csv
import heapq
import sys
import math
import random
from bisect import bisect_left
from collections import defaultdict


class Node:
    def __init__(self, station_name, g=float('inf'), total=0,h=0, parent=None, edge=None,arrival_time=None,current_line=None):
        self.station_name = station_name  # name of the station
        self.g = g  # edge cost
        self.total = total # cost so far (adding f's)
        self.h = h  # heuristic: estimated remaining travel time
        self.f = total + h  # total estimated cost

        self.parent = parent  # pointer to predecessor Node
        self.parent_station_name =  self.parent.station_name if  self.parent else ""
        self.edge = edge  # the edge (trip) taken to reach this node; tuple: (line, dep_time, arr_time, from_station, to_station)
        self.arrival_time = arrival_time
        self.current_line = current_line

    def __lt__(self, other):
        # This is needed for the heapq to compare nodes.
        return self.g < other.g

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.parent_station_name == other.parent_station_name and self.arrival_time == other.arrival_time and self.current_line == other.current_line and self.station_name == other.station_name and self.total ==  other.total

    def __hash__(self):
        return hash((self.station_name, self.arrival_time, self.current_line, self.parent_station_name,self.total))
    def __repr__(self):
        return f"Node({self.station_name}, g={self.g}, total={self.total},arrival={self.arrival_time}, h={self.h}, f={self.f}, current_line= {self.current_line})"



def parse_time(tstr):
    hh, mm, ss = map(int, tstr.split(':'))
    # if(hh>=24):
    #     hh = hh-24
    return hh * 3600 + mm * 60 + ss

def format_time(seconds):
    """
    reverts parse_time
    """
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

def haversine(lat1, lon1, lat2, lon2):
    """
    Computes the great-circle distance (in km) between two points on Earth.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Maximum bus speed in km/h (for heuristic) converted to km/s.
V_AVG = 20 / 3600.0  # ~0.01389 km/s #Average bus/tram speed (ASSUMPTION) (in straight line)

def heuristic(start, station_coords, end):
    """
    Estimates the minimal remaining travel time (in seconds) from 'stop' to 'goal'
    using the straight-line distance and maximum speed.
    """
    if start not in station_coords or end not in station_coords:
        return 0
    lat1, lon1 = station_coords[start]
    lat2, lon2 = station_coords[end]
    distance = haversine(lat1, lon1, lat2, lon2)
    return 1* distance / V_AVG


def build_adjacency(df):
    """
    Returns adjacency2: dict of dict,
      adjacency2[start_stop][(line, end_stop)] = list of (dep_time, arr_time),
    plus stop_coords.
    """
    adjacency = {}
    stop_coords = {}

    for _, row in df.iterrows():
        line_name   = row['line']
        dep_time    = row['departure_time']
        arr_time    = row['arrival_time']
        start_stop  = row['start_stop']
        end_stop    = row['end_stop']

        # Store coords if not present
        if start_stop not in stop_coords:
            stop_coords[start_stop] = (float(row['start_stop_lat']), float(row['start_stop_lon']))
        if end_stop not in stop_coords:
            stop_coords[end_stop] = (float(row['end_stop_lat']), float(row['end_stop_lon']))

        # Ensure keys exist:
        if start_stop not in adjacency:
            adjacency[start_stop] = {}

        key = (line_name, end_stop)
        if key not in adjacency[start_stop]:
            adjacency[start_stop][key] = []

        adjacency[start_stop][key].append((dep_time, arr_time))

    # Now sort each sub-list by dep_time
    for st in adjacency:
        for (line_name, end_stop), times_list in adjacency[st].items():
            times_list.sort(key=lambda x: x[0])

    return adjacency, stop_coords



def get_neighbors(current, adjacency, transfer_penalty, min_wait=120):
    """
    current: your current A* node (with fields station_name, current_line, arrival_time, total, etc.).
    adjacency2: the nested adjacency dict described above.
    transfer_penalty: penalty time for transferring lines.
    min_wait: how many seconds of wait are required when transferring lines?

    Returns a list of neighbors:
      [(neighbor_station, edge_cost, new_total, new_arrival, edge_info), ...]
    """
    neighbors = []
    station = current.station_name

    if station not in adjacency:
        return neighbors

    # For each (candidate_line, candidate_next_station) group:
    for (candidate_line, candidate_next_station), departures_list in adjacency[station].items():

        # Decide if transferring lines
        if current.current_line is None or (current.current_line == candidate_line):
            # Same line -> no transfer
            earliest_catch_time = current.arrival_time
            penalty = 0
        else:
            # Different line -> transfer
            earliest_catch_time = current.arrival_time + min_wait
            penalty = transfer_penalty

        # departures_list is already sorted by dep_time
        chosen_departure = None
        for (dep_time, arr_time) in departures_list:
            if dep_time >= earliest_catch_time:
                # We can catch this departure. It's the first feasible one, so take it and break.
                chosen_departure = (dep_time, arr_time)
                break

        if chosen_departure is not None:
            dep_time, arr_time = chosen_departure

            edge_cost = (arr_time - current.arrival_time) + penalty
            new_total = current.total + edge_cost
            new_arrival = arr_time
            edge_info = (candidate_line, dep_time, arr_time, station, candidate_next_station)

            neighbors.append(
                (candidate_next_station, edge_cost, new_total, new_arrival, edge_info)
            )

    return neighbors

# def prepare_n_stations_for_search(adjacency,n):
#     station_names = list(adjacency.keys())
#     return_string =""
#     if(n<3):
#         return return_string
#     chosen_stations =  random.sample(station_names,n)
#
#     for name in chosen_stations[1:-1]:
#         return_string+=(name+";")
#     return_string+=chosen_stations[-1]
#
#     return chosen_stations[0],return_string







