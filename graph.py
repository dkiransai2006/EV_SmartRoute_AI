def build_ev_graph(stations):

    graph = {
        "START": [],
        "DESTINATION": []
    }

    h = {
        "START": 0,
        "DESTINATION": 0
    }

    for i, station in enumerate(stations):

        node = "STATION_" + str(i + 1)

        graph["START"].append(node)

        graph[node] = ["DESTINATION"]

        h[node] = station["distance_to_destination"]

    return graph, h