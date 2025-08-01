import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Typography, 
    Paper,
    IconButton,
    Tooltip,
    Chip
} from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import MapIcon from '@mui/icons-material/Map';

const MapViewSimple = ({ cities = [], selectedCityIndex = 0, onCitySelect }) => {
    const [mapLoaded, setMapLoaded] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setMapLoaded(true);
        }, 1000);

        return () => clearTimeout(timer);
    }, []);

    // Calculate optimal positions for city markers
    const calculateMarkerPositions = (cityCount) => {
        if (cityCount === 0) return [];
        
        const positions = [];
        const padding = 20; // Increased padding from edges
        const availableWidth = 100 - (padding * 2);
        const availableHeight = 100 - (padding * 2);
        
        if (cityCount === 1) {
            // Single city in center
            positions.push({ x: 50, y: 50 });
        } else if (cityCount === 2) {
            // Two cities side by side
            positions.push({ x: 30, y: 50 });
            positions.push({ x: 70, y: 50 });
        } else if (cityCount === 3) {
            // Triangle formation
            positions.push({ x: 50, y: 30 });
            positions.push({ x: 25, y: 70 });
            positions.push({ x: 75, y: 70 });
        } else if (cityCount === 4) {
            // Square formation
            positions.push({ x: 30, y: 30 });
            positions.push({ x: 70, y: 30 });
            positions.push({ x: 30, y: 70 });
            positions.push({ x: 70, y: 70 });
        } else {
            // For 5+ cities, use a grid-like distribution
            const cols = Math.ceil(Math.sqrt(cityCount));
            const rows = Math.ceil(cityCount / cols);
            
            for (let i = 0; i < cityCount; i++) {
                const row = Math.floor(i / cols);
                const col = i % cols;
                
                const x = padding + (col * availableWidth / Math.max(cols - 1, 1));
                const y = padding + (row * availableHeight / Math.max(rows - 1, 1));
                
                positions.push({ x, y });
            }
        }
        
        return positions;
    };

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
    const citiesWithCoordinates = cities.filter(city => 
        city.coordinates && 
        city.coordinates.latitude && 
        city.coordinates.longitude
    );

    if (citiesWithCoordinates.length === 0) {
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

    // Calculate positions for all cities
    const markerPositions = calculateMarkerPositions(citiesWithCoordinates.length);

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
                        {citiesWithCoordinates.length} locations marked
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
                backgroundColor: '#f5f5f5',
                overflow: 'hidden'
            }}>
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
                        <Typography variant="body2" color="text.secondary">
                            Loading map...
                        </Typography>
                    </Box>
                ) : (
                    <Box sx={{ 
                        height: '100%',
                        width: '100%',
                        position: 'relative',
                        background: `
                            linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 50%, #e8f5e8 100%),
                            radial-gradient(circle at 20% 80%, #81c784 0%, transparent 50%),
                            radial-gradient(circle at 80% 20%, #64b5f6 0%, transparent 50%),
                            radial-gradient(circle at 40% 40%, #ffb74d 0%, transparent 50%)
                        `,
                        backgroundSize: '100% 100%, 200px 200px, 150px 150px, 100px 100px',
                        backgroundPosition: '0 0, 0 0, 0 0, 0 0',
                        backgroundRepeat: 'no-repeat, no-repeat, no-repeat, no-repeat'
                    }}>
                        {/* Grid Pattern */}
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

                        {/* City Markers */}
                        {citiesWithCoordinates.map((city, index) => {
                            const position = markerPositions[index];
                            
                            return (
                                <Box
                                    key={index}
                                    sx={{
                                        position: 'absolute',
                                        left: `${position.x}%`,
                                        top: `${position.y}%`,
                                        transform: 'translate(-50%, -50%)',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease',
                                        zIndex: selectedCityIndex === index ? 2 : 1
                                    }}
                                    onClick={() => onCitySelect && onCitySelect(city, index)}
                                >
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
                                            border: selectedCityIndex === index ? 'none' : '1px solid rgba(0,0,0,0.1)',
                                            whiteSpace: 'nowrap'
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

                        {/* Map Info */}
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
                    </Box>
                )}
            </Box>

            <style>{`
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

export default MapViewSimple; 