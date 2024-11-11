// LocationInput.js
import React, { useState } from 'react';

const LocationInput = ({ city, setCity }) => {
  const [suggestions, setSuggestions] = useState([]);
  
  const handleInputChange = async (e) => {
    const query = e.target.value;
    setCity(query);

    if (query.length > 2) {
      // Replace with your API call for suggestions
      const response = await fetch(`http://localhost:5000/api/autocomplete?query=${query}`);
      const data = await response.json();
      setSuggestions(data.results);
    } else {
      setSuggestions([]);
    }
  };

  return (
    <div>
      <label>Enter Location:</label>
      <input type="text" value={city} onChange={handleInputChange} />
      {suggestions.length > 0 && (
        <ul>
          {suggestions.map((suggestion, index) => (
            <li key={index} onClick={() => setCity(suggestion)}>
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default LocationInput;
