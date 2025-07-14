import React, { useState, useEffect } from 'react';
import {
    Box,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    Typography,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    IconButton,
    Divider,
    Paper
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';

const TravelList = ({ onSelectTravel, selectedTravel }) => {
    const [travels, setTravels] = useState([]);
    const [openDialog, setOpenDialog] = useState(false);
    const [newTravelName, setNewTravelName] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const fetchTravels = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) return;

                const response = await fetch('http://localhost:8000/api/travels/', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    setTravels(data);
                }
            } catch (error) {
                console.error('Error fetching travels:', error);
            }
        };

        fetchTravels();
    }, []);

    const handleCreateTravel = async () => {
        if (!newTravelName.trim()) return;

        setIsLoading(true);
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.error('No token found in localStorage');
                throw new Error('No token found');
            }

            console.log('Sending request with token:', token);

            const response = await fetch('http://localhost:8000/api/travels/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    title: newTravelName.trim(),
                    destination: "To be determined", // Default value, can be updated later
                    status: "planned"
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Server response:', response.status, errorData);
                throw new Error(errorData.detail || 'Failed to create travel');
            }

            const newTravel = await response.json();
            console.log('Travel created successfully:', newTravel);
            setTravels(prev => [...prev, newTravel]);
            onSelectTravel(newTravel);
            setOpenDialog(false);
            setNewTravelName('');
        } catch (error) {
            console.error('Error creating travel:', error);
            // Here you could show an error message to the user
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ width: '100%', maxWidth: 360, bgcolor: 'background.paper' }}>
            <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" component="h2">My Trips</Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenDialog(true)}
                    sx={{
                        backgroundColor: 'primary.main',
                        '&:hover': {
                            backgroundColor: 'primary.dark',
                        }
                    }}
                >
                    New Trip
                </Button>
            </Box>
            <Divider />
            <List sx={{ p: 0 }}>
                {travels.length === 0 ? (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                            You don't have any trips created
                        </Typography>
                    </Box>
                ) : (
                    travels.map((travel) => (
                        <ListItem key={travel._id} disablePadding>
                            <ListItemButton
                                selected={selectedTravel?._id === travel._id}
                                onClick={() => onSelectTravel(travel)}
                                sx={{
                                    '&.Mui-selected': {
                                        backgroundColor: 'primary.light',
                                        '&:hover': {
                                            backgroundColor: 'primary.light',
                                        },
                                    },
                                }}
                            >
                                <ListItemText
                                    primary={travel.title || 'Untitled'}
                                    primaryTypographyProps={{
                                        fontWeight: selectedTravel?._id === travel._id ? 'bold' : 'normal',
                                        fontSize: '1rem'
                                    }}
                                />
                            </ListItemButton>
                        </ListItem>
                    ))
                )}
            </List>

            <Dialog 
                open={openDialog} 
                onClose={() => setOpenDialog(false)}
                maxWidth="sm"
                fullWidth
                PaperProps={{
                    sx: {
                        borderRadius: 2,
                        boxShadow: 3
                    }
                }}
            >
                <DialogTitle sx={{ 
                    m: 0, 
                    p: 2, 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    backgroundColor: 'primary.main',
                    color: 'white'
                }}>
                    <Typography variant="h6">Create New Trip</Typography>
                    <IconButton
                        aria-label="close"
                        onClick={() => setOpenDialog(false)}
                        sx={{
                            color: 'white',
                            '&:hover': {
                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                            },
                        }}
                    >
                        <CloseIcon />
                    </IconButton>
                </DialogTitle>
                <DialogContent sx={{ p: 3 }}>
                    <Paper elevation={0} sx={{ p: 2, backgroundColor: 'background.default' }}>
                        <TextField
                            autoFocus
                            margin="dense"
                            label="Trip Name"
                            fullWidth
                            value={newTravelName}
                            onChange={(e) => setNewTravelName(e.target.value)}
                            variant="outlined"
                            placeholder="Ex: Trip to Paris"
                        />
                    </Paper>
                </DialogContent>
                <DialogActions sx={{ p: 2, backgroundColor: 'background.default' }}>
                    <Button 
                        onClick={() => setOpenDialog(false)}
                        sx={{ mr: 1 }}
                    >
                        Cancel
                    </Button>
                    <Button 
                        onClick={handleCreateTravel} 
                        variant="contained"
                        disabled={!newTravelName.trim() || isLoading}
                        sx={{
                            backgroundColor: 'primary.main',
                            '&:hover': {
                                backgroundColor: 'primary.dark',
                            }
                        }}
                    >
                        {isLoading ? 'Creating...' : 'Create Trip'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default TravelList; 