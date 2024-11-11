// ToursList.js
import React from 'react';

const ToursList = ({ selectedTours, setSelectedTours }) => {
  const tourOptions = ["City Tour", "Museum Tour", "Nature Tour", "Historical Tour", "Physical Activity"];

  const handleTourSelection = (tour) => {
    setSelectedTours((prev) =>
      prev.includes(tour) ? prev.filter((t) => t !== tour) : [...prev, tour]
    );
  };

  return (
    <div>
      <label>Tours:</label>
      {tourOptions.map((tour, index) => (
        <div key={index}>
          <input
            type="checkbox"
            checked={selectedTours.includes(tour)}
            onChange={() => handleTourSelection(tour)}
          />
          {tour}
        </div>
      ))}
    </div>
  );
};

export default ToursList;
