def a_star(graph, h, start, goal):

    open = [start]
    visited = []
    parent = {start: None}

    g = {
        start: 0
    }

    while open:

        best = open[0]

        for node in open:

            if g[node] + h[node] < g[best] + h[best]:
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

            return visited, path, g[best]

        for child in graph[best]:

            new_g = g[best] + 1

            if child not in visited and child not in open:

                g[child] = new_g

                parent[child] = best

                open.append(child)

    return visited, [], -1