import { useState, useEffect } from 'react';
import { API_BASE } from '../config';

const useGoogleMapsKey = () => {
    const [apiKey, setApiKey] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE}/api/config/google-maps-key`)
            .then(response => response.json())
            .then(data => {
                setApiKey(data.key);
                setLoading(false);
            })
            .catch(err => {
                setError(err);
                setLoading(false);
            });
    }, []);

    return { apiKey, loading, error };
};

export default useGoogleMapsKey;