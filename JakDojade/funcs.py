import csv
import heapq
import sys
import math
from bisect import bisect_left
from collections import defaultdict


class Node:
    def __init__(self, station_name, g=float('inf'), h=0, parent=None, edge=None,arrival_time=None):
        self.station_name = station_name  # name of the station
        self.g = g  # cost so far. Travels or time respectively. In time mode, it's the arrival time. In travels mode it's end cost.
        self.h = h  # heuristic: estimated remaining travel time
        self.f = g + h  # total estimated cost
        self.parent = parent  # pointer to predecessor Node
        self.edge = edge  # the edge (trip) taken to reach this node; tuple: (line, dep_time, arr_time, from_station, to_station)
        self.arrival_time = arrival_time if arrival_time is not None else g
        self.current_line = None

    def __lt__(self, other):
        # This is needed for the heapq to compare nodes.
        return self.g < other.g
    def __repr__(self):
        return f"Node({self.station_name}, g={self.g}, h={self.h}, f={self.f})"



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
V_AVG = 40 / 3600.0  # ~0.01389 km/s #Average bus/tram speed (ASSUMPTION)

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
    return distance / V_AVG


def build_adjacency(df):
    """
    Reads CSV data
    builds adjacency dict = adjacency[start_stop] = list (dep_time, arr_time, line, end_stop)
    Sorted by dep_time
    """
    adjacency = defaultdict(list)
    stop_coords = {}  # Mapping stop -> (latitude, longitude)


    for id,row in df.iterrows():

        line_name   = row['line']
        dep_time    = row['departure_time']
        arr_time    = row['arrival_time']
        start_stop  = row['start_stop']
        end_stop    = row['end_stop']

        # Save coordinates if not already present
        if start_stop not in stop_coords:
            stop_coords[start_stop] = (float(row['start_stop_lat']), float(row['start_stop_lon']))
        if end_stop not in stop_coords:
            stop_coords[end_stop] = (float(row['end_stop_lat']), float(row['end_stop_lon']))

        adjacency[start_stop].append((dep_time, arr_time, line_name, end_stop))

    # Posortuj listy wg dep_time
    for st in adjacency:
        adjacency[st].sort(key=lambda x: x[0])

    return adjacency,stop_coords

def get_neighbors(current, adjacency, transfer_penalty,min_wait=120):
    """
    Returns neighbor information for the current node.
    For each trip (dep_time, arr_time, candidate_line, next_station) from current.station_name:
      - If current.current_line is None or equals candidate_line:
           Trip is catchable if dep_time >= current.arrival_time.
           new_cost = candidate arrival time; new_arrival = candidate arrival time.
      - Else (transferring):
           Trip is catchable only if dep_time >= current.arrival_time + 120 (2 minutes wait).
           new_cost = candidate arrival time + transfer_penalty;
           new_arrival = candidate arrival time + transfer_penalty.
    Returns a list of tuples:
       (neighbor_station, new_cost, new_arrival, edge_info)
    where edge_info = (candidate_line, dep_time, arr_time, current.station_name, next_station).
    """
    neighbors = []

    if current.station_name not in adjacency:
        return neighbors
    for (dep_time, arr_time, candidate_line, next_station) in adjacency[current.station_name]:
        if current.current_line is None or current.current_line == candidate_line:
            # Same line or first ride
            if dep_time >= current.arrival_time:
                new_cost = arr_time
                new_arrival = arr_time
                edge_info = (candidate_line, dep_time, arr_time, current.station_name, next_station)
                neighbors.append((next_station, new_cost, new_arrival, edge_info))
        else:
            # Transfer: require at least 2 minutes wait
            if dep_time >= current.arrival_time + min_wait:
                new_cost = current.g + transfer_penalty
                new_arrival = arr_time
                edge_info = (candidate_line, dep_time, arr_time, current.station_name, next_station)
                neighbors.append((next_station, new_cost, new_arrival, edge_info))
    return neighbors










def reconstruct_path(end_node):
    """
    Reconstructs the path from the start to the end Node.
    Returns a list of edges:
      Each edge is a tuple: (line, departure_time, from_stop, arrival_time, to_stop)
    If no path exists, returns an empty list.
    """
    path = []
    current = end_node
    while current.parent is not None:
        path.append(current.edge)
        current = current.parent
    path.reverse()
    return path


def group_segments(path):
    """
    Given the raw path (each segment is
       (line, dep_time, start_stop, arr_time, end_stop)),
    group consecutive segments by the same line.

    Returns a list of grouped segments:
       (line, group_dep_time, group_arr_time, group_start_station, group_end_station).
    """
    if not path:
        return []

    grouped = []
    # Start the first group from the first segment
    current_line = path[0][0]
    current_dep_time = path[0][1]
    current_arr_time = path[0][2]
    current_start_station = path[0][3]
    current_end_station = path[0][4]

    for i in range(1, len(path)):
        line, dep_t, arr_t,st_start,  st_end = path[i]
        if line == current_line:
            # Continue the same line
            current_arr_time = arr_t
            current_end_station = st_end
        else:
            # Line changed => close the previous group
            grouped.append((
                current_line,
                current_dep_time,
                current_arr_time,
                current_start_station,
                current_end_station
            ))
            # Start a new group
            current_line = line
            current_dep_time = dep_t
            current_start_station = st_start
            current_arr_time = arr_t
            current_end_station = st_end

    # Add the last group
    grouped.append((
        current_line,
        current_dep_time,
        current_arr_time,
        current_start_station,
        current_end_station
    ))

    return grouped



def print_grouped_schedule(groups):
    """
    Prints each grouped segment (same line), including:
      - total ride time for that line segment
      - transfer time before the next line
    """
    for i, group in enumerate(groups):
        line, dep_time,  arr_time,st_start, st_end = group
        group_ride_time = arr_time - dep_time
        print(
            f"Line {line}: from '{st_start}' at {format_time(dep_time)} "
            f"to '{st_end}' at {format_time(arr_time)}. "
            f"Ride time: {group_ride_time} s (~{group_ride_time/60:.1f} min)"
        )

        # If there's a next group => print transfer time
        if i < len(groups) - 1:
            next_line, next_dep_time, _, _, _ = groups[i+1]
            transfer_time = next_dep_time - arr_time
            print(
                f"  Transfer time before catching line {next_line}: "
                f"{transfer_time} s (~{transfer_time/60:.1f} min)"
            )


