import React from 'react';
import ReactDualRangeSlider from '../ReactDualRangeSlider';
import '../steps/steps.css';

const tourOptions = ["City Tour", "Museum Tour", "Nature Tour", "Historical Tour", "Physical Activity"];

const PreferencesStep = ({ selectedTours, diningPreference, onToursChange, onDiningChange, onSubmit, onBack, loading }) => {
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

