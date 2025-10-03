import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Drawer, 
    List, 
    ListItem, 
    ListItemIcon, 
    ListItemText, 
    Typography, 
    Dialog, 
    ListItemButton,
    useTheme
} from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import MapIcon from '@mui/icons-material/Map';
import HotelIcon from '@mui/icons-material/Hotel';
import DirectionsTransitIcon from '@mui/icons-material/DirectionsTransit';
import ChatSection from './ChatSection';
import ItinerarySection from './ItinerarySection';
import TravelList from './TravelList';
import HotelsSection from './HotelsSection';
import TransportSection from './TransportSection';

const MainCanvas = () => {
    const [selectedItem, setSelectedItem] = useState('chat');
    const [itineraryCities, setItineraryCities] = useState([]);
    const [selectedTravel, setSelectedTravel] = useState(null);
    const [showTravelList, setShowTravelList] = useState(false);
    const theme = useTheme();

    // Load the first travel when the component mounts
    useEffect(() => {
        const loadFirstTravel = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) return;

                const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
                const response = await fetch(`${API_URL}/api/travels`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Error loading travels');
                }

                const travels = await response.json();
                console.log('Loaded travels:', travels);
                if (travels && travels.length > 0) {
                    console.log('Setting first travel:', travels[0]);
                    setSelectedTravel(travels[0]);
                } else {
                    console.log('No travels found');
                }
            } catch (error) {
                console.error('Error loading first travel:', error);
            }
        };

        loadFirstTravel();
    }, []);

    const handleMenuClick = (item) => {
        console.log('Menu item clicked:', item);
        setSelectedItem(item);
    };

    const handleTravelResponse = (response) => {
        if (response.cities && response.cities.length > 0) {
            setItineraryCities(response.cities);
        }
    };

    const handleSelectTravel = (travel) => {
        console.log('Travel selected:', travel);
        setSelectedTravel(travel);
        setShowTravelList(false);
    };

    const menuItems = [
        { text: 'Chat', icon: <ChatIcon />, value: 'chat' },
        { text: 'Itinerary', icon: <MapIcon />, value: 'itinerary' },
        { text: 'Hotels', icon: <HotelIcon />, value: 'hotels' },
        { text: 'Transports', icon: <DirectionsTransitIcon />, value: 'transport' },
    ];

    console.log('Current selectedTravel:', selectedTravel);
    console.log('Current selectedItem:', selectedItem);

    return (
        <Box sx={{
            display: 'flex',
            height: '100vh',
            overflow: 'hidden',
            background: `linear-gradient(135deg, 
                rgba(15, 139, 141, 0.05) 0%, 
                rgba(236, 154, 41, 0.03) 50%, 
                rgba(185, 163, 148, 0.02) 100%)`,
            position: 'relative'
        }}>
            {/* Background Pattern */}
            <Box sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundImage: 'url(../assets/images/background_lake_mountains.jpg)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                opacity: 0.1,
                zIndex: 0
            }} />

            {/* Sidebar */}
            <Drawer
                variant="permanent"
                anchor="left"
                sx={{
                    width: 300,
                    flexShrink: 0,
                    zIndex: 1,
                    '& .MuiDrawer-paper': {
                        width: 300,
                        boxSizing: 'border-box',
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                        borderRight: `1px solid ${theme.palette.divider}`,
                        marginTop: '64px',
                        height: 'calc(100vh - 64px)',
                        overflow: 'hidden',
                        boxShadow: '2px 0 20px rgba(0, 0, 0, 0.1)'
                    },
                }}
            >
                {/* Header Section */}
                <Box sx={{
                    p: 3,
                    background: `linear-gradient(135deg, 
                        ${theme.palette.primary.main} 0%, 
                        ${theme.palette.primary.dark} 100%)`,
                    color: 'white',
                    borderBottom: `1px solid ${theme.palette.divider}`
                }}>
                    <Typography variant="h6" sx={{ mb: 1, fontWeight: 700 }}>
                        Current Trip
                    </Typography>
                    <Typography 
                        variant="subtitle1" 
                        sx={{
                            cursor: 'pointer',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontWeight: 500,
                            '&:hover': {
                                color: 'white',
                                textDecoration: 'underline'
                            }
                        }}
                        onClick={() => setShowTravelList(true)}
                    >
                        {selectedTravel ? selectedTravel.title : 'Select a trip'}
                    </Typography>
                </Box>

                {/* Navigation Menu */}
                <List sx={{ overflow: 'auto', p: 2, flex: 1 }}>
                    {menuItems.map((item) => (
                        <ListItem key={item.value} disablePadding sx={{ mb: 1 }}>
                            <ListItemButton
                                onClick={() => handleMenuClick(item.value)}
                                selected={selectedItem === item.value}
                                sx={{
                                    borderRadius: 3,
                                    mx: 1,
                                    py: 2,
                                    '&.Mui-selected': {
                                        backgroundColor: theme.palette.primary.main,
                                        color: 'white',
                                        boxShadow: '0 4px 12px rgba(15, 139, 141, 0.3)',
                                        '&:hover': {
                                            backgroundColor: theme.palette.primary.dark,
                                        },
                                        '& .MuiListItemIcon-root': {
                                            color: 'white',
                                        }
                                    },
                                    '&:hover': {
                                        backgroundColor: 'rgba(15, 139, 141, 0.1)',
                                        transform: 'translateX(4px)',
                                        transition: 'all 0.3s ease'
                                    },
                                    transition: 'all 0.3s ease'
                                }}
                            >
                                <ListItemIcon sx={{
                                    color: selectedItem === item.value ? 
                                        'white' : theme.palette.text.secondary,
                                    minWidth: 40
                                }}>
                                    {item.icon}
                                </ListItemIcon>
                                <ListItemText 
                                    primary={item.text} 
                                    primaryTypographyProps={{
                                        fontWeight: selectedItem === item.value ? 700 : 500,
                                        fontSize: '1rem'
                                    }}
                                />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Drawer>

            {/* Main Content Area */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    position: 'relative',
                    zIndex: 1,
                    height: '100%',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column'
                }}
            >
                {/* Chat Section with custom styling */}
                <Box sx={{ 
                    display: selectedItem === 'chat' ? 'flex' : 'none',
                    flex: 1,
                    flexDirection: 'column',
                    minHeight: 0,
                    p: 3,
                    background: 'rgba(255, 255, 255, 0.8)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 3,
                    m: 2,
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                }}>
                    {selectedTravel ? (
                        <ChatSection onTravelResponse={handleTravelResponse} travelId={selectedTravel._id} />
                    ) : (
                        <Box sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            textAlign: 'center'
                        }}>
                            <Typography variant="h5" sx={{ mb: 2, color: theme.palette.text.secondary }}>
                                No Trip Selected
                            </Typography>
                            <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                                Please select a trip to start chatting with the travel assistant.
                            </Typography>
                        </Box>
                    )}
                </Box>

                {/* Itinerary Section */}
                {selectedItem === 'itinerary' && (
                    <Box sx={{
                        flex: 1,
                        p: 3,
                        background: 'rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(10px)',
                        borderRadius: 3,
                        m: 2,
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                    }}>
                        {selectedTravel ? (
                            <ItinerarySection cities={itineraryCities} travelId={selectedTravel._id} />
                        ) : (
                            <Box sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: '100%',
                                textAlign: 'center'
                            }}>
                                <Typography variant="h5" sx={{ mb: 2, color: theme.palette.text.secondary }}>
                                    No Trip Selected
                                </Typography>
                                <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                                    Please select a trip to view the itinerary.
                                </Typography>
                            </Box>
                        )}
                    </Box>
                )}

                {/* Other sections with modern design */}
                {selectedItem === 'hotels' && (
                    <Box sx={{
                        flex: 1,
                        p: 3,
                        background: 'rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(10px)',
                        borderRadius: 3,
                        m: 2,
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                    }}>
                        {selectedTravel ? (
                            <HotelsSection travelId={selectedTravel._id} />
                        ) : (
                            <Box sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: '100%',
                                textAlign: 'center'
                            }}>
                                <Typography variant="h5" sx={{ mb: 2, color: theme.palette.text.secondary }}>
                                    No Trip Selected
                                </Typography>
                                <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                                    Please select a trip to view hotel suggestions.
                                </Typography>
                            </Box>
                        )}
                    </Box>
                )}

                {selectedItem === 'transport' && (
                    <Box sx={{
                        flex: 1,
                        p: 3,
                        background: 'rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(10px)',
                        borderRadius: 3,
                        m: 2,
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                    }}>
                        {selectedTravel ? (
                            <TransportSection travelId={selectedTravel._id} />
                        ) : (
                            <Box sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: '100%',
                                textAlign: 'center'
                            }}>
                                <Typography variant="h5" sx={{ mb: 2, color: theme.palette.text.secondary }}>
                                    No Trip Selected
                                </Typography>
                                <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                                    Please select a trip to view transport plan.
                                </Typography>
                            </Box>
                        )}
                    </Box>
                )}

                {selectedItem !== 'chat' && selectedItem !== 'itinerary' && selectedItem !== 'hotels' && (
                    <Box sx={{
                        flex: 1,
                        p: 3,
                        background: 'rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(10px)',
                        borderRadius: 3,
                        m: 2,
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <Box sx={{ textAlign: 'center' }}>
                            <Box sx={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                width: 80,
                                height: 80,
                                borderRadius: '50%',
                                backgroundColor: theme.palette.primary.light,
                                color: theme.palette.primary.main,
                                mb: 3
                            }}>
                                {menuItems.find(item => item.value === selectedItem)?.icon}
                            </Box>
                            <Typography variant="h4" sx={{
                                mb: 2,
                                color: theme.palette.primary.main,
                                fontWeight: 700
                            }}>
                                {menuItems.find(item => item.value === selectedItem)?.text}
                            </Typography>
                            <Typography variant="body1" sx={{
                                color: theme.palette.text.secondary,
                                fontSize: '1.1rem',
                                maxWidth: 400
                            }}>
                                This feature is coming soon.
                            </Typography>
                        </Box>
                    </Box>
                )}
            </Box>

            {/* Travel List Dialog */}
            <Dialog
                open={showTravelList}
                onClose={() => setShowTravelList(false)}
                maxWidth="sm"
                fullWidth
                PaperProps={{
                    sx: {
                        borderRadius: 3,
                        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.2)',
                        overflow: 'hidden'
                    }
                }}
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