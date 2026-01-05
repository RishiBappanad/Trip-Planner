import React, { useState, useEffect } from 'react';
import { GoogleMap, Marker, useLoadScript } from '@react-google-maps/api';
import '../steps/steps.css';

const GOOGLE_MAPS_API_KEY = 'AIzaSyCaNKux4_R3TSDEUcF3KKd7UzE1WbiqnpY';

const HotelStep = ({ location, locationCoords, radius, budget, selectedHotel, onBudgetChange, onHotelSelect, onNext, onBack }) => {
  const { isLoaded, loadError } = useLoadScript({ googleMapsApiKey: GOOGLE_MAPS_API_KEY });
  const [hotels, setHotels] = useState([]);
  const [loadingHotels, setLoadingHotels] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (location && locationCoords && budget) {
      fetchHotels();
    }
  }, [location, locationCoords, radius, budget]);

  const fetchHotels = async () => {
    setLoadingHotels(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/search-hotels', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: location,
          location_coords: locationCoords,
          radius: radius,
          max_price: budget,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setHotels(data.hotels || []);
    } catch (err) {
      console.error('Error fetching hotels:', err);
      setError(err.message);
      setHotels([]);
    } finally {
      setLoadingHotels(false);
    }
  };

  const mapContainerStyle = {
    width: '100%',
    height: '400px',
    borderRadius: '8px',
  };

  const mapOptions = {
    zoom: 12,
    center: locationCoords || { lat: 40.7128, lng: -74.0060 },
    mapTypeId: 'roadmap'
  };

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading map...</div>;

  return (
    <div className="step-container">
      <h2>Step 3: Choose Your Hotel</h2>
      <p className="step-description">
        Set your hotel budget per night and select a hotel from the available options.
      </p>
      
      <div className="form-group">
        <label htmlFor="budget">
          Hotel Budget per Night: ${budget}
        </label>
        <input
          id="budget"
          type="range"
          min="50"
          max="1000"
          step="10"
          value={budget}
          onChange={(e) => onBudgetChange(Number(e.target.value))}
          className="form-slider"
        />
        <div className="slider-labels">
          <span>$50</span>
          <span>$500</span>
          <span>$1000</span>
        </div>
      </div>

      {loadingHotels && (
        <div className="loading-message">Loading hotels...</div>
      )}

      {error && (
        <div className="error-message">Error: {error}</div>
      )}

      <div className="hotels-container">
        <div className="hotels-list">
          <h3>Available Hotels</h3>
          {hotels.length === 0 && !loadingHotels && (
            <p>No hotels found. Try adjusting your budget or radius.</p>
          )}
          {hotels.map((hotel, idx) => (
            <div
              key={idx}
              className={`hotel-card ${selectedHotel?.name === hotel.name ? 'selected' : ''}`}
              onClick={() => onHotelSelect(hotel)}
            >
              <h4>{hotel.name}</h4>
              <p className="hotel-address">{hotel.address}</p>
              {hotel.price && (
                <p className="hotel-price">${hotel.price}/night</p>
              )}
            </div>
          ))}
        </div>

        <div className="map-wrapper">
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={locationCoords}
            zoom={mapOptions.zoom}
            options={mapOptions}
          >
            {hotels.map((hotel, idx) => (
              hotel.lat && hotel.lon && (
                <Marker
                  key={idx}
                  position={{ lat: hotel.lat, lng: hotel.lon }}
                  title={hotel.name}
                  icon={{
                    path: 'M0-48c-26.4 0-48 21.6-48 48s21.6 48 48 48 48-21.6 48-48-21.6-48-48-48z',
                    fillColor: selectedHotel?.name === hotel.name ? '#e74c3c' : '#3498db',
                    fillOpacity: 1,
                    scale: 0.4,
                    strokeColor: '#fff',
                    strokeWeight: 1
                  }}
                />
              )
            ))}
          </GoogleMap>
        </div>
      </div>

      {selectedHotel && (
        <div className="selected-hotel">
          ✓ Selected: {selectedHotel.name}
        </div>
      )}

      <div className="step-actions">
        <button type="button" onClick={onBack} className="btn btn-secondary">
          Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!selectedHotel}
          className="btn btn-primary"
        >
          Next: Transportation
        </button>
      </div>
    </div>
  );
};

export default HotelStep;

