import React, { useState } from 'react';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Typography, Paper } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import MapIcon from '@mui/icons-material/Map';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import PlaceIcon from '@mui/icons-material/Place';
import FlightIcon from '@mui/icons-material/Flight';
import ChatSection from './ChatSection';
import ItinerarySection from './ItinerarySection';

const MainCanvas = () => {
    const [selectedItem, setSelectedItem] = useState('chat');
    const [itineraryCities, setItineraryCities] = useState([]);

    const handleMenuClick = (item) => {
        setSelectedItem(item);
    };

    const handleTravelResponse = (response) => {
        if (response.cities && response.cities.length > 0) {
            setItineraryCities(response.cities);
        }
    };

    const menuItems = [
        { text: 'Chat', icon: <ChatIcon />, value: 'chat' },
        { text: 'Viajes', icon: <TravelExploreIcon />, value: 'travel' },
        { text: 'Itinerario', icon: <MapIcon />, value: 'itinerary' },
        { text: 'Visita', icon: <LocationOnIcon />, value: 'visit' },
        { text: 'Lugares', icon: <PlaceIcon />, value: 'places' },
        { text: 'Vuelos', icon: <FlightIcon />, value: 'flights' },
    ];

    return (
        <Box sx={{ display: 'flex', height: '100vh' }}>
            <Drawer
                variant="permanent"
                anchor="left"
                sx={{
                    width: 240,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: 240,
                        boxSizing: 'border-box',
                        backgroundColor: '#f5f5f5',
                        borderRight: '1px solid rgba(0, 0, 0, 0.12)'
                    },
                }}
            >
                <Box sx={{ p: 2 }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                        Travel Assistant
                    </Typography>
                </Box>
                <List>
                    {menuItems.map((item) => (
                        <ListItem 
                            button 
                            key={item.value}
                            onClick={() => handleMenuClick(item.value)}
                            selected={selectedItem === item.value}
                            sx={{
                                '&.Mui-selected': {
                                    backgroundColor: 'rgba(0, 0, 0, 0.08)',
                                    '&:hover': {
                                        backgroundColor: 'rgba(0, 0, 0, 0.12)',
                                    },
                                },
                            }}
                        >
                            <ListItemIcon>
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItem>
                    ))}
                </List>
            </Drawer>

            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    backgroundColor: '#f5f5f5',
                    minHeight: '100vh'
                }}
            >
                {selectedItem === 'chat' ? (
                    <ChatSection onTravelResponse={handleTravelResponse} />
                ) : selectedItem === 'itinerary' ? (
                    <ItinerarySection cities={itineraryCities} />
                ) : (
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h5">
                            {menuItems.find(item => item.value === selectedItem)?.text}
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 2 }}>
                            Contenido de {menuItems.find(item => item.value === selectedItem)?.text} en desarrollo...
                        </Typography>
                    </Paper>
                )}
            </Box>
        </Box>
    );
};

export default MainCanvas; 