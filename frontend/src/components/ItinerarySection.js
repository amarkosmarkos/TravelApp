import React from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemIcon, ListItemText, ListItemSecondaryAction } from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import PeopleIcon from '@mui/icons-material/People';
import MyLocationIcon from '@mui/icons-material/MyLocation';

const ItinerarySection = ({ cities }) => {
    const formatPopulation = (population) => {
        if (!population) return 'N/A';
        return new Intl.NumberFormat('es-ES').format(population);
    };

    const formatCoordinates = (coordinates) => {
        if (!coordinates) return 'N/A';
        return `${coordinates.latitude.toFixed(4)}, ${coordinates.longitude.toFixed(4)}`;
    };

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Paper 
                elevation={3} 
                sx={{ 
                    flex: 1, 
                    p: 3, 
                    backgroundColor: '#f5f5f5'
                }}
            >
                <Typography variant="h5" sx={{ mb: 3 }}>
                    Itinerario de Viaje
                </Typography>

                {cities && cities.length > 0 ? (
                    <List>
                        {cities.map((city, index) => (
                            <ListItem 
                                key={index}
                                sx={{
                                    backgroundColor: '#ffffff',
                                    mb: 2,
                                    borderRadius: 1,
                                    boxShadow: 1,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'flex-start'
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                    <ListItemIcon>
                                        <LocationOnIcon color="primary" />
                                    </ListItemIcon>
                                    <ListItemText 
                                        primary={city.name}
                                        primaryTypographyProps={{
                                            variant: 'h6'
                                        }}
                                    />
                                </Box>
                                
                                <Box sx={{ 
                                    display: 'flex', 
                                    gap: 2, 
                                    ml: 7, 
                                    mt: 1,
                                    color: 'text.secondary'
                                }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <PeopleIcon fontSize="small" />
                                        <Typography variant="body2">
                                            Población: {formatPopulation(city.population)}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <MyLocationIcon fontSize="small" />
                                        <Typography variant="body2">
                                            Coordenadas: {formatCoordinates(city.coordinates)}
                                        </Typography>
                                    </Box>
                                </Box>
                            </ListItem>
                        ))}
                    </List>
                ) : (
                    <Box 
                        sx={{ 
                            display: 'flex', 
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            textAlign: 'center'
                        }}
                    >
                        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                            No hay ciudades en el itinerario
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Comienza una conversación con el asistente de viajes para crear tu itinerario
                        </Typography>
                    </Box>
                )}
            </Paper>
        </Box>
    );
};

export default ItinerarySection; 