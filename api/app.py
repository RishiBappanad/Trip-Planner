from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import os
import requests
import urllib.parse
from datetime import datetime
from itenerary import Itinerary
from place import Place
from place import PlaceType
import search
import random
import config

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [config.FRONTEND_URL], "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

@app.route('/api/search-hotels', methods=['POST', 'OPTIONS'])
def search_hotels():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.json
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

    try:
        location = data.get('location')
        location_coords = data.get('location_coords')
        radius = data.get('radius', 5)  # in miles
        budget_per_night = data.get('max_price', 200)  # This is actually budget per night
        check_in_date = data.get('check_in_date')
        check_out_date = data.get('check_out_date')

        # Calculate number of nights and total max price
        num_nights = 1  # Default to 1 night
        if check_in_date and check_out_date:
            try:
                check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
                check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
                num_nights = (check_out - check_in).days
                if num_nights < 1:
                    num_nights = 1  # Ensure at least 1 night
            except Exception as date_err:
                print(f"Error calculating nights: {date_err}")
                num_nights = 1

        # Max price is budget per night * number of nights
        max_price = budget_per_night
        print(f"Budget per night: ${budget_per_night}, Nights: {num_nights}, Max total price: ${max_price}")

        # Use Amadeus API if we have coordinates and dates
        if location_coords and check_in_date and check_out_date:
            try:
                lat = location_coords.get('lat')
                lng = location_coords.get('lng')

                # Step 1: Get hotels by geocode
                hotels = search.get_hotels(lat, lng, radius)

                # Step 2: Get priced hotels (batches of 5)
                priced_hotel_list = search.priced_hotels(
                    max_price=max_price * num_nights,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    hotels=hotels,
                    num_nights=num_nights
                )

                return jsonify({'hotels': priced_hotel_list})
            except Exception as amadeus_err:
                print(f"Amadeus API error: {amadeus_err}")
                # Fallback to Foursquare if Amadeus fails
                pass

        # Fallback to Foursquare search
        # Determine query based on hotel_name
        query = data.get('hotel') if data.get('hotel') else "hotel"

        hotels = search.search_places(
            location=location,
            query=query,
            max_price=max_price if not data.get('hotel_name') else None,  # Skip price filter for specific hotel
            radius=radius,
            location_coords=location_coords
        )

        # Format hotels for frontend
        hotel_list = []
        for hotel in hotels:
            hotel_list.append({
                'name': hotel.name,
                'address': hotel.address,
                'lat': hotel.lat,
                'lon': hotel.lon,
                'price': max_price  # Foursquare doesn't always return price, use max_price as estimate
            })

        return jsonify({'hotels': hotel_list})
    except Exception as e:
        print(f"Error in search_hotels: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'hotels': []}), 500

@app.route('/api/submit', methods=['POST', 'OPTIONS'])
def submit():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.json
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400

    try:

        location = data.get('location')
        location_coords = data.get('location_coords')
        radius = data.get('radius', 5)
        hotel_data = data.get('hotel')
        rent_car = data.get('rent_car')
        budget = data.get('budget')
        duration = data.get('duration')
        selected_tours = data.get('selected_tours', [])
        food_percentages = data.get('food_percentages', [0, 0, 100])
        must_visit_locations = data.get('must_visit_locations', [])
        radius *= 1609.34

        # Parse selected hotel as a place
        hotel_place = None
        if hotel_data:
            hotel_place = parse_input_location({
                'name': hotel_data.get('name', 'Selected Hotel'),
                'type': 'Hotel',
                'address': hotel_data.get('address', '')
            })
            hotel_place.lat = hotel_data.get('lat')
            hotel_place.lon = hotel_data.get('lon')
            hotel_place.fill_location()
        print(f"Received submit request: location={location}, tours={selected_tours}, must_visit={must_visit_locations}, duration={duration}")
        
        search_center = location
        
        if not search_center:
            return jsonify({'error': 'No valid search location provided'}), 400
        
        # Map tour types to better search queries
        tour_query_map = {
            "City Tour": "landmark",
            "Museum Tour": "museum",
            "Nature Tour": "park",
            "Historical Tour": "historical monument",
            "Physical Activity": "sports center"
        }
        
        # Separate must-visit into food and tours
        must_visit_food = []
        must_visit_tours = []
        for must_visit in must_visit_locations:
            place = parse_input_location(must_visit)
            place.fill_location()
            if place.type == PlaceType.FOOD:
                must_visit_food.append(place)
            else:
                must_visit_tours.append(place)

        print(f"Added {len(must_visit_tours)} must-visit tour places")
        print(f"Added {len(must_visit_food)} must-visit food places")

        # Get tour places
        tour_places = get_tours(selected_tours, tour_query_map, search_center, radius, location_coords, must_visit_tours)

        # Search for food with better, more specific queries (within radius)
        fast_food_spots = search.search_places(location=search_center, query="fast food restaurant", radius=radius, location_coords=location_coords)
        local_food_spots = search.search_places(location=search_center, query="local restaurant", radius=radius, location_coords=location_coords)
        fancy_food_spots = search.search_places(location=search_center, query="fine dining restaurant", radius=radius, location_coords=location_coords)

        print(f"Found {len(fast_food_spots)} fast food spots")
        print(f"Found {len(local_food_spots)} local food spots")
        print(f"Found {len(fancy_food_spots)} fancy food spots")

        # Get food places
        all_food = get_food(food_percentages, fast_food_spots, local_food_spots, fancy_food_spots, duration, must_visit_food)

        daily_itineraries, tour_count, food_count = build_daily_itineraries(hotel_place, tour_places, all_food, duration, location_coords, radius, rent_car)

        # Build response
        response_data = {
            'success': True,
            'location': location,
            'duration': duration,
            'rent_car': rent_car,
            'budget': budget,
            'food_percentages': food_percentages,
            'daily_itineraries': daily_itineraries,
            'total_tours': tour_count,
            'total_food': food_count,
            'message': 'Daily itineraries created and optimized successfully'
        }
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in submit: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def parse_input_location(location):
    name = location['name']
    type = location['type']
    address = location['address']
    if type == 'Food':
        type = PlaceType.FOOD
    elif type == 'Tour':
        type = PlaceType.TOUR
    elif type == 'Hotel':
        type = PlaceType.HOTEL
    else:
        type = PlaceType.OTHER
    place = Place(name, address, type=type, address=address, lat=None, lon=None)
    return place


def split_food_by_percentage(food_percentages, fast_food_spots, local_food_spots, fancy_food_spots, duration):
    """Split food options by user-specified percentages, returning allocated food spots."""
    remaining_food_spots = 3 * duration
    all_food = []
    if remaining_food_spots > 0:
        fast_percent, local_percent, fancy_percent = [p / 100.0 for p in food_percentages]
        fast_amount = int(fast_percent * remaining_food_spots)
        local_amount = int(local_percent * remaining_food_spots)
        fancy_amount = int(fancy_percent * remaining_food_spots)
        # Adjust for rounding errors by adding remainder to fancy
        total_allocated = fast_amount + local_amount + fancy_amount
        if total_allocated < remaining_food_spots:
            fancy_amount += remaining_food_spots - total_allocated
        # Take what's necessary (min with available)
        fast_amount = min(fast_amount, len(fast_food_spots))
        local_amount = min(local_amount, len(local_food_spots))
        fancy_amount = min(fancy_amount, len(fancy_food_spots))
        # Add the spots
        all_food = fast_food_spots[:fast_amount] + local_food_spots[:local_amount] + fancy_food_spots[:fancy_amount]

    print(f"Food allocation: {len(all_food)} food places allocated for {duration} days")

    random.shuffle(all_food)
    return all_food


def get_tours(selected_tours, tour_query_map, search_center, radius, location_coords, must_visit_tours):
    """Get tour places from selected tours and must-visit tours, with deduplication."""
    existing_places = set((p.name.lower(), p.address.lower()) for p in must_visit_tours)
    additional_tours = []

    for tour in selected_tours:
        query = tour_query_map.get(tour, tour)
        places = search.search_places(location=search_center, query=query, radius=radius, location_coords=location_coords)
        added_count = 0
        for place in places:
            key = (place.name.lower(), place.address.lower())
            if key not in existing_places:
                additional_tours.append(place)
                existing_places.add(key)
                added_count += 1
        print(f"Found {added_count} additional places for '{tour}' (query: '{query}')")

    random.shuffle(additional_tours)
    tour_places = must_visit_tours + additional_tours
    return tour_places


def get_food(food_percentages, fast_food_spots, local_food_spots, fancy_food_spots, duration, must_visit_food):
    """Get food places from categories and must-visit food, with deduplication."""
    # Categorize places
    all_candidates = []
    for p in fast_food_spots:
        p.temp_type = 'fast'
        all_candidates.append(p)
    for p in local_food_spots:
        p.temp_type = 'local'
        all_candidates.append(p)
    for p in fancy_food_spots:
        p.temp_type = 'fancy'
        all_candidates.append(p)

    # Deduplicate all candidates
    seen = set()
    unique_candidates = []
    for p in all_candidates:
        key = (p.name.lower(), p.address.lower())
        if key not in seen:
            seen.add(key)
            unique_candidates.append(p)

    # Group by temp_type
    fast_unique = [p for p in unique_candidates if getattr(p, 'temp_type', None) == 'fast']
    local_unique = [p for p in unique_candidates if getattr(p, 'temp_type', None) == 'local']
    fancy_unique = [p for p in unique_candidates if getattr(p, 'temp_type', None) == 'fancy']

    split_result = split_food_by_percentage(food_percentages, fast_unique, local_unique, fancy_unique, duration)
    all_food = must_visit_food + split_result
    return all_food


def build_daily_itineraries(hotel_place, tour_places, all_food, duration, location_coords, radius, rent_car):
    """Build and optimize daily itineraries."""
    daily_itineraries = []
    tour_count = 0
    food_count = 0

    for day in range(duration):
        day_itinerary = Itinerary()
        day_itinerary.mode = "driving" if rent_car else "transit"

        # Add selected hotel as the first place in the itinerary
        if hotel_place:
            day_itinerary.add_place(hotel_place)

        # Add 2-3 tours per day (handle cases with fewer available tour places)
        tours_per_day = min(len(tour_places), random.randint(2, min(3, len(tour_places))) if len(tour_places) >= 2 else len(tour_places))
        for _ in range(tours_per_day):
            if tour_places:
                tour_count += 1
                place = tour_places.pop(0)
                day_itinerary.add_place(place)

        # Add 3 food spots per day
        food_per_day = 3
        added_food = 0
        for _ in range(food_per_day):
            if all_food:
                food_count += 1
                place = all_food.pop(0)
                day_itinerary.add_place(place)
                added_food += 1
        print(f"Day {day + 1}: Added {added_food} food spots, remaining food: {len(all_food)}")

        # Optimize this day's itinerary
        if len(day_itinerary.places) > 0:
            try:
                day_itinerary.create_distance_matrix()
                print(f"Day {day + 1}: Created distance matrix for {len(day_itinerary.places)} places")
                # Run hill-climbing optimization
                max_iterations = 50
                for iteration in range(max_iterations):
                    done = day_itinerary.execute_step()
                    if done:
                        print(f"Day {day + 1}: Optimization converged at iteration {iteration}")
                        print(day_itinerary.places)
                        break
            except Exception as opt_err:
                print(f"Day {day + 1}: Error during optimization: {opt_err}")
                # Use unoptimized schedule if optimization fails

        day_itinerary.final = list(day_itinerary.places)

        # Ensure the itinerary starts at the hotel
        if hotel_place:
            try:
                hotel_index = day_itinerary.final.index(hotel_place)
                # Rotate the list so hotel is first
                day_itinerary.final = day_itinerary.final[hotel_index:] + day_itinerary.final[:hotel_index]
            except ValueError:
                pass  # Hotel not found in the list

        daily_itineraries.append({
            'day': day + 1,
            'places': [
                {
                    'name': place.name,
                    'type': place.type.value,
                    'address': getattr(place, 'address', None),
                    'lat': getattr(place, 'lat', None),
                    'lon': getattr(place, 'lon', None),
                    'location': getattr(place, 'location', None)
                }
                for place in day_itinerary.final
            ]
        })

    return daily_itineraries, tour_count, food_count

@app.route('/api/config/google-maps-key', methods=['GET'])
def get_google_maps_key():
    return jsonify({'key': config.GOOGLE_MAPS_API_KEY})

if __name__ == '__main__':
    app.run(debug=True)
