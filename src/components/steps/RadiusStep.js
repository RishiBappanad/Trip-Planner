import React, { useState, useEffect, useMemo } from 'react';
import { GoogleMap, Circle, Marker, useLoadScript } from '@react-google-maps/api';
import '../steps/steps.css';
import useGoogleMapsKey from '../useGoogleMapsKey';

const RadiusStep = ({
  location,
  locationCoords,
  radius,
  onRadiusChange,
  onLocationCoordsChange,
  onNext,
  onBack,
}) => {
  const { apiKey, loading: keyLoading, error: keyError } = useGoogleMapsKey();
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: apiKey,
  });

  // Single source of truth
  const [center, setCenter] = useState(locationCoords);

  useEffect(() => {
    setCenter(locationCoords);
  }, [locationCoords]);

  const radiusInMeters = useMemo(() => radius * 1609.34, [radius]);

  const mapContainerStyle = {
    width: '100%',
    height: '500px',
    borderRadius: '8px',
  };

  const mapOptions = {
    zoom: 11,
    mapTypeId: 'roadmap',
    disableDefaultUI: false,
  };

  if (keyLoading) return <div>Loading API key...</div>;
  if (keyError) return <div>Error loading API key</div>;

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded || !center) return <div>Loading map...</div>;

  return (
    <div className="step-container">
      <h2>Step 2: Set Your Travel Radius</h2>
      <p className="step-description">
        Drag the marker to adjust your location. The circle shows how far you're
        willing to travel.
      </p>

      <div className="form-group">
        <label htmlFor="radius">Radius: {radius} miles</label>
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
          center={center}
          zoom={11}
          options={mapOptions}
        >
          {/* Visual radius */}
          <Circle
            center={center}
            radius={radiusInMeters}
            options={{
              fillColor: '#3498db',
              fillOpacity: 0.2,
              strokeColor: '#2980b9',
              strokeOpacity: 0.8,
              strokeWeight: 2,
              clickable: false,
            }}
          />

          {/* Draggable center */}
          <Marker
            position={center}
            draggable
            title="Drag to adjust location"
            onDragEnd={(e) => {
              const newCenter = {
                lat: e.latLng.lat(),
                lng: e.latLng.lng(),
              };

              setCenter(newCenter);
              onLocationCoordsChange?.(newCenter);
            }}
          />
        </GoogleMap>
      </div>

      <div className="step-actions">
        <button type="button" onClick={onBack} className="btn btn-secondary">
          Back
        </button>
        <button type="button" onClick={onNext} className="btn btn-primary">
          Next: Choose Hotel
        </button>
      </div>
    </div>
  );
};

export default RadiusStep;
