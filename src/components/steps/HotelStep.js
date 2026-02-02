import React, { useState, useEffect, useRef } from 'react';
import { GoogleMap, Marker, InfoWindow, useLoadScript } from '@react-google-maps/api';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import '../steps/steps.css';
import useGoogleMapsKey from '../useGoogleMapsKey';
import { API_BASE } from '../../config';

const HotelStep = ({
  location,
  locationCoords,
  radius,
  budget,
  selectedHotel,
  checkInDate,
  checkOutDate,
  rentCar,
  duration,
  onBudgetChange,
  onHotelSelect,
  onCheckInChange,
  onCheckOutChange,
  onRentCarChange,
  onDurationChange,
  onNext,
  onBack,
}) => {
  const { apiKey, loading: keyLoading, error: keyError } = useGoogleMapsKey();
  const { isLoaded, loadError } = useLoadScript({ googleMapsApiKey: apiKey });
  const [hotels, setHotels] = useState([]);
  const [loadingHotels, setLoadingHotels] = useState(false);
  const [error, setError] = useState(null);
  const [hotelName, setHotelName] = useState('');
  const [selectedMarker, setSelectedMarker] = useState(null);
  const mapRef = useRef();

  // Set default dates if not provided
  const defaultCheckIn = checkInDate || new Date();
  const defaultCheckOut = checkOutDate || new Date(Date.now() + 24 * 60 * 60 * 1000); // Tomorrow

  // Calculate duration when dates change
  useEffect(() => {
    if (checkInDate && checkOutDate) {
      const diffTime = Math.abs(checkOutDate - checkInDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays !== duration) {
        onDurationChange(diffDays);
      }
    }
  }, [checkInDate, checkOutDate, duration, onDurationChange]);

  // Fit map bounds to all hotels
  useEffect(() => {
    if (hotels.length > 0 && mapRef.current && window.google) {
      const bounds = new window.google.maps.LatLngBounds();
      hotels.forEach(hotel => {
        if (hotel.lat && hotel.lon) {
          bounds.extend({ lat: hotel.lat, lng: hotel.lon });
        }
      });
      mapRef.current.fitBounds(bounds);
    }
  }, [hotels]);

  const fetchHotels = async () => {
    setLoadingHotels(true);
    setError(null);
    try {
      // Format dates as YYYY-MM-DD for API
      const formatDate = (date) => {
        if (!date) return null;
        const d = new Date(date);
        return d.toISOString().split('T')[0];
      };

      const response = await fetch(`${API_BASE}/api/search-hotels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: location,
          location_coords: locationCoords,
          radius: radius,
          max_price: budget,
          hotel_name: hotelName,
          check_in_date: formatDate(checkInDate || defaultCheckIn),
          check_out_date: formatDate(checkOutDate || defaultCheckOut),
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

  if (keyLoading) return <div>Loading API key...</div>;
  if (keyError) return <div>Error loading API key</div>;

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading map...</div>;

  return (
    <div className="step-container">
      <h2>Step 3: Choose Your Hotel & Transportation</h2>
      <p className="step-description">
        Set your hotel preferences, transportation, and dates.
      </p>

      <div className="form-group">
        <label htmlFor="hotelName">Hotel Name (optional)</label>
        <input
          id="hotelName"
          type="text"
          value={hotelName}
          onChange={(e) => setHotelName(e.target.value)}
          placeholder="Enter hotel address or leave blank for budget search"
          className="form-input"
        />
      </div>

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

      <div className="form-group">
        <button
          type="button"
          onClick={fetchHotels}
          disabled={!location || !locationCoords || loadingHotels}
          className="btn btn-secondary"
        >
          {loadingHotels ? 'Searching...' : 'Search Hotels'}
        </button>
      </div>

      <div className="form-group">
        <label>Travel Dates</label>
        <div className="date-picker-container">
          <div className="date-picker-group">
            <label htmlFor="checkin" className="date-label">Check-in Date</label>
            <DatePicker
              id="checkin"
              selected={checkInDate || defaultCheckIn}
              onChange={(date) => onCheckInChange(date)}
              minDate={new Date()}
              maxDate={checkOutDate || null}
              selectsStart
              startDate={checkInDate || defaultCheckIn}
              endDate={checkOutDate || defaultCheckOut}
              className="date-picker-input"
              dateFormat="MM/dd/yyyy"
              placeholderText="Select check-in date"
            />
          </div>
          <div className="date-picker-group">
            <label htmlFor="checkout" className="date-label">Check-out Date</label>
            <DatePicker
              id="checkout"
              selected={checkOutDate || defaultCheckOut}
              onChange={(date) => onCheckOutChange(date)}
              minDate={checkInDate || defaultCheckIn}
              selectsEnd
              startDate={checkInDate || defaultCheckIn}
              endDate={checkOutDate || defaultCheckOut}
              className="date-picker-input"
              dateFormat="MM/dd/yyyy"
              placeholderText="Select check-out date"
            />
          </div>
        </div>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={rentCar}
            onChange={(e) => onRentCarChange(e.target.checked)}
            className="form-checkbox"
          />
          <span>Rent a Car</span>
        </label>
        <p className="help-text">
          {rentCar
            ? 'You\'ll be using a car for transportation. Routes will be optimized for driving.'
            : 'You\'ll be using public transit. Routes will be optimized for transit.'}
        </p>
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
              onMouseEnter={() => setSelectedMarker(idx)}
              onMouseLeave={() => setSelectedMarker(null)}
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
            onLoad={(map) => { mapRef.current = map; }}
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
                >
                  {selectedMarker === idx && (
                    <InfoWindow onCloseClick={() => setSelectedMarker(null)}>
                      <div>
                        <h3>{hotel.name}</h3>
                        <p>{hotel.address}</p>
                        {hotel.price && <p>${hotel.price}/night</p>}
                      </div>
                    </InfoWindow>
                  )}
                </Marker>
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
          Next: Preferences
        </button>
      </div>
    </div>
  );
};

export default HotelStep;

