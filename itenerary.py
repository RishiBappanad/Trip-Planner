import math
import random


class Itinerary:

    def __init__(self):
        self.schedule = []
        self.places = []
        self.visited = []
        self.heuristic = 0
        self.optimal = math.inf
        self.final = []
        self.restarts = 0
        self.path = []

    def add_place(self, place):
        """Add a place to the itinerary."""
        self.places.append(place)

    def distance_between(self, place1, place2):
        """Calculate the Euclidean distance between two places."""
        x1, y1 = place1.location
        x2, y2 = place2.location
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def random_path(self, places):
        """Generate a random path (random TSP initialization)."""
        path = places[:]
        random.shuffle(path)
        return path

    def cost_of(self, path):
        """Calculate the total distance of a path."""
        total_distance = 0.0
        for i in range(len(path) - 1):
            total_distance += self.distance_between(path[i], path[i + 1])
        # Add the distance back to the starting point to complete the tour
        total_distance += self.distance_between(path[-1], path[0])
        return total_distance

    def execute_step(self):
        """Perform a local search to improve the path."""
        if improve(self.path, self) > 0.1:
            return False
        if self.cost_of(self.path) < self.optimal:
            self.optimal = self.cost_of(self.path)
            self.final = self.path[:]
        while self.restarts < 10:
            self.restarts += 1
            self.path = self.random_path(self.places)
            return False
        return True

def improve(path, solver):
    improvement = 0.0
    for i in range(len(path) - 1):
        for j in range(i + 1, len(path)):
            current_distance = (
                solver.distance_between(path[i], path[i + 1]) +
                solver.distance_between(path[j], path[(j + 1) % len(path)])
            )
            new_distance = (
                solver.distance_between(path[i], path[j]) +
                solver.distance_between(path[i + 1], path[(j + 1) % len(path)])
            )
            local_distance = current_distance - new_distance
            if local_distance > 0:
                path = swap(path, i, j)
                improvement += local_distance

    return improvement

def swap(path, i, j):
    if i > j:
        return path
    temp = list(path[i + 1:j + 1])
    temp.reverse()
    new_path = path[:i + 1] + temp + path[j + 1:]
    path[:] = new_path
    return path
