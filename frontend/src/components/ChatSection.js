import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress, useTheme } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import TravelSetup from './TravelSetup';

const ChatSection = ({ travelId }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [connected, setConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showTravelSetup, setShowTravelSetup] = useState(false);
    const [travelConfig, setTravelConfig] = useState(null);
    const wsRef = useRef(null);
    const messagesEndRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const currentTravelIdRef = useRef(travelId);
    const theme = useTheme();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Initialize chat when component mounts
    useEffect(() => {
        if (travelId) {
            console.log('Initializing chat for travel:', travelId);
            loadChatHistory();
            connectWebSocket();
        }
    }, []); // Empty dependency array - only run once on mount

    // Effect to handle travel change
    useEffect(() => {
        if (travelId && travelId !== currentTravelIdRef.current) {
            console.log(`Changing travel: ${currentTravelIdRef.current} -> ${travelId}`);
            // Clear current messages
            setMessages([]);
            setLoading(true);
            // Update current travel reference
            currentTravelIdRef.current = travelId;
            // Close existing WebSocket connection
            if (wsRef.current) {
                wsRef.current.close();
            }
            // Load messages for the new travel
            loadChatHistory();
            // Connect WebSocket for the new travel
            connectWebSocket();
        }
    }, [travelId]);

    const connectWebSocket = useCallback(() => {
        if (!travelId) {
            console.log('No travelId provided, skipping WebSocket connection');
            return;
        }

        const token = localStorage.getItem('token');
        if (!token) {
            setError('No authentication token found');
            return;
        }

        // Clear previous reconnection timeout
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        try {
            console.log('Attempting to connect WebSocket for travel:', travelId);
            const ws = new WebSocket(`ws://localhost:8000/api/travels/${travelId}/ws?token=${encodeURIComponent(token)}`);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log(`WebSocket connected for travel ${travelId}`);
                setConnected(true);
                setError(null);
                reconnectAttemptsRef.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Raw WebSocket message:', event.data);
                    console.log('Parsed WebSocket message:', data);

                    if (data.type === 'message') {
                        const message = data.data;
                        console.log('Message data:', message);
                        
                        // Verify that the message belongs to the current travel
                        if (message.travel_id === travelId) {
                            // Update user message with real backend ID
                            if (message.is_user) {
                                setMessages(prevMessages => {
                                    const updatedMessages = prevMessages.map(m => {
                                        if (m.id.startsWith('temp-') && m.content === message.content) {
                                            return { ...m, id: message.id };
                                        }
                                        return m;
                                    });
                                    return updatedMessages;
                                });
                            } else {
                                // Add assistant message
                                const assistantMessage = {
                                    id: message.id,
                                    content: message.content,
                                    is_user: false,
                                    timestamp: message.timestamp || new Date().toISOString(),
                                    user_id: 'assistant',
                                    travel_id: travelId
                                };
                                setMessages(prevMessages => [...prevMessages, assistantMessage]);
                            }
                            scrollToBottom();
                        } else {
                            console.warn('Received message for different travel:', message.travel_id);
                        }
                    } else if (data.type === 'error') {
                        console.error('Error from server:', data.data);
                        setError(data.data.message || 'Error processing message');
                    }
                } catch (error) {
                    console.error('Error handling WebSocket message:', error);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setError('Error connecting to chat server');
                setConnected(false);
            };

            ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code);
                setConnected(false);

                // Only try to reconnect if we're on the same travel
                if (travelId === currentTravelIdRef.current) {
                    const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
                    reconnectAttemptsRef.current += 1;

                    if (event.code === 4001) {
                        setError('Authentication required');
                    } else if (event.code === 4002) {
                        setError('Invalid authentication token');
                    } else if (event.code === 4004) {
                        setError('Not authorized to access this travel');
                    } else if (reconnectAttemptsRef.current < 5) {
                        reconnectTimeoutRef.current = setTimeout(() => {
                            connectWebSocket();
                        }, backoffTime);
                    } else {
                        setError('Failed to connect to chat server after multiple attempts');
                    }
                }
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            setError('Failed to create WebSocket connection');
            setConnected(false);
        }

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [travelId]);

    const loadChatHistory = async () => {
        if (!travelId) {
            console.log('No travelId provided, skipping chat history load');
            setLoading(false);
            return;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No authentication token found');
            }

            console.log('Loading chat history for travel:', travelId);
            const response = await fetch(`http://localhost:8000/api/travels/${travelId}/chat`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load chat history');
            }

            const data = await response.json();
            console.log(`Loaded ${data.length} messages for travel ${travelId}`);
            setMessages(data);
            setLoading(false);
        } catch (error) {
            console.error('Error in loadChatHistory:', error);
            setError(error.message);
            setLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!newMessage.trim() || !connected) return;

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No authentication token found');
            }

            // Create user message with ISO timestamp format
            const userMessage = {
                id: `temp-${Date.now()}`,
                content: newMessage,
                is_user: true,
                timestamp: new Date().toISOString(),
                user_id: localStorage.getItem('userId'),
                travel_id: travelId
            };

            // Add message to local state immediately
            setMessages(prevMessages => [...prevMessages, userMessage]);
            setNewMessage('');

            const message = {
                type: "message",
                data: {
                    message: newMessage,
                    is_user: true,
                    travel_id: travelId
                }
            };

            // Send message through WebSocket
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify(message));
            } else {
                throw new Error('WebSocket connection is not open');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setError(error.message);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const handleTravelSetupComplete = (config) => {
        setTravelConfig(config);
        setShowTravelSetup(false);
        // Aquí podrías iniciar el chat con la configuración
        console.log('Configuración de viaje completada:', config);
    };

    const handleTravelSetupCancel = () => {
        setShowTravelSetup(false);
    };

    const showSetupForm = () => {
        setShowTravelSetup(true);
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <CircularProgress />
            </Box>
        );
    }

    // Mostrar TravelSetup si no hay configuración
    if (showTravelSetup) {
        return (
            <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
                <TravelSetup 
                    onSetupComplete={handleTravelSetupComplete}
                    onCancel={handleTravelSetupCancel}
                />
            </Box>
        );
    }

    return (
        <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            height: '100%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}>
            {/* Header con botón de configuración */}
            <Box sx={{ 
                p: 2, 
                background: 'rgba(255, 255, 255, 0.9)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" color="primary">
                        Travel Assistant
                    </Typography>
                    {!travelConfig && (
                        <Button 
                            variant="outlined" 
                            onClick={showSetupForm}
                            size="small"
                        >
                            Configurar Viaje
                        </Button>
                    )}
                </Box>
            </Box>

            {/* Messages Area */}
            <Paper 
                elevation={0} 
                sx={{ 
                    flex: 1, 
                    p: 2, 
                    mb: 2, 
                    overflow: 'auto',
                    background: 'rgba(255, 255, 255, 0.6)',
                    borderRadius: 0,
                    '&::-webkit-scrollbar': {
                        width: '8px',
                    },
                    '&::-webkit-scrollbar-track': {
                        background: 'rgba(0, 0, 0, 0.1)',
                        borderRadius: '4px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                        background: theme.palette.primary.main,
                        borderRadius: '4px',
                    },
                    '&::-webkit-scrollbar-thumb:hover': {
                        background: theme.palette.primary.dark,
                    }
                }}
            >
                {error && (
                    <Typography color="error" sx={{ mb: 2, p: 2, background: 'rgba(244, 67, 54, 0.1)', borderRadius: 1 }}>
                        {error}
                    </Typography>
                )}
                
                {messages.map((message, index) => (
                    <Box
                        key={index}
                        sx={{
                            display: 'flex',
                            justifyContent: message.is_user ? 'flex-end' : 'flex-start',
                            mb: 2
                        }}
                    >
                        <Paper
                            elevation={2}
                            sx={{
                                p: 2,
                                maxWidth: '70%',
                                background: message.is_user 
                                    ? `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`
                                    : 'rgba(255, 255, 255, 0.9)',
                                color: message.is_user ? 'white' : theme.palette.text.primary,
                                borderRadius: 3,
                                backdropFilter: 'blur(10px)',
                                boxShadow: message.is_user 
                                    ? '0 4px 12px rgba(15, 139, 141, 0.3)'
                                    : '0 2px 8px rgba(0, 0, 0, 0.1)'
                            }}
                        >
                            <Typography variant="body1" sx={{ lineHeight: 1.5 }}>
                                {message.content}
                            </Typography>
                            <Typography variant="caption" sx={{ 
                                opacity: 0.7,
                                display: 'block',
                                mt: 1
                            }}>
                                {message.timestamp ? new Date(message.timestamp).toLocaleString('en-US', {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    day: '2-digit',
                                    month: '2-digit',
                                    year: 'numeric',
                                    hour12: false
                                }) : 'Just now'}
                            </Typography>
                        </Paper>
                    </Box>
                ))}
                <div ref={messagesEndRef} />
            </Paper>

            {/* Input Area */}
            <Box sx={{ 
                display: 'flex', 
                gap: 1,
                p: 2,
                background: 'rgba(255, 255, 255, 0.8)',
                borderRadius: '0 0 8px 8px'
            }}>
                <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    disabled={!connected}
                    sx={{ 
                        '& .MuiOutlinedInput-root': {
                            background: 'rgba(255, 255, 255, 0.9)',
                            borderRadius: 2
                        }
                    }}
                />
                <Button
                    variant="contained"
                    color="primary"
                    endIcon={<SendIcon />}
                    onClick={sendMessage}
                    disabled={!connected || !newMessage.trim()}
                    sx={{
                        backgroundColor: theme.palette.primary.main,
                        '&:hover': {
                            backgroundColor: theme.palette.primary.dark,
                        },
                        minWidth: 100
                    }}
                >
                    Send
                </Button>
            </Box>
        </Box>
    );
};

export default ChatSection; 