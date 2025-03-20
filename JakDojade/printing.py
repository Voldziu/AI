
from funcs import *



def reconstruct_path(end_node):
    """
    Reconstructs the path from the start to the end Node.
    Returns a list of edges:
      Each edge is a tuple: (line, departure_time, from_stop, arrival_time, to_stop)
    If no path exists, returns an empty list.
    """
    path = []
    current = end_node
    #print(current)
    while current.parent is not None:
        #print(current)
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
def print_grouped_schedule(start_time,groups):
    """
    Prints each grouped segment (same line), including:
      - total ride time for that line segment
      - transfer time before the next line
    """
    start_index = 0
    first_group = groups[start_index]
    line, dep_time, arr_time, st_start, st_end = first_group
    if(start_time<dep_time):
        waiting_time = dep_time-start_time
        print(
            f"  Waiting time to catch first line: "
            f"{waiting_time} s ({waiting_time / 60:.1f} min)"
        )
    for i, group in enumerate(groups[start_index:]):
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
                f"{transfer_time} s ({transfer_time/60:.1f} min)"
            )


def print_whole_stats(end_node,start_station,end_station,start_time):
    start_time_str = format_time(start_time)


    if end_node is None:
        print("There's no connection between those stations.")
        sys.exit(1)

    path = reconstruct_path(end_node)
    if not path:
        print("No connection (parent invalid)")
        sys.exit(1)

    # Group consecutive segments by line
    grouped_path = group_segments(path)

    print(f"\t\t=== Route from {start_station} to {end_station}  ===\n")
    print(f"Start time: {start_time_str}")
    print_grouped_schedule(start_time, grouped_path)

    # Print total travel time
    total_travel_time = end_node.arrival_time - start_time
    # print("\n=== Final cost ===", file=sys.stderr)
    # print(f"\n=== {end_node.total} ===", file=sys.stderr)
    # print(
    #     f"Final travel time: {total_travel_time} s "
    #     f"(~{total_travel_time / 60:.1f} min)",
    #     file=sys.stderr
    # )