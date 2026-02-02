import math
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import os
import requests
import urllib.parse
from datetime import datetime
from place import Place
from place import PlaceType
from config import FOURSQUARE_API_KEY
import concurrent.futures

# Amadeus configuration
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET
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
        list[tuple]: each tuple is (hotel_dict, location_tuple) where hotel_dict has {hotelId, name},
                     and location_tuple is (lat, lon, address)
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
            print(geo['latitude'])
            address_obj = item.get("address", {})
            print(address_obj['lines'][0] if 'lines' in address_obj and address_obj['lines'] else None)
            address = ", ".join(
                filter(
                    None,
                    [
                        address_obj['lines'][0] if 'lines' in address_obj and address_obj['lines'] else None,
                        address_obj['cityName'] if 'cityName' in address_obj else None,
                        address_obj['postalCode'] if 'postalCode' in address_obj else None,
                        address_obj['countryCode'] if 'countryCode' in address_obj else None,
                    ],
                )
            )

            hotel_dict = {
                "hotelId": hotel_id,
                "name": name or "Unknown",
            }
            location_tuple = (geo['latitude'], geo['longitude'], address or "Unknown")
            hotels.append((hotel_dict, location_tuple))
        except Exception as e:
            print(f"Error parsing Amadeus hotel item: {e}")
    return hotels


def _chunk_hotels(hotels, batch_size=5):
    """
    Helper to split a list of hotels into batches of valid size for the offers API.
    """
    for i in range(0, len(hotels), batch_size):
        yield hotels[i : i + batch_size]


def _process_batch(access_token, batch, base_params, headers, hotels_dict, max_price):
    """
    Process a batch of hotels to get priced offers.
    """
    url = f"{AMADEUS_BASE_URL}/v3/shopping/hotel-offers"
    hotel_ids = [h[0].get("hotelId") for h in batch if h[0].get("hotelId")]
    if not hotel_ids:
        return []

    params = base_params.copy()
    params["hotelIds"] = ",".join(hotel_ids)

    resp = requests.get(url, headers=headers, params=params)
    print(f"Amadeus priced_hotels batch request: {resp.url}")
    if resp.status_code != 200:
        print(f"Amadeus priced_hotels batch error: {resp.status_code} - {resp.text}")
        return []

    data = resp.json().get("data", [])
    batch_result = []
    for item in data:
        try:
            hotel_info = item.get("hotel", {})
            hotel_id = hotel_info.get("hotelId")
            offers = item.get("offers", [])
            if not hotel_id or not offers:
                continue

            # Find the location_tuple from input hotels
            location_tuple = hotels_dict.get(hotel_id)
            if not location_tuple:
                continue

            lat, lon, addr = location_tuple
            hotel_name = hotels_dict.get(hotel_id + "_name", "Unknown")

            # Find any offer for hotel within the price range
            qualifying_price = None
            for offer in offers:
                price_info = offer.get("price", {})
                total_str = price_info.get("total")
                try:
                    total_val = float(total_str)
                except (TypeError, ValueError):
                    continue
                if total_val <= max_price: 
                    qualifying_price = total_val
                    break
            if qualifying_price is None:
                continue

            hotel_entry = {
                "hotelId": hotel_id,
                "name": hotel_info.get("name") or hotel_name,
                "lat": lat,
                "lon": lon,
                "address": addr,
                "price": qualifying_price / (base_params.get("num_nights", 1)),
            }

            batch_result.append(hotel_entry)
            print(f"Added hotel: {hotel_entry}")
        except Exception as e:
            print(f"Error parsing Amadeus offer item: {e}")
    return batch_result


def priced_hotels(max_price, check_in_date, check_out_date, hotels, num_nights, adults=1, currency="USD"):
    """
    Step 2: Given a price ceiling, dates, and a hotel list from get_hotels,
    return a list of hotels that have at least one offer within the price range.

    Args:
        max_price (float): maximum total price (per stay) to include
        check_in_date (str): YYYY-MM-DD
        check_out_date (str): YYYY-MM-DD
        hotels (list[tuple]): list from get_hotels(), each (hotel_dict, location_tuple)
        adults (int): number of adults
        currency (str): currency code, e.g. 'USD'

    Returns:
        list[dict]: one entry per hotel that has any matching offer,
                    each dict includes location info from get_hotels and 'price' field.
    """
    if not hotels:
        return []

    access_token = get_amadeus_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    # Create a dict for quick lookup of location and name
    hotels_dict = {}
    for h in hotels:
        h_dict, loc = h
        hotel_id = h_dict.get("hotelId")
        if hotel_id:
            hotels_dict[hotel_id] = loc
            hotels_dict[hotel_id + "_name"] = h_dict.get("name", "Unknown")

    base_params = {
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
        "adults": adults,
        "currency": currency,
        "priceRange": f"0-{max_price}",
        "num_nights": num_nights,
    }

    result = []
    seen_ids = set()

    # Process hotels in parallel batches
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for batch in _chunk_hotels(hotels, batch_size=5):
            futures.append(executor.submit(_process_batch, access_token, batch, base_params, headers, hotels_dict, max_price))

        for future in concurrent.futures.as_completed(futures):
            batch_result = future.result()
            for hotel_entry in batch_result:
                hotel_id = hotel_entry["hotelId"]
                if hotel_id not in seen_ids:
                    result.append(hotel_entry)
                    seen_ids.add(hotel_id)
                    if len(result) >= 20:
                        return result[:20]

    print(f"Total priced hotels: {len(result)}")
    return result



def search_places(location, query, max_price=None, radius=None, location_coords=None):
    """Search places using Foursquare Places API and return list of Place objects with address and coords."""
    if location is None:
        return []
    location_str = str(location_coords['lat']) + "," + str(location_coords['lng']) if location_coords else location
    
    # Build URL with parameters
    if location_coords and radius:
        url = f"https://places-api.foursquare.com/places/search?query={urllib.parse.quote(query)}&ll={urllib.parse.quote(location_str)}&radius={urllib.parse.quote(str(int(radius)))}&sort=POPULARITY&limit=20"
    else:
        url = f"https://places-api.foursquare.com/places/search?query={urllib.parse.quote(query)}&near={urllib.parse.quote(location_str)}&sort=POPULARITY&limit=20"
    
    # Add max_price if provided (for hotels)
    if max_price is not None:
        if max_price < 150:
            url += f"&max_price={0}"
        elif max_price < 300:
            url += f"&max_price={1}"
        elif max_price < 450:
            url += f"&max_price={2}"
        else:
            url += f"&max_price={3}"
               
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

                    if location_coords and radius and lat and lon:
                        # Calculate distance in miles using Haversine formula
                        from math import radians, cos, sin, asin, sqrt
                        lat1, lon1 = radians(location_coords['lat']), radians(location_coords['lng'])
                        lat2, lon2 = radians(lat), radians(lon)
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        distance_miles = 3959 * c  
                        
                        if distance_miles > radius:
                            continue  # Skip places outside radius

                    location_str = f"{lat},{lon}" if lat and lon else place_addr

                    # Use vague category type instead of specific query
                    category_type = get_category_type(query)
                    print(place_name, category_type)
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
        return PlaceType.FOOD
    
    # Tour/attraction categories
    if any(tour_term in query_lower for tour_term in ['landmark', 'museum', 'park', 'monument', 'sports', 'tour', 'attraction', 'activity']):
        return PlaceType.TOUR
    
    # Default fallback
    return PlaceType.OTHER
