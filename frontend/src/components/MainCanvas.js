import React, { useState, useEffect } from 'react';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Typography, Paper, Dialog, ListItemButton } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import MapIcon from '@mui/icons-material/Map';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import PlaceIcon from '@mui/icons-material/Place';
import FlightIcon from '@mui/icons-material/Flight';
import ChatSection from './ChatSection';
import ItinerarySection from './ItinerarySection';
import TravelList from './TravelList';

const MainCanvas = () => {
    const [selectedItem, setSelectedItem] = useState('chat');
    const [itineraryCities, setItineraryCities] = useState([]);
    const [selectedTravel, setSelectedTravel] = useState(null);
    const [showTravelList, setShowTravelList] = useState(false);

    // Cargar el primer viaje al montar el componente
    useEffect(() => {
        const loadFirstTravel = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) return;

                const response = await fetch('http://localhost:8000/api/travels', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Error al cargar los viajes');
                }

                const travels = await response.json();
                if (travels && travels.length > 0) {
                    setSelectedTravel(travels[0]);
                }
            } catch (error) {
                console.error('Error al cargar el primer viaje:', error);
            }
        };

        loadFirstTravel();
    }, []);

    const handleMenuClick = (item) => {
        setSelectedItem(item);
    };

    const handleTravelResponse = (response) => {
        if (response.cities && response.cities.length > 0) {
            setItineraryCities(response.cities);
        }
    };

    const handleSelectTravel = (travel) => {
        setSelectedTravel(travel);
        setShowTravelList(false);
    };

    const menuItems = [
        { text: 'Chat', icon: <ChatIcon />, value: 'chat' },
        { text: 'Itinerario', icon: <MapIcon />, value: 'itinerary' },
        { text: 'Visita', icon: <LocationOnIcon />, value: 'visit' },
        { text: 'Lugares', icon: <PlaceIcon />, value: 'places' },
        { text: 'Vuelos', icon: <FlightIcon />, value: 'flights' },
    ];

    return (
        <Box sx={{ 
            display: 'flex', 
            height: '100%',
            overflow: 'hidden'
        }}>
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
                        borderRight: '1px solid rgba(0, 0, 0, 0.12)',
                        marginTop: '64px',
                        height: 'calc(100vh - 64px)',
                        overflow: 'hidden'
                    },
                }}
            >
                <Box sx={{ p: 2 }}>
                    <Typography variant="h6" sx={{ mb: 1 }}>
                        Viaje
                    </Typography>
                    <Typography 
                        variant="subtitle1" 
                        sx={{ 
                            cursor: 'pointer',
                            color: 'primary.main',
                            '&:hover': { textDecoration: 'underline' }
                        }}
                        onClick={() => setShowTravelList(true)}
                    >
                        {selectedTravel ? selectedTravel.title : 'Viaje por determinar'}
                    </Typography>
                </Box>
                <List sx={{ overflow: 'auto' }}>
                    {menuItems.map((item) => (
                        <ListItem key={item.value} disablePadding>
                            <ListItemButton
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
                            </ListItemButton>
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
                    height: '100%',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column'
                }}
            >
                {/* ChatSection siempre montado pero oculto cuando no está activo */}
                <Box sx={{ 
                    display: selectedItem === 'chat' ? 'flex' : 'none',
                    flex: 1,
                    flexDirection: 'column',
                    minHeight: 0
                }}>
                    <ChatSection onTravelResponse={handleTravelResponse} travelId={selectedTravel?._id} />
                </Box>

                {/* Otros componentes */}
                {selectedItem === 'itinerary' && (
                    <ItinerarySection cities={itineraryCities} travelId={selectedTravel?._id} />
                )}
                {selectedItem !== 'chat' && selectedItem !== 'itinerary' && (
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

            <Dialog
                open={showTravelList}
                onClose={() => setShowTravelList(false)}
                maxWidth="sm"
                fullWidth
            >
                <TravelList 
                    onSelectTravel={handleSelectTravel}
                    selectedTravel={selectedTravel}
                />
            </Dialog>
        </Box>
    );
};

export default MainCanvas; 