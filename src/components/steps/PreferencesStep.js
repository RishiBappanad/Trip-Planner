import React, { useState } from 'react';
import ReactDualRangeSlider from '../ReactDualRangeSlider';
import '../steps/steps.css';

const tourOptions = ["City Tour", "Museum Tour", "Nature Tour", "Historical Tour", "Physical Activity"];

const PreferencesStep = ({ selectedTours, diningPreference, mustVisitLocations, onToursChange, onDiningChange, onMustVisitChange, onSubmit, onBack, loading }) => {
  const [newLocation, setNewLocation] = useState({ name: '', type: 'Tour', address: '' });

  const handleTourSelect = (tour) => {
    const newTours = selectedTours.includes(tour)
      ? selectedTours.filter(t => t !== tour)
      : [...selectedTours, tour];
    onToursChange(newTours);
  };

  return (
    <div className="step-container">
      <h2>Step 5: Dining & Tour Preferences</h2>
      <p className="step-description">
        Select your preferred tours and dining preferences to customize your itinerary.
      </p>
      
      <div className="form-group">
        <label>Tours</label>
        <div className="tours-grid">
          {tourOptions.map((tour, index) => (
            <label key={index} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedTours.includes(tour)}
                onChange={() => handleTourSelect(tour)}
                className="form-checkbox"
              />
              <span>{tour}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Dining Preferences</label>
        <ReactDualRangeSlider
          limits={[0, 100]}
          values={[
            diningPreference.fastFood || 0,
            Math.min(100, (diningPreference.fastFood || 0) + (diningPreference.local || 0)),
          ]}
          lock={[false, false]}
          reverse={false}
          formatFunc={(v) => v}
          rangeColor="#4c6ef5"
          onChange={(vals) => {
            const low = Number(vals[0]) || 0;
            const high = Number(vals[1]) || 0;
            const ff = Math.max(0, Math.min(100, Math.round(low)));
            const u = Math.max(0, Math.min(100, Math.round(high)));
            const local = Math.max(0, Math.min(100, u - ff));
            const upscale = Math.max(0, 100 - u);
            onDiningChange({ fastFood: ff, local, upscale });
          }}
        />
        <div className="dining-labels">
          <span>Fast Food: {diningPreference.fastFood}%</span>
          <span>Local Dining: {diningPreference.local}%</span>
          <span>High-End: {diningPreference.upscale}%</span>
        </div>
      </div>

      <div className="form-group">
        <label>Must-Visit Locations (Optional)</label>
        <p className="step-description">Add specific locations you want to visit with custom name and type.</p>
        <div className="must-visit-input">
          <input
            type="text"
            value={newLocation.name}
            onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
            placeholder="Name, e.g., White House"
            className="form-input"
          />
          <select
            value={newLocation.type}
            onChange={(e) => setNewLocation({ ...newLocation, type: e.target.value })}
            className="form-select"
          >
            <option value="Tour">Tour</option>
            <option value="Food">Food</option>
            <option value="Other">Other</option>
          </select>
          <input
            type="text"
            value={newLocation.address}
            onChange={(e) => setNewLocation({ ...newLocation, address: e.target.value })}
            placeholder="Address, e.g., 1600 Pennsylvania Avenue NW, Washington, DC"
            className="form-input"
          />
          <button
            type="button"
            onClick={() => {
              if (newLocation.name.trim() && newLocation.address.trim()) {
                onMustVisitChange([...mustVisitLocations, { ...newLocation }]);
                setNewLocation({ name: '', type: 'Tour', address: '' });
              }
            }}
            className="btn btn-secondary"
          >
            Add Location
          </button>
        </div>
        {mustVisitLocations.length > 0 && (
          <ul className="must-visit-list">
            {mustVisitLocations.map((loc, idx) => (
              <li key={idx} className="must-visit-item">
                <strong>{loc.name}</strong> ({loc.type}): {loc.address}
                <button
                  type="button"
                  onClick={() => onMustVisitChange(mustVisitLocations.filter((_, i) => i !== idx))}
                  className="remove-btn"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="step-actions">
        <button type="button" onClick={onBack} className="btn btn-secondary">
          Back
        </button>
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || selectedTours.length === 0}
          className="btn btn-primary"
        >
          {loading ? 'Creating Itinerary...' : 'Create My Itinerary'}
        </button>
      </div>
    </div>
  );
};

export default PreferencesStep;

