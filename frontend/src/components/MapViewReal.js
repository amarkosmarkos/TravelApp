import React, { useState, useEffect, useRef } from 'react';
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

// Leaflet imports
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom marker icon
const createCustomIcon = (isSelected) => {
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                width: ${isSelected ? '48px' : '40px'};
                height: ${isSelected ? '48px' : '40px'};
                border-radius: 50%;
                background: ${isSelected ? 'linear-gradient(135deg, #1976d2, #42a5f5)' : 'linear-gradient(135deg, #ffffff, #f5f5f5)'};
                border: 3px solid ${isSelected ? '#1565c0' : '#1976d2'};
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: ${isSelected ? '0 6px 25px rgba(25, 118, 210, 0.5)' : '0 4px 15px rgba(0,0,0,0.2)'};
                color: ${isSelected ? 'white' : '#1976d2'};
                font-size: ${isSelected ? '24px' : '20px'};
                transition: all 0.3s ease;
            ">
                📍
            </div>
        `,
        iconSize: [isSelected ? 48 : 40, isSelected ? 48 : 40],
        iconAnchor: [isSelected ? 24 : 20, isSelected ? 48 : 40],
        popupAnchor: [0, -48]
    });
};

// Map controls component
const MapControls = ({ onCenter, onZoomIn, onZoomOut, onFullscreen }) => {
    const map = useMap();

    const handleCenter = () => {
        map.setView(map.getCenter(), map.getZoom());
    };

    const handleZoomIn = () => {
        map.zoomIn();
    };

    const handleZoomOut = () => {
        map.zoomOut();
    };

    return (
        <Box sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            gap: 1
        }}>
            <Tooltip title="Center map">
                <IconButton 
                    size="small" 
                    onClick={handleCenter}
                    sx={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' }
                    }}
                >
                    <MyLocationIcon />
                </IconButton>
            </Tooltip>
            <Tooltip title="Zoom in">
                <IconButton 
                    size="small" 
                    onClick={handleZoomIn}
                    sx={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' }
                    }}
                >
                    <ZoomInIcon />
                </IconButton>
            </Tooltip>
            <Tooltip title="Zoom out">
                <IconButton 
                    size="small" 
                    onClick={handleZoomOut}
                    sx={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' }
                    }}
                >
                    <ZoomOutIcon />
                </IconButton>
            </Tooltip>
            <Tooltip title="Fullscreen">
                <IconButton 
                    size="small" 
                    onClick={onFullscreen}
                    sx={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' }
                    }}
                >
                    <FullscreenIcon />
                </IconButton>
            </Tooltip>
        </Box>
    );
};

// Map resize handler
const MapResizeHandler = () => {
    const map = useMap();
    
    useEffect(() => {
        const handleResize = () => {
            map.invalidateSize();
        };
        
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [map]);
    
    return null;
};

const MapViewReal = ({ cities = [], selectedCityIndex = 0, onCitySelect }) => {
    const [mapLoaded, setMapLoaded] = useState(false);
    const [loadingProgress, setLoadingProgress] = useState(0);
    const mapRef = useRef(null);

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

    // Calculate center point from cities
    const getMapCenter = () => {
        if (processedCities.length === 0) return [0, 0];
        
        const totalLat = processedCities.reduce((sum, city) => sum + city.coordinates.latitude, 0);
        const totalLng = processedCities.reduce((sum, city) => sum + city.coordinates.longitude, 0);
        
        return [totalLat / processedCities.length, totalLng / processedCities.length];
    };

    // Calculate zoom level based on city spread
    const getZoomLevel = () => {
        if (processedCities.length <= 1) return 12;
        
        const lats = processedCities.map(city => city.coordinates.latitude);
        const lngs = processedCities.map(city => city.coordinates.longitude);
        
        const latSpread = Math.max(...lats) - Math.min(...lats);
        const lngSpread = Math.max(...lngs) - Math.min(...lngs);
        const maxSpread = Math.max(latSpread, lngSpread);
        
        if (maxSpread > 10) return 6;
        if (maxSpread > 5) return 8;
        if (maxSpread > 1) return 10;
        return 12;
    };

    // Simulated map loading with progress
    useEffect(() => {
        const timer = setTimeout(() => {
            setMapLoaded(true);
        }, 800);

        const progressTimer = setInterval(() => {
            setLoadingProgress(prev => {
                if (prev >= 100) {
                    clearInterval(progressTimer);
                    return 100;
                }
                return prev + 10;
            });
        }, 80);

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

    const mapCenter = getMapCenter();
    const zoomLevel = getZoomLevel();

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
                alignItems: 'center',
                flexShrink: 0
            }}>
                <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                        Itinerary Map
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {processedCities.length} locations marked
                    </Typography>
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
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        borderRadius: 2,
                        p: 3,
                        minWidth: 200,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
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
                    <Box sx={{ 
                        height: '100%',
                        width: '100%',
                        position: 'relative'
                    }}>
                        <MapContainer 
                            center={mapCenter} 
                            zoom={zoomLevel} 
                            style={{ height: '100%', width: '100%' }}
                            zoomControl={false}
                            attributionControl={false}
                            ref={mapRef}
                            key={`map-${processedCities.length}`}
                        >
                            {/* Map resize handler */}
                            <MapResizeHandler />
                            
                            {/* OpenStreetMap tiles */}
                            <TileLayer
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                maxZoom={18}
                                minZoom={2}
                            />
                            
                            {/* City Markers */}
                            {processedCities.map((city, index) => (
                                <Marker 
                                    key={`marker-${index}-${selectedCityIndex === index}`}
                                    position={[city.coordinates.latitude, city.coordinates.longitude]}
                                    icon={createCustomIcon(selectedCityIndex === index)}
                                    eventHandlers={{
                                        click: () => onCitySelect && onCitySelect(city, index)
                                    }}
                                >
                                    <Popup>
                                        <Box sx={{ p: 1, minWidth: 200 }}>
                                            <Typography variant="h6" gutterBottom>
                                                {city.name}
                                            </Typography>
                                            <Chip 
                                                label={`Day ${index + 1}`}
                                                size="small"
                                                color="primary"
                                                sx={{ mb: 1 }}
                                            />
                                            {city.description && (
                                                <Typography variant="body2" color="text.secondary">
                                                    {city.description}
                                                </Typography>
                                            )}
                                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                                                {city.coordinates.latitude.toFixed(4)}, {city.coordinates.longitude.toFixed(4)}
                                            </Typography>
                                        </Box>
                                    </Popup>
                                </Marker>
                            ))}
                            
                            {/* Map Controls */}
                            <MapControls />
                        </MapContainer>
                    </Box>
                )}
            </Box>

            <style>{`
                .leaflet-container {
                    font-family: 'Roboto', sans-serif;
                }
                .leaflet-popup-content-wrapper {
                    border-radius: 8px;
                }
                .leaflet-popup-content {
                    margin: 0;
                    border-radius: 8px;
                }
                .custom-marker {
                    background: transparent;
                    border: none;
                }
                .leaflet-control-attribution {
                    display: none;
                }
            `}</style>
        </Box>
    );
};

export default MapViewReal; 