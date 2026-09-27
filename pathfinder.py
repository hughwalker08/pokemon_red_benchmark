from collections import deque

MOVES = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def find_path(walkable, start, target, blocked=(), goals=None):
    """Shortest list of directions from start to the reachable square closest to target.

    walkable: grid of True/False, indexed [row][col]
    start, target: (row, col); target may be off the grid or on a blocked square
    blocked: extra squares to avoid, e.g. where people are standing
    goals: optional set of squares that all count as arriving (e.g. every square past a map edge);
           if any is reachable, the nearest one by walking distance wins
    """
    rows, cols = len(walkable), len(walkable[0])
    came_from = {start: None}
    queue = deque([start])

    while queue:
        square = queue.popleft()
        for direction, (row_change, col_change) in MOVES.items():
            row, col = square[0] + row_change, square[1] + col_change
            neighbour = (row, col)
            if not (0 <= row < rows and 0 <= col < cols):
                continue
            if not walkable[row][col] or neighbour in blocked or neighbour in came_from:
                continue
            came_from[neighbour] = (square, direction)
            queue.append(neighbour)

    def distance(square):
        return abs(square[0] - target[0]) + abs(square[1] - target[1])

    reached_goals = [square for square in came_from if goals and square in goals]
    if reached_goals:
        best = reached_goals[0]
    else:
        best = min(came_from, key=distance)

    path = []
    square = best
    while came_from[square] is not None:
        square, direction = came_from[square]
        path.append(direction)
    path.reverse()
    return path
