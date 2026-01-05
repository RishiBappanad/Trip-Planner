import React, { useState, useMemo } from 'react';
import { GoogleMap, Circle, useLoadScript } from '@react-google-maps/api';
import '../steps/steps.css';

const GOOGLE_MAPS_API_KEY = 'AIzaSyCaNKux4_R3TSDEUcF3KKd7UzE1WbiqnpY';

const RadiusStep = ({ location, locationCoords, radius, onRadiusChange, onNext, onBack }) => {
  const { isLoaded, loadError } = useLoadScript({ googleMapsApiKey: GOOGLE_MAPS_API_KEY });

  // Convert miles to meters for the circle
  const radiusInMeters = useMemo(() => {
    return radius * 1609.34; // 1 mile = 1609.34 meters
  }, [radius]);

  const mapContainerStyle = {
    width: '100%',
    height: '500px',
    borderRadius: '8px',
  };

  const mapOptions = {
    zoom: 11,
    center: locationCoords || { lat: 40.7128, lng: -74.0060 },
    mapTypeId: 'roadmap'
  };

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading map...</div>;

  return (
    <div className="step-container">
      <h2>Step 2: Set Your Travel Radius</h2>
      <p className="step-description">
        Choose how far you're willing to travel from your location (in miles).
        The circle on the map shows your selected radius.
      </p>
      
      <div className="form-group">
        <label htmlFor="radius">
          Radius: {radius} miles
        </label>
        <input
          id="radius"
          type="range"
          min="1"
          max="50"
          value={radius}
          onChange={(e) => onRadiusChange(Number(e.target.value))}
          className="form-slider"
        />
        <div className="slider-labels">
          <span>1 mile</span>
          <span>25 miles</span>
          <span>50 miles</span>
        </div>
      </div>

      <div className="map-wrapper">
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={locationCoords}
          zoom={mapOptions.zoom}
          options={mapOptions}
        >
          {locationCoords && (
            <Circle
              center={locationCoords}
              radius={radiusInMeters}
              options={{
                fillColor: '#3498db',
                fillOpacity: 0.2,
                strokeColor: '#2980b9',
                strokeOpacity: 0.8,
                strokeWeight: 2,
              }}
            />
          )}
        </GoogleMap>
      </div>

      <div className="step-actions">
        <button type="button" onClick={onBack} className="btn btn-secondary">
          Back
        </button>
        <button
          type="button"
          onClick={onNext}
          className="btn btn-primary"
        >
          Next: Choose Hotel
        </button>
      </div>
    </div>
  );
};

export default RadiusStep;

