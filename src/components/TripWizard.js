import React, { useState } from 'react';
import LocationStep from './steps/LocationStep';
import RadiusStep from './steps/RadiusStep';
import HotelStep from './steps/HotelStep';
import PreferencesStep from './steps/PreferencesStep';
import ItineraryDisplay from './ItineraryDisplay';
import './TripWizard.css';

const TripWizard = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    location: '',
    locationCoords: null, // { lat, lng }
    radius: 5, // in miles
    selectedHotel: null,
    checkInDate: new Date(),
    checkOutDate: new Date(Date.now() + 24 * 60 * 60 * 1000), // Tomorrow
    rentCar: false,
    budget: 100,
    duration: 1,
    selectedTours: [],
    diningPreference: {
      fastFood: 0,
      local: 0,
      upscale: 0,
    },
    mustVisitLocations: [],
  });
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateFormData = (updates) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const submitAndNext = async () => {
    await handleSubmit();
    setCurrentStep(5);
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (!formData.location || !formData.selectedHotel || !formData.checkInDate || !formData.checkOutDate) {
      setError('Please complete all required fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: formData.location,
          location_coords: formData.locationCoords,
          radius: formData.radius,
          hotel: formData.selectedHotel,
          rent_car: formData.rentCar,
          budget: Number(formData.budget),
          duration: Number(formData.duration),
          selected_tours: formData.selectedTours,
          food_percentages: [
            formData.diningPreference.fastFood,
            formData.diningPreference.local,
            formData.diningPreference.upscale,
          ],
          must_visit_locations: formData.mustVisitLocations,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setResponse(data);
      setError(null);
    } catch (err) {
      console.error("Error:", err.message);
      setError(err.message || 'Failed to submit form. Check backend connection.');
      setResponse(null);
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <LocationStep
            location={formData.location}
            locationCoords={formData.locationCoords}
            onLocationSelect={(location, coords) => {
              updateFormData({ location, locationCoords: coords });
            }}
            onNext={nextStep}
          />
        );
      case 2:
        return (
          <RadiusStep
            location={formData.location}
            locationCoords={formData.locationCoords}
            radius={formData.radius}
            onRadiusChange={(radius) => updateFormData({ radius })}
            onLocationCoordsChange={(coords) => {
              console.log('TripWizard: Updating locationCoords to', coords);
              updateFormData({ locationCoords: coords });
            }}
            onNext={nextStep}
            onBack={prevStep}
          />
        );
      case 3:
        return (
          <HotelStep
            location={formData.location}
            locationCoords={formData.locationCoords}
            radius={formData.radius}
            budget={formData.budget}
            selectedHotel={formData.selectedHotel}
            checkInDate={formData.checkInDate}
            checkOutDate={formData.checkOutDate}
            rentCar={formData.rentCar}
            duration={formData.duration}
            onBudgetChange={(budget) => updateFormData({ budget })}
            onHotelSelect={(hotel) => updateFormData({ selectedHotel: hotel })}
            onCheckInChange={(date) => updateFormData({ checkInDate: date })}
            onCheckOutChange={(date) => updateFormData({ checkOutDate: date })}
            onRentCarChange={(rentCar) => updateFormData({ rentCar })}
            onDurationChange={(duration) => updateFormData({ duration })}
            onNext={nextStep}
            onBack={prevStep}
          />
        );
      case 4:
        return (
          <PreferencesStep
            selectedTours={formData.selectedTours}
            diningPreference={formData.diningPreference}
            mustVisitLocations={formData.mustVisitLocations}
            onToursChange={(tours) => updateFormData({ selectedTours: tours })}
            onDiningChange={(pref) => updateFormData({ diningPreference: pref })}
            onMustVisitChange={(locations) => updateFormData({ mustVisitLocations: locations })}
            onSubmit={submitAndNext}
            onBack={prevStep}
            loading={loading}
          />
        );
      case 5:
        return (
          response && response.success ? (
            <ItineraryDisplay data={response} location={formData.location} />
          ) : (
            <div>Loading itinerary...</div>
          )
        );
      default:
        return null;
    }
  };

  return (
    <div className="trip-wizard">
      <div className="wizard-header">
        <h1>Trip Planner</h1>
        <div className="step-indicator">
          {[1, 2, 3, 4, 5].map((step) => (
            <div
              key={step}
              className={`step-dot ${currentStep >= step ? 'active' : ''} ${currentStep === step ? 'current' : ''}`}
            >
              {step}
            </div>
          ))}
        </div>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      <div className="wizard-content">
        {renderStep()}
      </div>


    </div>
  );
};

export default TripWizard;

