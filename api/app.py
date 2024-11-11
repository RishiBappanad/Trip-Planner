
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import requests
from itenerary import Itinerary  
from place import Place 
import random

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

FOURSQUARE_API_KEY = 
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json  # Expecting JSON data

    location = data.get('location')
    rent_car = data.get('rent_car')
    budget = data.get('budget')
    duration = data.get('duration')
    selected_tours = data.get('selected_tours')
    food_percentages = data.get('food_percentages')
    fast_food = food_percentages[0]
    local_food = food_percentages[1]
    high_dining = food_percentages[2]

    

    # Your existing logic here
    itinerary = Itinerary()
    itinerary.mode = "driving" if rent_car else "transit"
    
    # Add logic to search for places, create distance matrix, etc.
    # Make sure to adjust any print statements to return jsonify results instead
    
    response_data = {
        'optimized_path': [place.name for place in itinerary.final],
        # Include other relevant response data as needed
    }
    tours = []
    for tour in selected_tours:
        tours.append(search_places(location=location, query=tour))
    fast_food_spots = search_places(location=location, query= "fast food")
    local_food_spots = search_places(location=location, query= "local food")
    fancy_food_spots = search_places(location=location, query= "high dining")
    num_food_locations = duration * 3
    fast_food *= num_food_locations
    fast_food = round(fast_food)
    local_food = round(local_food *num_food_locations)
    high_dining = round(high_dining * num_food_locations)


    food = []
    for i in range(fast_food):
        food.append(fast_food_spots[i])
    for i in range(fancy_food_spots):
        food.append(fancy_food_spots[i])
    for i in range(local_food):
        food.append(local_food_spots[i])
    random.shuffle(food)

    itineraries = []
    for i in range(duration):
        curr = Itinerary
        curr.add_place(tours.pop)
        curr.add_place(tours.pop)
        curr.add_place(food.pop)
        curr.add_place(food.pop)
        curr.add_place(food.pop)

        curr.create_distance_matrix()
        done = False
        while not done:
            done = curr.execute_step()

    return jsonify(response_data)

def search_places(self, location, query):
    location = urllib.parse.quote(location)
    url = f"https://api.foursquare.com/v3/places/search?query={query}&near={location}"
    headers = {
        "accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        responses = response.json().get('results', [])
        places = []
        for place in responses:
            place = Place(place['name'], place['location']['address'], type=query)
            places.append(place)

    else:
        print(f"Error fetching places: {response.status_code}")
        return []


if __name__ == '__main__':
    app.run(debug=True)
