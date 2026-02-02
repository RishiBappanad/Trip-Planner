import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { GoogleMap, Marker, InfoWindow, Polyline, useLoadScript } from '@react-google-maps/api';
import '../styles/ItineraryDisplay.css';
import useGoogleMapsKey from './useGoogleMapsKey';

const typeColors = {
  'landmark': '#FF6B6B',
  'museum': '#4ECDC4',
  'park': '#95E1D3',
  'historical monument': '#F38181',
  'sports center': '#AA96DA',
  'fast food restaurant': '#FCBAD3',
  'local restaurant': '#A8D8EA',
  'fine dining restaurant': '#FFD700',
  'default': '#3498DB'
};

const ItineraryDisplay = ({ data, location }) => {
  const { apiKey, loading: keyLoading, error: keyError } = useGoogleMapsKey();
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [expandedDay, setExpandedDay] = useState(-1);
  const [zoom, setZoom] = useState(12);

  if (keyLoading) return <div>Loading API key...</div>;
  if (keyError) return <div>Error loading API key</div>;

  const { isLoaded, loadError } = useLoadScript({ googleMapsApiKey: apiKey });

  // Default city coord fallback map
  const coordMap = useMemo(() => ({
    'new york': { lat: 40.7128, lng: -74.0060 },
    'los angeles': { lat: 34.0522, lng: -118.2437 },
    'chicago': { lat: 41.8781, lng: -87.6298 },
    'san francisco': { lat: 37.7749, lng: -122.4194 },
    'boston': { lat: 42.3601, lng: -71.0589 }
  }), []);

  // Places state: flatten incoming data and keep coordinates (may be null initially)
  const [places, setPlaces] = useState([]);
  const [center, setCenter] = useState(() => {
    const city = (location || '').toLowerCase().split(',')[0].trim();
    return coordMap[city] || { lat: 40.7128, lng: -74.0060 };
  });

  // Calculate average center from all places with valid coordinates
  const averageCenter = useMemo(() => {
    const validPlaces = places.filter(p => p.lat != null && p.lng != null);
    if (validPlaces.length === 0) {
      return null;
    }
    const sumLat = validPlaces.reduce((sum, p) => sum + p.lat, 0);
    const sumLng = validPlaces.reduce((sum, p) => sum + p.lng, 0);
    return {
      lat: sumLat / validPlaces.length,
      lng: sumLng / validPlaces.length
    };
  }, [places]);

  // Calculate center for the selected day
  const dayCenter = useMemo(() => {
    if (expandedDay === -1) return null;
    const dayPlaces = places.filter(p => p.day === expandedDay + 1);
    const validPlaces = dayPlaces.filter(p => p.lat != null && p.lng != null);
    if (validPlaces.length === 0) return null;
    const sumLat = validPlaces.reduce((sum, p) => sum + p.lat, 0);
    const sumLng = validPlaces.reduce((sum, p) => sum + p.lng, 0);
    return {
      lat: sumLat / validPlaces.length,
      lng: sumLng / validPlaces.length
    };
  }, [places, expandedDay]);

  // Update center based on selected day or overall average
  useEffect(() => {
    if (dayCenter) {
      setCenter(dayCenter);
    } else if (averageCenter) {
      setCenter(averageCenter);
    }
  }, [dayCenter, averageCenter]);

  // Update zoom based on selected day
  useEffect(() => {
    setZoom(expandedDay === -1 ? 12 : 14);
  }, [expandedDay]);

  // Build initial places whenever data changes
  useEffect(() => {
    if (!data || !data.daily_itineraries) {
      setPlaces([]);
      return;
    }
    const flat = data.daily_itineraries.flatMap((day, dayIdx) =>
      day.places.map((place, placeIdx) => ({
        id: `${dayIdx}-${placeIdx}`,
        name: place.name,
        type: place.type,
        address: place.address,
        day: day.day || dayIdx + 1,
        placeIdx,
        // Prefer backend-provided coords
        lat: place.lat ? Number(place.lat) : null,
        lng: place.lon ? Number(place.lon) : null
      }))
    );
    setPlaces(flat);
  }, [data, coordMap, location]);

  // Helper: promisified geocode using Google Maps Geocoder
  const geocodeAddress = (geocoder, address) => {
    return new Promise((resolve) => {
      if (!address) return resolve(null);
      geocoder.geocode({ address }, (results, status) => {
        if (status === 'OK' && results && results[0] && results[0].geometry && results[0].geometry.location) {
          const loc = results[0].geometry.location;
          resolve({ lat: loc.lat(), lng: loc.lng() });
        } else {
          resolve(null);
        }
      });
    });
  };

  // When Maps API loaded, geocode any missing place coords
  useEffect(() => {
    if (!isLoaded || !window.google) return;
    const geocoder = new window.google.maps.Geocoder();

    // Geocode missing place coords sequentially to be polite with quota
    (async () => {
      const updated = [...places];
      let changed = false;
      for (let i = 0; i < updated.length; i++) {
        if (updated[i].lat == null || updated[i].lng == null) {
          const addressToUse = updated[i].address || `${updated[i].name}, ${location}`;
          try {
            const res = await geocodeAddress(geocoder, addressToUse);
            if (res) {
              updated[i].lat = res.lat;
              updated[i].lng = res.lng;
              changed = true;
            } else {
              // fallback: use current center if available, otherwise skip
              if (center) {
                updated[i].lat = center.lat + (Math.random() - 0.5) * 0.02;
                updated[i].lng = center.lng + (Math.random() - 0.5) * 0.02;
                changed = true;
              }
            }
          } catch (err) {
            // fallback: use current center if available
            if (center) {
              updated[i].lat = center.lat + (Math.random() - 0.5) * 0.02;
              updated[i].lng = center.lng + (Math.random() - 0.5) * 0.02;
              changed = true;
            }
          }
          // small delay to avoid spamming geocoding quota
          await new Promise(r => setTimeout(r, 150));
        }
      }
      if (changed) setPlaces(updated);
    })();
  }, [isLoaded, places.length, location]);

  // Create polylines for each day
  const dayPolylines = useMemo(() => {
    if (!data.daily_itineraries) return [];
    return data.daily_itineraries.map((day, dayIdx) => {
      const dayPlaces = places.filter(p => p.day === dayIdx + 1);
      if (dayPlaces.length < 2) return null;
      return {
        day: dayIdx + 1,
        path: dayPlaces.map(p => ({ lat: p.lat, lng: p.lng }))
      };
    });
  }, [data.daily_itineraries, places]);

  const getMarkerColor = (type) => {
    return typeColors[type] || typeColors['default'];
  };

  const mapContainerStyle = {
    width: '100%',
    height: '500px',
    borderRadius: '8px',
    marginBottom: '20px'
  };

  const mapOptions = {
    center: center,
    mapTypeId: 'roadmap'
  };

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading map...</div>;

  return (
    <div className="itinerary-display">
      <div className="itinerary-header">
        <h2>🗺️ Your Trip to {location}</h2>
        <p className="trip-summary">
          {data.duration} day{data.duration > 1 ? 's' : ''} • {data.total_tours} attractions • {data.total_food} restaurants
        </p>
      </div>

      {/* Google Map */}
      <div className="map-container">
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={center}
          zoom={zoom}
          options={mapOptions}
        >
          {/* Draw polylines for each day */}
          {dayPolylines.filter(poly => expandedDay === -1 || poly.day === expandedDay + 1).map((polyline, idx) =>
            polyline && (
              <Polyline
                key={`polyline-day-${polyline.day}`}
                path={polyline.path}
                options={{
                  strokeColor: `hsl(${(polyline.day - 1) * 60 % 360}, 70%, 50%)`,
                  strokeOpacity: 0.7,
                  strokeWeight: 3
                }}
              />
            )
          )}

          {/* Markers for places */}
          {places.filter(p => expandedDay === -1 || p.day === expandedDay + 1).map((place) => (
            <Marker
              key={`marker-${place.id}`}
              position={{ lat: place.lat ?? (center.lat + (Math.random() - 0.5) * 0.02), lng: place.lng ?? (center.lng + (Math.random() - 0.5) * 0.02) }}
              onClick={() => setSelectedMarker(place.id)}
              title={place.name}
              icon={{
                path: 'M0-48c-26.4 0-48 21.6-48 48s21.6 48 48 48 48-21.6 48-48-21.6-48-48-48z',
                fillColor: getMarkerColor(place.type),
                fillOpacity: 1,
                scale: 0.3,
                strokeColor: '#fff',
                strokeWeight: 1
              }}
            >
              {selectedMarker === place.id && (
                <InfoWindow
                  onCloseClick={() => setSelectedMarker(null)}
                >
                  <div className="info-window">
                    <h3>{place.name}</h3>
                    <p><strong>Type:</strong> {place.type}</p>
                    <p><strong>Address:</strong> {place.address}</p>
                    <p><strong>Day:</strong> {place.day}</p>
                  </div>
                </InfoWindow>
              )}
            </Marker>
          ))}
        </GoogleMap>
      </div>

      {/* Day-by-Day Itinerary */}
      <div className="itinerary-container">
        <h3>📅 Day-by-Day Itinerary</h3>
        {data.daily_itineraries.map((day, dayIdx) => (
          <div key={`day-${dayIdx}`} className="day-card">
            <div
              className="day-header"
              onClick={() => setExpandedDay(expandedDay === dayIdx ? -1 : dayIdx)}
            >
              <h4>Day {day.day}</h4>
              <span className="day-count">{day.places.length} activities</span>
              <span className="expand-icon">{expandedDay === dayIdx ? '▼' : '▶'}</span>
            </div>

            {expandedDay === dayIdx && (
              <div className="day-places">
                {day.places.map((place, placeIdx) => {
                  const placeObj = places.find(p => p.day === day.day && p.placeIdx === placeIdx);
                  return (
                    <div
                      key={`place-${dayIdx}-${placeIdx}`}
                      className="place-item"
                      onMouseEnter={() => placeObj && setSelectedMarker(placeObj.id)}
                      onMouseLeave={() => setSelectedMarker(null)}
                    >
                      <div className="place-number">{placeIdx + 1}</div>
                      <div className="place-details">
                        <h5>{place.name}</h5>
                        <p className="place-type">{place.type}</p>
                        <p className="place-address">{place.address}</p>
                      </div>
                      <div
                        className="place-color-indicator"
                        style={{ backgroundColor: getMarkerColor(place.type) }}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Trip Summary */}
      <div className="trip-details">
        <div className="detail-box">
          <span className="detail-label">Location:</span>
          <span className="detail-value">{data.location}</span>
        </div>
        <div className="detail-box">
          <span className="detail-label">Duration:</span>
          <span className="detail-value">{data.duration} days</span>
        </div>
        <div className="detail-box">
          <span className="detail-label">Transport:</span>
          <span className="detail-value">{data.rent_car ? '🚗 Car' : '🚌 Transit'}</span>
        </div>
        <div className="detail-box">
          <span className="detail-label">Budget/Night:</span>
          <span className="detail-value">${data.budget}</span>
        </div>
      </div>
    </div>
  );
};

export default ItineraryDisplay;
