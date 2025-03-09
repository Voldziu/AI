from funcs import *


def dijkstra(adjacency, start_station, end_station, start_time):
    """
    Dijkstra algorithm implementation
      - adjacency: dict with list of (dep_time, arr_time, line, next_stop)
      - start_station: starting station (A)
      - end_station: target station (B)
      - start_time: time (in seconds after midnight) at which we are at the start station

    Returns:
      The final (goal) Node that contains the final arrival time and parent pointer
      so that the path can be reconstructed. Returns None if no path is found.
    """
    # Create a dictionary to hold the best-known Node for each station.
    best_nodes = {}

    # Initialize the start node.
    start_node = Node(start_station, g=start_time, parent=None, edge=None)
    best_nodes[start_station] = start_node

    # Priority queue (min-heap) for Node objects.
    open_list = [start_node]

    while open_list:
        # Get the node with the smallest cost (arrival time).
        current = heapq.heappop(open_list)

        # If we already found a better way to this station, skip.
        if current.g > best_nodes[current.station_name].g:
            continue

        # If the current node is the goal, return it.
        if current.station_name== end_station:
            return current

        # Retrieve all trips (edges) from current.stop.
        edges = adjacency.get(current.station_name, [])
        if not edges:
            continue

        # Build a list of departure times to perform binary search.
        dep_times = [edge[0] for edge in edges]
        # Find the earliest trip we can catch (dep_time >= current.g).
        idx = bisect_left(dep_times, current.g)

        # Explore each valid trip from index idx onward.
        for i in range(idx, len(edges)):
            dep_time, arr_time, line_name, next_stop = edges[i]
            # We can catch the trip if dep_time >= current.g; arrival time is arr_time.
            arrival = arr_time

            # If this trip leads to an earlier arrival at next_stop, update.
            if arrival < best_nodes.get(next_stop, Node(next_stop)).g:
                new_node = Node(next_stop, g=arrival, parent=current,
                                edge=(line_name, dep_time, arr_time, current.station_name, next_stop))
                best_nodes[next_stop] = new_node
                heapq.heappush(open_list, new_node)

    return None