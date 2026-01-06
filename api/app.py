from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import os
import requests
import urllib.parse
from datetime import datetime
from itenerary import Itinerary
from place import Place
import random

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"], "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

FOURSQUARE_API_KEY = 'SM242XPEPY4214Z5FLIJI1IL2ZMG02PA22ZOQ1SRDMQ0RWBC'

# Amadeus configuration (use environment variables in a real deployment)
AMADEUS_CLIENT_ID = "G6323WYjtTGJZT5gJvd7RwDI3jNk2A87"
AMADEUS_CLIENT_SECRET = "Gfnk0HzXGikjTsLR"
AMADEUS_BASE_URL = "https://test.api.amadeus.com"


def get_amadeus_access_token():
    """
    Retrieve an OAuth2 access token from Amadeus.
    Expects AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET to be set in the environment.
    """
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        raise RuntimeError("Amadeus credentials not configured. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET.")

    token_url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET,
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to obtain Amadeus token: {resp.status_code} - {resp.text}")
    payload = resp.json()
    return payload.get("access_token")


def get_hotels(lat, lon, radius_miles):
    """
    Step 1: Given a center point and radius, return a list of hotels from Amadeus.

    Args:
        lat (float): latitude of center
        lon (float): longitude of center
        radius_miles (float): search radius in miles

    Returns:
        list[dict]: each dict contains at least {hotelId, name, lat, lon, address}
    """
    access_token = get_amadeus_access_token()

    url = f"{AMADEUS_BASE_URL}/v1/reference-data/locations/hotels/by-geocode"
    params = {
        "latitude": lat,
        "longitude": lon,
        "radius": radius_miles,
        "radiusUnit": "MILE",
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    resp = requests.get(url, headers=headers, params=params)
    print(f"Amadeus get_hotels request: {resp.url}")
    if resp.status_code != 200:
        print(f"Amadeus get_hotels error: {resp.status_code} - {resp.text}")
        return []

    data = resp.json().get("data", [])
    hotels = []
    for item in data:
        try:
            hotel_id = item.get("hotelId")
            name = item.get("name") or item.get("hotel", {}).get("name")
            geo = item.get("geoCode", {})
            address_obj = item.get("address", {})
            address = ", ".join(
                filter(
                    None,
                    [
                        address_obj.get("addressLine"),
                        address_obj.get("cityName"),
                        address_obj.get("postalCode"),
                        address_obj.get("countryCode"),
                    ],
                )
            )

            hotels.append(
                {
                    "hotelId": hotel_id,
                    "name": name or "Unknown",
                    "lat": geo.get("latitude"),
                    "lon": geo.get("longitude"),
                    "address": address or "Unknown",
                }
            )
        except Exception as e:
            print(f"Error parsing Amadeus hotel item: {e}")
    return hotels


def _chunk_hotels(hotels, batch_size=5):
    """
    Helper to split a list of hotels into batches of valid size for the offers API.
    """
    for i in range(0, len(hotels), batch_size):
        yield hotels[i : i + batch_size]


def priced_hotels(max_price, check_in_date, check_out_date, hotels, adults=1, currency="USD"):
    """
    Step 2: Given a price ceiling, dates, and a hotel list from get_hotels,
    return a list of hotels that have at least one offer within the price range.

    Args:
        max_price (float): maximum total price (per stay) to include
        check_in_date (str): YYYY-MM-DD
        check_out_date (str): YYYY-MM-DD
        hotels (list[dict]): list from get_hotels()
        adults (int): number of adults
        currency (str): currency code, e.g. 'USD'

    Returns:
        list[dict]: one entry per hotel that has any matching offer,
                    each dict includes a 'price' field from a qualifying offer.
    """
    if not hotels:
        return []

    access_token = get_amadeus_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    result = []
    seen_ids = set()

    # Process hotels in batches of 5
    for batch in _chunk_hotels(hotels, batch_size=5):
        hotel_ids = [h.get("hotelId") for h in batch if h.get("hotelId")]
        if not hotel_ids:
            continue

        url = f"{AMADEUS_BASE_URL}/v3/shopping/hotel-offers"
        params = {
            "hotelIds": ",".join(hotel_ids),
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "currency": currency,
            "priceRange": f"0-{max_price}",
        }

        resp = requests.get(url, headers=headers, params=params)
        print(f"Amadeus priced_hotels request: {resp.url}")
        if resp.status_code != 200:
            print(f"Amadeus priced_hotels error: {resp.status_code} - {resp.text}")
            continue

        data = resp.json().get("data", [])
        for item in data:
            try:
                hotel_info = item.get("hotel", {})
                hotel_id = hotel_info.get("hotelId")
                offers = item.get("offers", [])
                if not hotel_id or not offers or hotel_id in seen_ids:
                    continue

                # Find any offer within the price range (take the first that matches)
                qualifying_price = None
                for offer in offers:
                    price_info = offer.get("price", {})
                    total_str = price_info.get("total")
                    print(total_str)
                    try:
                        total_val = float(total_str)
                    except (TypeError, ValueError):
                        continue
                    if total_val <= max_price:
                        qualifying_price = total_val
                        break
                if qualifying_price is None:
                    continue

                geo = hotel_info.get("geoCode", {})
                address_obj = hotel_info.get("address", {})
                address = ", ".join(
                    filter(
                        None,
                        [
                            address_obj.get("addressLine"),
                            address_obj.get("cityName"),
                            address_obj.get("postalCode"),
                            address_obj.get("countryCode"),
                        ],
                    )
                )

                hotel_entry = {
                    "hotelId": hotel_id,
                    "name": hotel_info.get("name") or "Unknown",
                    "lat": geo.get("latitude"),
                    "lon": geo.get("longitude"),
                    "address": address or "Unknown",
                    "price": qualifying_price,
                }

                result.append(hotel_entry)
                print(f"Added hotel: {hotel_entry}")
                seen_ids.add(hotel_id)
            except Exception as e:
                print(f"Error parsing Amadeus offer item: {e}")
    print(result)
    return result



@app.route('/api/search-hotels', methods=['POST', 'OPTIONS'])
def search_hotels():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.json
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
        max_price = budget_per_night * num_nights
        print(f"Budget per night: ${budget_per_night}, Nights: {num_nights}, Max total price: ${max_price}")
        
        # Use Amadeus API if we have coordinates and dates
        if location_coords and check_in_date and check_out_date:
            try:
                lat = location_coords.get('lat')
                lng = location_coords.get('lng')
                
                # Step 1: Get hotels by geocode
                hotels = get_hotels(lat, lng, radius)
                
                # Step 2: Get priced hotels (batches of 5)
                priced_hotel_list = priced_hotels(
                    max_price=max_price,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    hotels=hotels
                )
                
                return jsonify({'hotels': priced_hotel_list})
            except Exception as amadeus_err:
                print(f"Amadeus API error: {amadeus_err}")
                # Fallback to Foursquare if Amadeus fails
                pass
        
        # Fallback to Foursquare search
        hotels = search_places(
            location=location,
            query="hotel",
            max_price=max_price,
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
        data = request.json  # Expecting JSON data

        location = data.get('location')
        location_coords = data.get('location_coords')
        radius = data.get('radius', 5)
        hotel = data.get('hotel')
        rent_car = data.get('rent_car')
        budget = data.get('budget')
        duration = data.get('duration')
        selected_tours = data.get('selected_tours', [])
        food_percentages = data.get('food_percentages', [0, 0, 100])
        
        print(f"Received submit request: location={location}, tours={selected_tours}, duration={duration}")
        
        # Use hotel location as center if provided, otherwise use location_coords or location
        if hotel and hotel.get('lat') and hotel.get('lon'):
            search_center = f"{hotel['lat']},{hotel['lon']}"
        elif location_coords and location_coords.get('lat') and location_coords.get('lng'):
            search_center = f"{location_coords['lat']},{location_coords['lng']}"
        else:
            search_center = location or ""
        
        if not search_center:
            return jsonify({'error': 'No valid search location provided'}), 400
        
        # Map tour types to better search queries for Nominatim
        tour_query_map = {
            "City Tour": "landmark",
            "Museum Tour": "museum",
            "Nature Tour": "park",
            "Historical Tour": "historical monument",
            "Physical Activity": "sports center"
        }
        
        # Get place recommendations for tours (within radius of hotel/location)
        tour_places = []
        for tour in selected_tours:
            query = tour_query_map.get(tour, tour)  # Use mapped query or fallback to tour name
            places = search_places(location=search_center, query=query, radius=radius, location_coords=location_coords)
            tour_places.extend(places)
            print(f"Found {len(places)} places for '{tour}' (query: '{query}')")
        
        # Search for food with better, more specific queries (within radius)
        fast_food_spots = search_places(location=search_center, query="fast food restaurant", radius=radius, location_coords=location_coords)
        local_food_spots = search_places(location=search_center, query="local restaurant", radius=radius, location_coords=location_coords)
        fancy_food_spots = search_places(location=search_center, query="fine dining restaurant", radius=radius, location_coords=location_coords)
        
        print(f"Found {len(fast_food_spots)} fast food spots")
        print(f"Found {len(local_food_spots)} local food spots")
        print(f"Found {len(fancy_food_spots)} fancy food spots")
        
        # Pool all food options
        all_food = fast_food_spots + local_food_spots + fancy_food_spots
        random.shuffle(all_food)
        
        # Build daily itineraries
        daily_itineraries = []
        tour_idx = 0
        food_idx = 0
        
        for day in range(duration):
            day_itinerary = Itinerary()
            day_itinerary.mode = "driving" if rent_car else "transit"
            
            # Add 2-3 tours per day (handle cases with fewer available tour places)
            available_tours = len(tour_places) - tour_idx
            if available_tours <= 0:
                tours_per_day = 0
            elif available_tours < 2:
                # If only 1 tour remains, take that one
                tours_per_day = available_tours
            else:
                # When 2 or more tours remain, choose between 2 and up to 3 (but no more than available)
                tours_per_day = random.randint(2, min(3, available_tours))

            for _ in range(tours_per_day):
                if tour_idx < len(tour_places):
                    day_itinerary.add_place(tour_places[tour_idx])
                    tour_idx += 1
            
            # Add 3 food spots per day
            food_per_day = 3
            for _ in range(food_per_day):
                if food_idx < len(all_food):
                    day_itinerary.add_place(all_food[food_idx])
                    food_idx += 1
            
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
                            break
                except Exception as opt_err:
                    print(f"Day {day + 1}: Error during optimization: {opt_err}")
                    # Use unoptimized schedule if optimization fails
                    day_itinerary.final = list(day_itinerary.places)
            
            daily_itineraries.append({
                'day': day + 1,
                'places': [
                    {
                        'name': place.name,
                        'type': place.type,
                        'address': getattr(place, 'address', None),
                        'lat': getattr(place, 'lat', None),
                        'lon': getattr(place, 'lon', None),
                        'location': getattr(place, 'location', None)
                    }
                    for place in day_itinerary.final
                ]
            })
        
        # Build response
        response_data = {
            'success': True,
            'location': location,
            'duration': duration,
            'rent_car': rent_car,
            'budget': budget,
            'food_percentages': food_percentages,
            'daily_itineraries': daily_itineraries,
            'total_tours': tour_idx,
            'total_food': food_idx,
            'message': 'Daily itineraries created and optimized successfully'
        }
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in submit: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def search_places(location, query, max_price=None, radius=None, location_coords=None):
    """Search places using Foursquare Places API and return list of Place objects with address and coords."""
    # Ensure location is a string
    if location is None:
        return []
    location_str = str(location)
    
    # Build URL with parameters (Foursquare API handles URL encoding, so we can use the string directly)
    url = f"https://places-api.foursquare.com/places/search?query={urllib.parse.quote(query)}&near={urllib.parse.quote(location_str)}&limit=10"
    
    # Add max_price if provided (for hotels)
    if max_price is not None:
        url += f"&max_price={max_price}"
    
    headers = {
        "accept": "application/json",
        "X-Places-Api-Version": "2025-06-17",
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
    }
    try:
        response = requests.get(url, headers=headers)
        print(f"Foursquare API request to: {url}")
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            items = response.json().get('results', [])
            places = []
            for item in items:
                try:
                    place_name = item.get('name', 'Unknown')
                    loc = item.get('location', {})
                    # prefer formatted_address, fall back to components
                    place_addr = loc.get('formatted_address') or \
                        ", ".join(filter(None, [loc.get('address'), loc.get('locality'), loc.get('region'), loc.get('country')])) or 'Unknown'

                    geocodes = item.get('geocodes', {})
                    main = geocodes.get('main', {})
                    lat = main.get('latitude') if main else None
                    lon = main.get('longitude') if main else None

                    # Filter by radius if location_coords and radius are provided
                    if location_coords and radius and lat and lon:
                        # Calculate distance in miles using Haversine formula
                        from math import radians, cos, sin, asin, sqrt
                        lat1, lon1 = radians(location_coords['lat']), radians(location_coords['lng'])
                        lat2, lon2 = radians(lat), radians(lon)
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        distance_miles = 3959 * c  # Earth radius in miles
                        
                        if distance_miles > radius:
                            continue  # Skip places outside radius

                    # location string for routing: use 'lat,lon' if available, otherwise address
                    location_str = f"{lat},{lon}" if lat and lon else place_addr

                    # Use vague category type instead of specific query
                    category_type = get_category_type(query)
                    place = Place(place_name, location_str, type=category_type, address=place_addr, lat=lat, lon=lon)
                    places.append(place)
                except Exception as item_err:
                    print(f"Error parsing place item: {item_err}")
            return places
        else:
            print(f"Error fetching places: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception in search_places: {e}")
        return []

def get_category_type(query):
    """Map specific query strings to vague category types."""
    query_lower = query.lower()
    
    # Food categories
    if any(food_term in query_lower for food_term in ['restaurant', 'food', 'dining', 'cafe', 'bistro']):
        return "Food"
    
    # Tour/attraction categories
    if any(tour_term in query_lower for tour_term in ['landmark', 'museum', 'park', 'monument', 'sports', 'tour', 'attraction', 'activity']):
        return "Tour"
    
    # Default fallback
    return "Tour"

if __name__ == '__main__':
    app.run(debug=True)
