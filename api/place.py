class Place:
    def __init__(self, name, location, type=0):
        self.location = location
        self.type = type
        self.name = name
        self.time = 0 #log this in minutes

    def __str__(self):
        return "{}, {}".format(self.name, self.location)

    
