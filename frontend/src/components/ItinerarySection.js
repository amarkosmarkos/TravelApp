import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';

const ItinerarySection = ({ cities, travelId }) => {
    const [itinerary, setItinerary] = useState(null);
    const [error, setError] = useState(null);

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
                if (data && data.length > 0) {
                    setItinerary(data[0]); // Tomamos el primer itinerario
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

    const formatCoordinates = (coordinates) => {
        if (!coordinates) return 'N/A';
        return `${coordinates.latitude.toFixed(4)}, ${coordinates.longitude.toFixed(4)}`;
    };

    if (error) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography color="error">{error}</Typography>
            </Box>
        );
    }

    if (!itinerary || !itinerary.cities || itinerary.cities.length === 0) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography>No hay itinerario disponible para este viaje.</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
                Itinerario de Viaje
            </Typography>
            <List>
                {itinerary.cities.map((city, index) => (
                    <ListItem key={index}>
                        <ListItemIcon>
                            <LocationOnIcon />
                        </ListItemIcon>
                        <ListItemText
                            primary={city.name}
                            secondary={
                                city.coordinates && (
                                    <Typography component="span" variant="body2">
                                        Coordenadas: {formatCoordinates(city.coordinates)}
                                    </Typography>
                                )
                            }
                        />
                    </ListItem>
                ))}
            </List>
        </Box>
    );
};

export default ItinerarySection; 