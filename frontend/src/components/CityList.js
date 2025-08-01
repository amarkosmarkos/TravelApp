import React from 'react';
import { 
    Box, 
    List, 
    ListItem, 
    ListItemIcon, 
    Typography, 
    Paper,
    Chip,
    Divider
} from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';

const CityList = ({ cities = [], selectedCityIndex = 0, onCitySelect }) => {
    if (!cities || cities.length === 0) {
        return (
            <Box sx={{ 
                p: 3, 
                textAlign: 'center',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                flex: 1
            }}>
                <LocationOnIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                    No cities in itinerary
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Cities will appear here when the itinerary is generated
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            {/* Header */}
            <Box sx={{ 
                p: 2, 
                borderBottom: '1px solid',
                borderColor: 'divider',
                backgroundColor: 'background.paper',
                flexShrink: 0
            }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    City Itinerary
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {cities.length} {cities.length === 1 ? 'city' : 'cities'} in your trip
                </Typography>
            </Box>

            {/* Cities List */}
            <Box sx={{ 
                flex: 1, 
                overflow: 'auto',
                minHeight: 0
            }}>
                <List sx={{ p: 0 }}>
                    {cities.map((city, index) => (
                        <React.Fragment key={index}>
                            <ListItem 
                                onClick={() => onCitySelect && onCitySelect(city, index)}
                                selected={selectedCityIndex === index}
                                sx={{
                                    py: 2,
                                    px: 3,
                                    cursor: 'pointer',
                                    '&.Mui-selected': {
                                        backgroundColor: 'primary.light',
                                        '&:hover': {
                                            backgroundColor: 'primary.light',
                                        },
                                        '& .MuiListItemIcon-root': {
                                            color: 'primary.main',
                                        }
                                    },
                                    '&:hover': {
                                        backgroundColor: 'action.hover',
                                    },
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                <ListItemIcon sx={{ minWidth: 40 }}>
                                    <LocationOnIcon color={selectedCityIndex === index ? 'primary' : 'action'} />
                                </ListItemIcon>
                                
                                {/* Custom content instead of ListItemText */}
                                <Box sx={{ 
                                    flex: 1, 
                                    display: 'flex', 
                                    flexDirection: 'column',
                                    ml: 2
                                }}>
                                    {/* Primary content */}
                                    <Box sx={{ 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        gap: 1,
                                        mb: 0.5
                                    }}>
                                        <Typography 
                                            variant="body1" 
                                            sx={{ 
                                                fontWeight: selectedCityIndex === index ? 600 : 500 
                                            }}
                                        >
                                            {city.name}
                                        </Typography>
                                        <Chip 
                                            label={`Day ${index + 1}`}
                                            size="small"
                                            color={selectedCityIndex === index ? 'primary' : 'default'}
                                            variant={selectedCityIndex === index ? 'filled' : 'outlined'}
                                        />
                                    </Box>
                                    
                                    {/* Secondary content */}
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                        {city.coordinates && (
                                            <Typography variant="body2" color="text.secondary">
                                                {city.coordinates.latitude?.toFixed(4)}, {city.coordinates.longitude?.toFixed(4)}
                                            </Typography>
                                        )}
                                        {city.description && (
                                            <Typography variant="body2" color="text.secondary">
                                                {city.description}
                                            </Typography>
                                        )}
                                    </Box>
                                </Box>
                            </ListItem>
                            {index < cities.length - 1 && (
                                <Divider sx={{ mx: 3 }} />
                            )}
                        </React.Fragment>
                    ))}
                </List>
            </Box>

            {/* Footer */}
            <Box sx={{ 
                p: 2, 
                borderTop: '1px solid',
                borderColor: 'divider',
                backgroundColor: 'background.paper',
                flexShrink: 0
            }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CalendarTodayIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                        Duration: {cities.length} {cities.length === 1 ? 'day' : 'days'}
                    </Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default CityList; 