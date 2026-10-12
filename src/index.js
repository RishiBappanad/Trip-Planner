import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// StrictMode is deliberately omitted: @react-google-maps/api's useLoadScript
// doesn't handle StrictMode's dev-only double effect invocation cleanly,
// injecting the Maps script twice and breaking the marker/poly libraries
// (manifests as a blank map + "Loader.provide not called" console errors).
// This only affects local dev; production builds never use StrictMode.
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
