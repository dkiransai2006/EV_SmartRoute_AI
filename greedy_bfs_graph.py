def greedy_best_first(graph, h, start, goal):

    open = [start]
    visited = []
    parent = {start: None}

    while open:

        best = open[0]

        for node in open:

            if h[node] < h[best]:
                best = node

        open.remove(best)

        visited.append(best)

        if best == goal:

            path = []

            current = goal

            while current is not None:
                path.append(current)
                current = parent[current]

            path.reverse()

            return visited, path

        for child in graph[best]:

            if child not in visited and child not in open:

                open.append(child)

                if child not in parent:
                    parent[child] = best

    return visited, []