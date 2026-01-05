class Place:
    def __init__(self, name, location, type=0, address=None, lat=None, lon=None):
        # location: string used for routing (address or "lat,lon")
        # address: human-readable address to display in UI
        self.location = location
        self.address = address if address is not None else location
        self.type = type
        self.name = name
        self.time = 0  # log this in minutes
        # optional coordinates
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return "{}, {}".format(self.name, self.address)

    
