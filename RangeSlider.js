// RangeSlider.js
import React, { useState } from 'react';

const RangeSlider = ({ diningPreference, setDiningPreference }) => {
  const handleSliderChange = (type, value) => {
    const updatedPreference = { ...diningPreference, [type]: value };
    const total = updatedPreference.fastFood + updatedPreference.local + updatedPreference.upscale;

    // Adjust percentages proportionally to keep total at 100%
    if (total === 100) {
      setDiningPreference(updatedPreference);
    }
  };

  return (
    <div>
      <label>Dining Preferences:</label>
      <div className="dining-sliders">
        <label>Fast Food: {diningPreference.fastFood}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={diningPreference.fastFood}
          onChange={(e) => handleSliderChange('fastFood', parseInt(e.target.value))}
        />
        <label>Local Food: {diningPreference.local}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={diningPreference.local}
          onChange={(e) => handleSliderChange('local', parseInt(e.target.value))}
        />
        <label>Upscale Dining: {diningPreference.upscale}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={diningPreference.upscale}
          onChange={(e) => handleSliderChange('upscale', parseInt(e.target.value))}
        />
      </div>
    </div>
  );
};

export default RangeSlider;
