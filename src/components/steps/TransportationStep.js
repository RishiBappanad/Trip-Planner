import React from 'react';
import '../steps/steps.css';

const TransportationStep = ({ rentCar, duration, onRentCarChange, onDurationChange, onNext, onBack }) => {
  return (
    <div className="step-container">
      <h2>Step 4: Transportation & Duration</h2>
      <p className="step-description">
        Choose your transportation method and how long you'll be staying.
      </p>
      
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

      <div className="form-group">
        <label htmlFor="duration">
          Trip Duration: {duration} {duration === 1 ? 'day' : 'days'}
        </label>
        <input
          id="duration"
          type="range"
          min="1"
          max="30"
          value={duration}
          onChange={(e) => onDurationChange(Number(e.target.value))}
          className="form-slider"
        />
        <div className="slider-labels">
          <span>1 day</span>
          <span>15 days</span>
          <span>30 days</span>
        </div>
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
          Next: Preferences
        </button>
      </div>
    </div>
  );
};

export default TransportationStep;

