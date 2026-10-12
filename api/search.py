import hashlib
import math
import time
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import os
import requests
import urllib.parse
from datetime import datetime
from place import Place
from place import PlaceType
from config import FOURSQUARE_API_KEY

# Hotelbeds configuration (APItude test/sandbox environment)
from config import HOTELBEDS_API_KEY, HOTELBEDS_API_SECRET
HOTELBEDS_BASE_URL = "https://api.test.hotelbeds.com"

MILES_TO_KM = 1.60934


def _hotelbeds_headers():
    """
    Build the Api-key/X-Signature headers Hotelbeds requires on every request.
    Signature = sha256(api_key + secret + current unix timestamp).
    """
    if not HOTELBEDS_API_KEY or not HOTELBEDS_API_SECRET:
        raise RuntimeError("Hotelbeds credentials not configured. Set HOTELBEDS_API_KEY and HOTELBEDS_API_SECRET.")

    timestamp = str(int(time.time()))
    signature = hashlib.sha256(f"{HOTELBEDS_API_KEY}{HOTELBEDS_API_SECRET}{timestamp}".encode("utf-8")).hexdigest()
    return {
        "Api-key": HOTELBEDS_API_KEY,
        "X-Signature": signature,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def search_hotels_by_geolocation(lat, lon, radius_miles, check_in_date, check_out_date, max_price, num_nights, adults=1, currency="EUR"):
    """
    Search bookable hotel availability around a point using Hotelbeds' Booking API
    geolocation filter. One call covers what Amadeus needed two calls for (hotel
    lookup + priced offers), since Hotelbeds returns coordinates and rates together.

    Args:
        lat, lon (float): center point
        radius_miles (float): search radius in miles (converted to km for Hotelbeds)
        check_in_date, check_out_date (str): YYYY-MM-DD
        max_price (float): maximum total stay price to include
        num_nights (int): used to convert the stay total into a per-night price
        adults (int): occupants per room
        currency (str): Hotelbeds sandbox data is typically EUR regardless of this hint

    Returns:
        list[dict]: {name, lat, lon, address, price} per hotel, cheapest-rate <= max_price
    """
    url = f"{HOTELBEDS_BASE_URL}/hotel-api/1.0/hotels"
    body = {
        "stay": {"checkIn": check_in_date, "checkOut": check_out_date},
        "occupancies": [{"rooms": 1, "adults": adults, "children": 0}],
        "geolocation": {
            "latitude": lat,
            "longitude": lon,
            "radius": round(radius_miles * MILES_TO_KM),
            "unit": "km",
        },
    }

    resp = requests.post(url, headers=_hotelbeds_headers(), json=body)
    print(f"Hotelbeds availability request: {resp.url} body={body}")
    if resp.status_code != 200:
        print(f"Hotelbeds availability error: {resp.status_code} - {resp.text}")
        return []

    hotels_data = resp.json().get("hotels", {}).get("hotels", [])
    result = []
    for item in hotels_data:
        try:
            min_rate = item.get("minRate")
            if min_rate is None:
                continue
            total_price = float(min_rate)
            if total_price > max_price:
                continue

            address = ", ".join(filter(None, [item.get("zoneName"), item.get("destinationName")])) or "Unknown"

            # Hotelbeds returns latitude/longitude as strings; the frontend
            # feeds these straight into Google Maps' LatLngBounds, which
            # requires actual numbers and throws otherwise.
            lat = item.get("latitude")
            lon = item.get("longitude")

            result.append({
                "hotelId": item.get("code"),
                "name": item.get("name") or "Unknown",
                "lat": float(lat) if lat is not None else None,
                "lon": float(lon) if lon is not None else None,
                "address": address,
                "price": total_price / max(num_nights, 1),
            })
            if len(result) >= 20:
                break
        except Exception as e:
            print(f"Error parsing Hotelbeds hotel item: {e}")

    print(f"Total priced hotels: {len(result)}")
    return result



FOURSQUARE_HOTEL_CATEGORY_ID = "4bf58dd8d48988d1fa931735"


def search_places(location, query, max_price=None, radius=None, location_coords=None, category_ids=None):
    """Search places using Foursquare Places API and return list of Place objects with address and coords."""
    if location is None:
        return []
    location_str = str(location_coords['lat']) + "," + str(location_coords['lng']) if location_coords else location

    # fsq_category_ids matches ANY of a place's categories, not just its
    # primary one, so a hotel's in-house cafe/restaurant/breakfast room also
    # matches (it's tagged with both its own category and "Hotel"). Those
    # outrank the actual hotels under sort=POPULARITY within a small result
    # window, so pull a larger page and filter to primary-category matches
    # below rather than trusting the top 20 as-is.
    limit = 50 if category_ids else 20

    # Build URL with parameters
    if location_coords and radius:
        url = f"https://places-api.foursquare.com/places/search?query={urllib.parse.quote(query)}&ll={urllib.parse.quote(location_str)}&radius={urllib.parse.quote(str(int(radius)))}&sort=POPULARITY&limit={limit}"
    else:
        url = f"https://places-api.foursquare.com/places/search?query={urllib.parse.quote(query)}&near={urllib.parse.quote(location_str)}&sort=POPULARITY&limit={limit}"

    if category_ids:
        url += f"&fsq_category_ids={urllib.parse.quote(category_ids)}"

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
            allowed_category_ids = set(category_ids.split(',')) if category_ids else None
            places = []
            for item in items:
                try:
                    if allowed_category_ids:
                        item_categories = item.get('categories', [])
                        primary_category_id = item_categories[0].get('fsq_category_id') if item_categories else None
                        if primary_category_id not in allowed_category_ids:
                            continue  # skip venues only tagged Hotel as a secondary category (e.g. a hotel's cafe)

                    place_name = item.get('name', 'Unknown')
                    loc = item.get('location', {})
                    # prefer formatted_address, fall back to components
                    place_addr = loc.get('formatted_address') or \
                        ", ".join(filter(None, [loc.get('address'), loc.get('locality'), loc.get('region'), loc.get('country')])) or 'Unknown'

                    # This API version (2025-06-17) returns coordinates as
                    # top-level latitude/longitude fields, not nested under
                    # geocodes.main like the older Foursquare API did.
                    lat = item.get('latitude')
                    lon = item.get('longitude')

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
