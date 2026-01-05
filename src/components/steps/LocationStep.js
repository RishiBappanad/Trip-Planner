import React, { useState, useEffect, useRef } from 'react';
import '../steps/steps.css';

const LocationStep = ({ location, locationCoords, onLocationSelect, onNext }) => {
  const [locationInput, setLocationInput] = useState(location || '');
  const [locationSuggestions, setLocationSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const debounceTimer = useRef(null);

  useEffect(() => {
    if (location) {
      setLocationInput(location);
    }
  }, [location]);

  const fetchLocationSuggestions = async (query) => {
    if (!query || query.length < 2) {
      setLocationSuggestions([]);
      return;
    }

    setIsLoadingSuggestions(true);
    try {
      const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=8&addressdetails=1`;
      const res = await fetch(url, {
        headers: {
          'Accept-Language': 'en',
          'User-Agent': 'Trip-Planner-App'
        }
      });
      if (!res.ok) throw new Error(`Nominatim error: ${res.status}`);
      const data = await res.json();

      const suggestions = (data || [])
        .map(place => {
          const addr = place.address || {};
          const type = (place.type || '').toLowerCase();
          const placeName = place.name || place.display_name.split(',')[0] || '';
          const city = addr.city || addr.town || addr.village || addr.hamlet || addr.municipality || '';
          const state = addr.state || addr.region || '';
          const country = addr.country || '';

          const displayParts = [placeName];
          if (city && city !== placeName) {
            displayParts.push(city);
          }
          if (state) {
            displayParts.push(state);
          }
          if (country) {
            displayParts.push(country);
          }

          return {
            name: placeName,
            city,
            state,
            country,
            displayName: displayParts.filter(Boolean).join(', '),
            lat: parseFloat(place.lat),
            lon: parseFloat(place.lon),
            type
          };
        })
        .filter(p => {
          return (['city','town','village','municipality','hamlet'].includes(p.type) || (p.name && p.country));
        })
        .filter((v,i,a)=>a.findIndex(t=>t.displayName===v.displayName)===i)
        .slice(0,6);

      setLocationSuggestions(suggestions);
      setShowSuggestions(true);
    } catch (err) {
      console.error('Error fetching location suggestions:', err);
      setLocationSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleLocationInputChange = (e) => {
    const query = e.target.value;
    setLocationInput(query);
    
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchLocationSuggestions(query);
    }, 300);
  };

  const handleLocationSelect = (suggestion) => {
    setLocationInput(suggestion.displayName);
    setShowSuggestions(false);
    setLocationSuggestions([]);
    onLocationSelect(suggestion.displayName, { lat: suggestion.lat, lng: suggestion.lon });
  };

  const handleNext = () => {
    if (location && locationCoords) {
      onNext();
    }
  };

  return (
    <div className="step-container">
      <h2>Step 1: Choose Your Destination</h2>
      <p className="step-description">Select the city or location where you'd like to plan your trip.</p>
      
      <div className="form-group">
        <label htmlFor="location">Location</label>
        <div style={{ position: 'relative' }}>
          <input
            id="location"
            type="text"
            value={locationInput}
            onChange={handleLocationInputChange}
            placeholder="Search for a city..."
            autoComplete="off"
            className="form-input"
          />
          {isLoadingSuggestions && (
            <div className="loading-indicator">Loading...</div>
          )}
          {showSuggestions && locationSuggestions.length > 0 && (
            <div className="suggestions-dropdown">
              {locationSuggestions.map((suggestion, idx) => (
                <div
                  key={idx}
                  onClick={() => handleLocationSelect(suggestion)}
                  className="suggestion-item"
                >
                  <div className="suggestion-name">{suggestion.name}</div>
                  <div className="suggestion-details">{suggestion.displayName}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        {location && (
          <div className="selected-location">
            ✓ Selected: {location}
          </div>
        )}
      </div>

      <div className="step-actions">
        <div></div>
        <button
          type="button"
          onClick={handleNext}
          disabled={!location || !locationCoords}
          className="btn btn-primary"
        >
          Next: Set Radius
        </button>
      </div>
    </div>
  );
};

export default LocationStep;

