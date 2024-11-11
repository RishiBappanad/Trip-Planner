import math
import random
import googlemaps
from functools import  lru_cache

ROUTES_API_KEY = 


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
        self.gmaps = googlemaps.Client(key=ROUTES_API_KEY)
        self.mode = "transit"
        self.cache = {}
        self.distance_matrix = {}

    def add_place(self, place):
        """Add a place to the itinerary."""
        self.places.append(place)

    def distance_between(self, place1, place2):
        """Calculate the travel duration between two places using Google Maps API, with caching."""
        # Create a tuple key for the cache
        key = (place1.location, place2.location)
        # Check if the distance is already cached
        if key in self.cache:
            return self.cache[key]

        # Otherwise, calculate the distance


        # Call the Google Maps API
        return self.distance_matrix[place1.location][place2.location]


    def random_path(self, places):
        """Generate a random path (random TSP initialization)."""
        places = places[:]
        random.shuffle(places)
        return places

    def cost_of(self, places):
        """Calculate the total distance of a path."""
        total_distance = 0.0
        for i in range(len(places) - 1):
            total_distance += self.distance_between(places[i], places[i + 1])
        # Add the distance back to the starting point to complete the tour
        total_distance += self.distance_between(places[-1], places[0])
        return total_distance


    def create_distance_matrix(self):
        destinations = []
        for place in self.places:
            destinations.append(place.location)
        matrix = self.gmaps.distance_matrix(destinations, destinations, mode=self.mode)
        i = 0
        for row in matrix['rows']:
            j = 0
            distance_matrix = {}
            for element in row['elements']:
                if element['status'] == 'OK':
                    duration_value = element['duration']['value']
                else:
                    duration_value = math.inf
                distance_matrix[destinations[j]] = duration_value
                j += 1
            self.distance_matrix[destinations[i]] = distance_matrix
            i += 1

    def execute_step(self):
        """Perform a local search to improve the places."""
        if improve(self.places, self) > 0.1:
            return False
        if self.cost_of(self.places) < self.optimal:
            self.optimal = self.cost_of(self.places)
            self.final = self.places
        while self.restarts < 10:
            self.restarts += 1
            self.places = self.random_path(self.places)
            return False
        return True


def improve(places, solver):
    improvement = 0.0
    for i in range(len(places) - 1):
        for j in range(i + 1, len(places)):
            current_distance = (
                    solver.distance_between(places[i], places[i + 1]) +
                    solver.distance_between(places[j], places[(j + 1) % len(places)])
            )
            new_distance = (
                    solver.distance_between(places[i], places[j]) +
                    solver.distance_between(places[i + 1], places[(j + 1) % len(places)])
            )
            local_distance = current_distance - new_distance
            if local_distance > 0:
                places = swap(places, i, j)
                improvement += local_distance

    return improvement


def swap(places, i, j):
    if i > j:
        return places
    temp = list(places[i + 1:j + 1])
    temp.reverse()
    new_path = places[:i + 1] + temp + places[j + 1:]
    places[:] = new_path
    return places
