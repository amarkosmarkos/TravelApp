import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Divider } from '@mui/material';
import CityList from './CityList';
import MapViewReal from './MapViewReal';

const ItinerarySection = ({ cities, travelId }) => {
    const [itinerary, setItinerary] = useState(null);
    const [error, setError] = useState(null);
    const [selectedCityIndex, setSelectedCityIndex] = useState(0);

    useEffect(() => {
        const fetchItinerary = async () => {
            if (!travelId) return;

            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    throw new Error('No authentication token found');
                }

                const response = await fetch(`http://localhost:8000/api/travels/${travelId}/itinerary`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Failed to load itinerary');
                }

                const data = await response.json();
                console.log('Itinerary data received:', data);
                if (data && data.length > 0) {
                    setItinerary(data[0]); // Take the first itinerary
                    console.log('Setting itinerary:', data[0]);
                }
                setError(null);
            } catch (error) {
                console.error('Error fetching itinerary:', error);
                setError(error.message);
                setItinerary(null);
            }
        };

        fetchItinerary();
    }, [travelId]);

    const handleCitySelect = (city, index) => {
        setSelectedCityIndex(index);
        console.log('Selected city:', city, 'Index:', index);
    };

    // Use itinerary.cities if available, otherwise use the cities prop
    const citiesToDisplay = itinerary?.cities || cities || [];
    console.log('Cities to display:', citiesToDisplay);

    if (error) {
        return (
            <Box sx={{ 
                p: 3, 
                textAlign: 'center',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
            }}>
                <Typography color="error" variant="h6" gutterBottom>
                    Error loading itinerary
                </Typography>
                <Typography color="error" variant="body2">
                    {error}
                </Typography>
            </Box>
        );
    }

    if (!itinerary && (!cities || cities.length === 0)) {
        return (
            <Box sx={{ 
                p: 3, 
                textAlign: 'center',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
            }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                    No itinerary available
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    The itinerary will be generated when your travel request is processed.
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ 
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            {/* Header */}
            <Box sx={{ 
                p: 3, 
                borderBottom: '1px solid',
                borderColor: 'divider',
                backgroundColor: 'background.paper',
                flexShrink: 0
            }}>
                <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                    Travel Itinerary
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {citiesToDisplay.length} cities in your travel route
                </Typography>
            </Box>

            {/* Two Column Layout */}
            <Box sx={{ 
                flex: 1,
                display: 'flex',
                overflow: 'hidden',
                minHeight: 0
            }}>
                {/* Left Column - City List (40%) */}
                <Box sx={{ 
                    width: '40%',
                    borderRight: '1px solid',
                    borderColor: 'divider',
                    backgroundColor: 'background.paper',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }}>
                    <CityList 
                        cities={citiesToDisplay}
                        selectedCityIndex={selectedCityIndex}
                        onCitySelect={handleCitySelect}
                    />
                </Box>

                {/* Right Column - Real Map View (60%) */}
                <Box sx={{ 
                    width: '60%',
                    backgroundColor: 'background.paper',
                    position: 'relative',
                    overflow: 'hidden'
                }}>
                    <MapViewReal 
                        cities={citiesToDisplay}
                        selectedCityIndex={selectedCityIndex}
                        onCitySelect={handleCitySelect}
                    />
                </Box>
            </Box>
        </Box>
    );
};

export default ItinerarySection; 