def ucs(graph, start, goal):

    open = [(0, start)]
    visited = []
    parent = {start: None}

    while open:

        open.sort()

        cost, best = open.pop(0)

        if best in visited:
            continue

        visited.append(best)

        if best == goal:

            path = []

            current = goal

            while current is not None:
                path.append(current)
                current = parent[current]

            path.reverse()

            return visited, path, cost

        for child in graph[best]:

            new_cost = cost + 1

            if child not in visited:

                open.append((new_cost, child))

                if child not in parent:
                    parent[child] = best

    return visited, [], -1