import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Typography, 
    Paper,
    IconButton,
    Tooltip,
    Chip,
    LinearProgress
} from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import MapIcon from '@mui/icons-material/Map';

const MapView = ({ cities = [], selectedCityIndex = 0, onCitySelect }) => {
    const [mapLoaded, setMapLoaded] = useState(false);
    const [loadingProgress, setLoadingProgress] = useState(0);

    // Simulated map loading with progress
    useEffect(() => {
        const timer = setTimeout(() => {
            setMapLoaded(true);
        }, 1500);

        const progressTimer = setInterval(() => {
            setLoadingProgress(prev => {
                if (prev >= 100) {
                    clearInterval(progressTimer);
                    return 100;
                }
                return prev + 10;
            });
        }, 150);

        return () => {
            clearTimeout(timer);
            clearInterval(progressTimer);
        };
    }, []);

    if (!cities || cities.length === 0) {
        return (
            <Box sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                p: 3,
                textAlign: 'center'
            }}>
                <MapIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                    No cities to display
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    The map will be displayed when there are cities in the itinerary
                </Typography>
            </Box>
        );
    }

    // Filter cities with valid coordinates
    const citiesWithCoordinates = cities.filter(city => {
        // Check for both possible coordinate structures
        const hasCoordinates = city.coordinates && 
            city.coordinates.latitude && 
            city.coordinates.longitude;
        
        const hasDirectCoordinates = city.latitude && city.longitude;
        
        return hasCoordinates || hasDirectCoordinates;
    });

    // Transform cities to have consistent coordinate structure
    const processedCities = citiesWithCoordinates.map(city => {
        let latitude, longitude;
        
        if (city.coordinates && city.coordinates.latitude && city.coordinates.longitude) {
            // Use coordinates object structure
            latitude = city.coordinates.latitude;
            longitude = city.coordinates.longitude;
        } else if (city.latitude && city.longitude) {
            // Use direct latitude/longitude structure
            latitude = city.latitude;
            longitude = city.longitude;
        } else {
            return null;
        }
        
        return {
            ...city,
            coordinates: {
                latitude: latitude,
                longitude: longitude
            }
        };
    }).filter(city => city !== null);

    if (processedCities.length === 0) {
        return (
            <Box sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                p: 3,
                textAlign: 'center'
            }}>
                <LocationOnIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                    No coordinates available
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Cities don't have coordinates to display on the map
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Map Header */}
            <Box sx={{ 
                p: 2, 
                borderBottom: '1px solid',
                borderColor: 'divider',
                backgroundColor: 'background.paper',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                        Itinerary Map
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {processedCities.length} locations marked
                    </Typography>
                </Box>
                
                {/* Map Controls */}
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Center map">
                        <IconButton size="small">
                            <MyLocationIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Zoom in">
                        <IconButton size="small">
                            <ZoomInIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Zoom out">
                        <IconButton size="small">
                            <ZoomOutIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Fullscreen">
                        <IconButton size="small">
                            <FullscreenIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* Map Container */}
            <Box sx={{ 
                flex: 1, 
                position: 'relative',
                background: `
                    linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 50%, #e8f5e8 100%),
                    radial-gradient(circle at 20% 80%, #81c784 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, #64b5f6 0%, transparent 50%),
                    radial-gradient(circle at 40% 40%, #ffb74d 0%, transparent 50%)
                `,
                backgroundSize: '100% 100%, 200px 200px, 150px 150px, 100px 100px',
                backgroundPosition: '0 0, 0 0, 0 0, 0 0',
                backgroundRepeat: 'no-repeat, no-repeat, no-repeat, no-repeat',
                overflow: 'hidden'
            }}>
                {/* Grid Pattern Overlay */}
                <Box sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundImage: `
                        linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
                    `,
                    backgroundSize: '20px 20px',
                    opacity: 0.3
                }} />

                {/* Water Bodies */}
                <Box sx={{
                    position: 'absolute',
                    top: '60%',
                    left: '10%',
                    width: '15%',
                    height: '8%',
                    borderRadius: '50%',
                    background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                    opacity: 0.6,
                    transform: 'rotate(-15deg)'
                }} />
                
                <Box sx={{
                    position: 'absolute',
                    top: '20%',
                    right: '15%',
                    width: '12%',
                    height: '6%',
                    borderRadius: '50%',
                    background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                    opacity: 0.4,
                    transform: 'rotate(25deg)'
                }} />

                {/* Roads */}
                <Box sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '5%',
                    right: '5%',
                    height: '2px',
                    background: 'linear-gradient(90deg, #8d6e63, #a1887f, #8d6e63)',
                    opacity: 0.7,
                    transform: 'rotate(-5deg)'
                }} />

                <Box sx={{
                    position: 'absolute',
                    top: '30%',
                    left: '20%',
                    width: '60%',
                    height: '2px',
                    background: 'linear-gradient(90deg, #8d6e63, #a1887f, #8d6e63)',
                    opacity: 0.7,
                    transform: 'rotate(15deg)'
                }} />

                {!mapLoaded ? (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        borderRadius: 2,
                        p: 3,
                        minWidth: 200
                    }}>
                        <MapIcon sx={{ fontSize: 32, color: 'primary.main', mb: 2 }} />
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Loading map...
                        </Typography>
                        <LinearProgress 
                            variant="determinate" 
                            value={loadingProgress} 
                            sx={{ mt: 1, width: '100%' }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            {loadingProgress}%
                        </Typography>
                    </Box>
                ) : (
                    <>
                        {/* City Markers */}
                        {processedCities.map((city, index) => {
                            // Calculate position based on index for better distribution
                            const baseX = 20 + (index * 15);
                            const baseY = 25 + (index * 12);
                            const x = Math.min(Math.max(baseX, 10), 80);
                            const y = Math.min(Math.max(baseY, 15), 75);
                            
                            return (
                                <Box
                                    key={index}
                                    sx={{
                                        position: 'absolute',
                                        left: `${x}%`,
                                        top: `${y}%`,
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease',
                                        transform: selectedCityIndex === index ? 'scale(1.2)' : 'scale(1)',
                                        zIndex: selectedCityIndex === index ? 2 : 1
                                    }}
                                    onClick={() => onCitySelect && onCitySelect(city, index)}
                                >
                                    {/* Connection Line to next city */}
                                    {index < processedCities.length - 1 && (
                                        <Box sx={{
                                            position: 'absolute',
                                            top: '50%',
                                            left: '50%',
                                            width: '60px',
                                            height: '2px',
                                            background: selectedCityIndex === index ? 
                                                'linear-gradient(90deg, #1976d2, #42a5f5)' : 
                                                'linear-gradient(90deg, #bdbdbd, #e0e0e0)',
                                            transform: 'translate(-50%, -50%) rotate(45deg)',
                                            opacity: selectedCityIndex === index ? 0.8 : 0.4,
                                            zIndex: -1
                                        }} />
                                    )}

                                    {/* Marker */}
                                    <Box sx={{
                                        position: 'relative',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center'
                                    }}>
                                        {/* Pulse effect for selected marker */}
                                        {selectedCityIndex === index && (
                                            <Box sx={{
                                                position: 'absolute',
                                                top: '50%',
                                                left: '50%',
                                                transform: 'translate(-50%, -50%)',
                                                width: 60,
                                                height: 60,
                                                borderRadius: '50%',
                                                background: 'radial-gradient(circle, rgba(25, 118, 210, 0.3) 0%, transparent 70%)',
                                                animation: 'pulse 2s infinite'
                                            }} />
                                        )}

                                        <Box sx={{
                                            width: selectedCityIndex === index ? 44 : 36,
                                            height: selectedCityIndex === index ? 44 : 36,
                                            borderRadius: '50%',
                                            background: selectedCityIndex === index ? 
                                                'linear-gradient(135deg, #1976d2, #42a5f5)' : 
                                                'linear-gradient(135deg, #ffffff, #f5f5f5)',
                                            border: `3px solid ${selectedCityIndex === index ? '#1565c0' : '#1976d2'}`,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            boxShadow: selectedCityIndex === index ? 
                                                '0 4px 20px rgba(25, 118, 210, 0.4)' : 
                                                '0 2px 8px rgba(0,0,0,0.2)',
                                            transition: 'all 0.3s ease',
                                            position: 'relative',
                                            zIndex: 1
                                        }}>
                                            <LocationOnIcon 
                                                sx={{ 
                                                    color: selectedCityIndex === index ? 'white' : '#1976d2',
                                                    fontSize: selectedCityIndex === index ? 22 : 18
                                                }} 
                                            />
                                        </Box>
                                        
                                        {/* City Label */}
                                        <Paper sx={{
                                            mt: 1,
                                            px: 1.5,
                                            py: 0.5,
                                            background: selectedCityIndex === index ? 
                                                'linear-gradient(135deg, #1976d2, #42a5f5)' : 
                                                'rgba(255, 255, 255, 0.95)',
                                            color: selectedCityIndex === index ? 'white' : 'text.primary',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                                            borderRadius: 2,
                                            minWidth: 90,
                                            textAlign: 'center',
                                            backdropFilter: 'blur(10px)',
                                            border: selectedCityIndex === index ? 'none' : '1px solid rgba(0,0,0,0.1)'
                                        }}>
                                            <Typography variant="caption" sx={{ 
                                                fontWeight: 600,
                                                fontSize: '0.7rem'
                                            }}>
                                                {city.name}
                                            </Typography>
                                            <Chip 
                                                label={`Day ${index + 1}`}
                                                size="small"
                                                sx={{
                                                    mt: 0.5,
                                                    backgroundColor: selectedCityIndex === index ? 'rgba(255,255,255,0.2)' : '#e3f2fd',
                                                    color: selectedCityIndex === index ? 'white' : '#1976d2',
                                                    fontSize: '0.6rem',
                                                    height: 18,
                                                    '& .MuiChip-label': {
                                                        px: 1
                                                    }
                                                }}
                                            />
                                        </Paper>
                                    </Box>
                                </Box>
                            );
                        })}

                        {/* Map Legend */}
                        <Box sx={{
                            position: 'absolute',
                            bottom: 16,
                            left: 16,
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            borderRadius: 2,
                            p: 1.5,
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(0,0,0,0.1)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1
                        }}>
                            <Box sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
                                border: '2px solid #1565c0'
                            }} />
                            <Typography variant="caption" color="text.secondary">
                                Click on markers to select a city
                            </Typography>
                        </Box>

                        {/* Scale Indicator */}
                        <Box sx={{
                            position: 'absolute',
                            bottom: 16,
                            right: 16,
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            borderRadius: 1,
                            p: 1,
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(0,0,0,0.1)'
                        }}>
                            <Typography variant="caption" color="text.secondary">
                                Scale: 1cm = 100km
                            </Typography>
                        </Box>
                    </>
                )}
            </Box>

            <style jsx>{`
                @keyframes pulse {
                    0% {
                        transform: translate(-50%, -50%) scale(1);
                        opacity: 0.8;
                    }
                    50% {
                        transform: translate(-50%, -50%) scale(1.2);
                        opacity: 0.4;
                    }
                    100% {
                        transform: translate(-50%, -50%) scale(1);
                        opacity: 0.8;
                    }
                }
            `}</style>
        </Box>
    );
};

export default MapView; 