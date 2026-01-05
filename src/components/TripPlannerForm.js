// TripPlannerForm.js
import React, { useState } from 'react';
import LocationInput from './LocationInput';
import ToursList from './ToursList';
import MultiRangeSlider from './MultiRangeSlider';
import './TripPlannerForm.css';

const TripPlannerForm = () => {
  const [city, setCity] = useState('');
  const [carRental, setCarRental] = useState(false);
  const [budget, setBudget] = useState(50);
  const [duration, setDuration] = useState(1);
  // diningPreference: { fastFood: number, local: number, upscale: number }
  const [diningPreference, setDiningPreference] = useState({ fastFood: 30, local: 40, upscale: 30 });
  const [selectedTours, setSelectedTours] = useState([]);

  const handleFormSubmit = (e) => {
    e.preventDefault();
    // Submit form data to the backend API
  };

  return (
    <div className="trip-planner">
      <h1>Trip Planner</h1>
      <form onSubmit={handleFormSubmit}>
        <LocationInput city={city} setCity={setCity} />
        <label>
          <input
            type="checkbox"
            checked={carRental}
            onChange={() => setCarRental(!carRental)}
          />
          Rent a Car
        </label>
        <label>
          Hotel Budget per Night:
          <input
            type="range"
            min="50"
            max="1000"
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
          />
          ${budget}
        </label>
        <label>
          Stay Duration (days):
          <input
            type="range"
            min="1"
            max="30"
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
          {duration} days
        </label>
        {/* Dining Preference Slider */}
        <label>
          Dining Preferences:
          <MultiRangeSlider
            onChange={(values) => setDiningPreference(values)}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9em' }}>
            <span>Fast Food</span>
            <span>Local Dining</span>
            <span>High-End</span>
          </div>
        </label>
        <ToursList selectedTours={selectedTours} setSelectedTours={setSelectedTours} />
        <button type="submit">Submit</button>
      </form>
    </div>
  );
};

export default TripPlannerForm;
