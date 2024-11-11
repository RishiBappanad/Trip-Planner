import React, { useState } from 'react';
import './App.css';
import RangeSlider from './components/RangeSlider';


function App() {
  const [location, setLocation] = useState('');
  const [rentCar, setRentCar] = useState(false);
  const [budget, setBudget] = useState(100);
  const [duration, setDuration] = useState(1);
  const [selectedTours, setSelectedTours] = useState([]);
  const [response, setResponse] = useState(null);
  const [diningPreference, setDiningPreference] = useState({
    fastFood: 0,
    local: 0,
    upscale: 0,
  });
  

  const tourOptions = ["City Tour", "Museum Tour", "Nature Tour", "Historical Tour", "Physical Activity"];

  const handleTourSelect = (tour) => {
    setSelectedTours(prev =>
      prev.includes(tour) ? prev.filter(t => t !== tour) : [...prev, tour]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('http://127.0.0.1:5000/api/submit/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location,
          rent_car: rentCar,
          budget,
          duration,
          selected_tours: selectedTours,
          food_percentages: [
            diningPreference.fastFood,
            diningPreference.local,
            diningPreference.upscale,
          ],
        }),
      });
    
      // Check if the response status is not OK (not in the 200-299 range)
      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }
    
      const data = await response.json();
      setResponse(data);
    
    } catch (error) {
      // Network errors or JSON parsing errors
      if (error.name === 'TypeError') {
        console.error("Network error or CORS issue:", error);
      } else if (error.name === 'SyntaxError') {
        console.error("Failed to parse JSON response:", error);
      } else {
        console.error("Error:", error.message);
      }
    }    
  };

  return (
    <div className="App">
      <h1>Trip Planner</h1>
      <form onSubmit={handleSubmit}>
        <label>Enter Location:</label>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />

        <label>
          <input
            type="checkbox"
            checked={rentCar}
            onChange={(e) => setRentCar(e.target.checked)}
          />
          Rent a Car
        </label>

        <label>Hotel Budget per Night: ${budget}</label>
        <input
          type="range"
          min="50"
          max="1000"
          value={budget}
          onChange={(e) => setBudget(Number(e.target.value))}
        />

        <label>Stay Duration (days): {duration}</label>
        <input
          type="range"
          min="1"
          max="30"
          value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
        />

        {/* Dining preference sliders */}
        <RangeSlider
          diningPreference={diningPreference}
          setDiningPreference={setDiningPreference}
        />

        <label>Tours:</label>
        {tourOptions.map((tour, index) => (
          <div key={index}>
            <label>
              <input
                type="checkbox"
                checked={selectedTours.includes(tour)}
                onChange={() => handleTourSelect(tour)}
              />
              {tour}
            </label>
          </div>
        ))}

        <button type="submit">Submit</button>
      </form>

      {response && (
        <div>
          <h2>Itinerary</h2>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
