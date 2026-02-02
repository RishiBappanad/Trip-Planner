from enum import Enum
import googlemaps
from config import ROUTES_API_KEY


class PlaceType(Enum):
    FOOD = 'FOOD'
    HOTEL = 'HOTEL'
    TOUR = 'TOUR'
    OTHER = 'OTHER'

    def __str__(self):
        return self.value

class Place:
    def __init__(self, name, location, type=0, address=None, lat=None, lon=None):
        # location: string used for routing (address or "lat,lon")
        # address: human-readable address to display in UI
        self.location = location
        self.address = address if address is not None else location
        self.type = PlaceType(type)
        self.name = name
        # optional coordinates
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return "{}, {}".format(self.name, self.address)

    def fill_location(self):
        if self.lat is not None and self.lon is not None and self.address is not None:
            return

        gmaps = googlemaps.Client(key=ROUTES_API_KEY)

        if self.address and (self.lat is None or self.lon is None):
            # Forward geocoding
            geocode_result = gmaps.geocode(self.address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                self.lat = location['lat']
                self.lon = location['lng']
                if not self.address:
                    self.address = geocode_result[0]['formatted_address']
        elif self.lat is not None and self.lon is not None and not self.address:
            # Reverse geocoding
            reverse_result = gmaps.reverse_geocode((self.lat, self.lon))
            if reverse_result:
                self.address = reverse_result[0]['formatted_address']

        # Update location string
        if self.lat is not None and self.lon is not None:
            self.location = f"{self.lat},{self.lon}"
        elif self.address:
            self.location = self.address
        

    
