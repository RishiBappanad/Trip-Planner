// TripPlannerForm.js
import React, { useState } from 'react';
import LocationInput from './LocationInput';
import RangeSlider from './RangeSlider';
import './TripPlannerForm.css';

const TripPlannerForm = () => {
  const [city, setCity] = useState('');
  const [carRental, setCarRental] = useState(false);
  const [budget, setBudget] = useState(50);
  const [duration, setDuration] = useState(1);
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
            onChange={(e) => setBudget(e.target.value)}
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
            onChange={(e) => setDuration(e.target.value)}
          />
          {duration} days
        </label>
        <RangeSlider diningPreference={diningPreference} setDiningPreference={setDiningPreference} />
        <ToursList selectedTours={selectedTours} setSelectedTours={setSelectedTours} />
        <button type="submit">Submit</button>
      </form>
    </div>
  );
};

export default TripPlannerForm;
