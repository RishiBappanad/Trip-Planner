import React, { useState } from 'react';
import api from '../services/apiService';

function UserInputForm({ onItineraryFetch }) {
  const [city, setCity] = useState('');
  const [preferences, setPreferences] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/get-itinerary', { city, preferences });
      onItineraryFetch(response.data);
    } catch (error) {
      console.error('Error fetching itinerary:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Enter city"
        value={city}
        onChange={(e) => setCity(e.target.value)}
      />
      <input
        type="text"
        placeholder="Enter preferences"
        value={preferences}
        onChange={(e) => setPreferences(e.target.value)}
      />
      <button type="submit">Get Itinerary</button>
    </form>
  );
}

export default UserInputForm;
