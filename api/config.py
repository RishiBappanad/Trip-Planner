import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')
HOTELBEDS_API_KEY = os.getenv('HOTELBEDS_API_KEY')
HOTELBEDS_API_SECRET = os.getenv('HOTELBEDS_API_SECRET')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# For backward compatibility
ROUTES_API_KEY = GOOGLE_MAPS_API_KEY