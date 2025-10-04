import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress, useTheme, Fade } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import SendIcon from '@mui/icons-material/Send';
import PsychologyIcon from '@mui/icons-material/Psychology';
import TravelSetup from './TravelSetup';

const ChatSection = ({ travelId }) => {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const isMock = (() => {
        try {
            const envFlag = (typeof process !== 'undefined' && process && process.env && process.env.REACT_APP_MOCK);
            const winFlag = (typeof window !== 'undefined' && window.REACT_APP_MOCK);
            return String(envFlag || winFlag || 'true').toLowerCase() === 'true';
        } catch (e) { return true; }
    })();
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [connected, setConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showTravelSetup, setShowTravelSetup] = useState(false);
    const [travelConfig, setTravelConfig] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const wsRef = useRef(null);
    const seenCorrelationIdsRef = useRef(new Set());
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

    // Initialize chat when mounting: load history and open WS
    useEffect(() => {
        if (travelId) {
            console.log('Initializing chat for travel:', travelId);
            loadChatHistory();
            connectWebSocket();
            // Force TravelSetup if no config saved locally for this travel
            const key = `travel-config-${travelId}`;
            const saved = localStorage.getItem(key);
            if (!saved) {
                if (isMock) {
                    const mockConfig = {
                        start_date: new Date().toISOString(),
                        total_days: 14,
                        country: 'thailand',
                        origin_city: '',
                        companions: 'solo',
                        preferences: {},
                        travel_id: travelId
                    };
                    try { localStorage.setItem(key, JSON.stringify(mockConfig)); } catch {}
                    setTravelConfig(mockConfig);
                    setShowTravelSetup(false);
                } else {
                    setShowTravelSetup(true);
                }
            } else {
                try {
                    setTravelConfig(JSON.parse(saved));
                } catch {}
            }
        }
    }, []); // Empty dependency array - only run once on mount

    // Effect to handle travel change
    useEffect(() => {
        if (travelId && travelId !== currentTravelIdRef.current) {
            console.log(`Changing travel: ${currentTravelIdRef.current} -> ${travelId}`);
            // Clear current messages
            setMessages([]);
            setLoading(true);
            // Reset correlation_id deduplication on travel change
            seenCorrelationIdsRef.current = new Set();
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
            // Derivar base WS de API_URL (http -> ws, https -> wss)
            let wsBase;
            try {
                const u = new URL(API_URL);
                wsBase = (u.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + u.host;
            } catch (e) {
                wsBase = API_URL.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
            }
            const ws = new WebSocket(`${wsBase}/api/travels/${travelId}/ws?token=${encodeURIComponent(token)}`);
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
                                const cid = message.correlation_id;
                                if (cid && seenCorrelationIdsRef.current.has(cid)) {
                                    return; // evitar duplicados
                                }
                                if (cid) {
                                    seenCorrelationIdsRef.current.add(cid);
                                }
                                const assistantMessage = {
                                    id: message.id,
                                    content: message.content,
                                    is_user: false,
                                    timestamp: message.timestamp || new Date().toISOString(),
                                    user_id: 'assistant',
                                    travel_id: travelId,
                                    correlation_id: cid
                                };
                                setMessages(prevMessages => [...prevMessages, assistantMessage]);
                                setIsProcessing(false); // Desactivar estado de procesamiento cuando llega respuesta
                            }
                            scrollToBottom();
                        } else {
                            console.warn('Received message for different travel:', message.travel_id);
                        }
                    } else if (data.type === 'error') {
                        console.error('Error from server:', data.data);
                        setError(data.data.message || 'Error processing message');
                        setIsProcessing(false); // Desactivar estado de procesamiento en caso de error
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
            const response = await fetch(`${API_URL}/api/travels/${travelId}/chat`, {
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
            setIsProcessing(true); // Activar estado de procesamiento

            const correlationId = (window.crypto && window.crypto.randomUUID) 
                ? window.crypto.randomUUID() 
                : `cid-${Date.now()}-${Math.random().toString(36).slice(2)}`;

            const message = {
                type: "message",
                data: {
                    message: newMessage,
                    is_user: true,
                    travel_id: travelId,
                    correlation_id: correlationId
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
            setIsProcessing(false); // Desactivar estado de procesamiento en caso de error
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
        // Persistir config
        try {
            localStorage.setItem(`travel-config-${config.travel_id}`, JSON.stringify(config));
        } catch {}
        // Send automatic greeting
        const greeting = `Welcome! I've registered your trip to ${config.country} for ${config.total_days} days (starting ${new Date(config.start_date).toLocaleDateString()}). I'm going to prepare a balanced route with variety of destinations. Any preferences (culture, nature, beach, pace)?`;
        setMessages(prev => [...prev, {
            id: `greet-${Date.now()}`,
            content: greeting,
            is_user: false,
            timestamp: new Date().toISOString(),
            user_id: 'assistant',
            travel_id: config.travel_id
        }]);
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

    // Show TravelSetup if no configuration
    if (showTravelSetup) {
        return (
            <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
                <TravelSetup 
                    onSetupComplete={handleTravelSetupComplete}
                    onCancel={handleTravelSetupCancel}
                    travelId={travelId}
                />
            </Box>
        );
    }

    return (
        <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            height: '100%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '& @keyframes pulse': {
                '0%': {
                    opacity: 1,
                    transform: 'scale(1)'
                },
                '50%': {
                    opacity: 0.7,
                    transform: 'scale(1.1)'
                },
                '100%': {
                    opacity: 1,
                    transform: 'scale(1)'
                }
            }
        }}>
            {/* Header with configuration button */}
            <Box sx={{ 
                p: 2, 
                background: 'rgba(255, 255, 255, 0.9)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" color="primary">
                        Travel Assistant
                    </Typography>
                    {!travelConfig && !isMock && (
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
                            {message.is_user ? (
                                <Typography 
                                    variant="body1" 
                                    sx={{ 
                                        lineHeight: 1.5,
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                    }}
                                >
                                    {message.content}
                                </Typography>
                            ) : (
                                <Box sx={{
                                    '& h1, & h2, & h3': { marginTop: 1, marginBottom: 1 },
                                    '& ul': { paddingLeft: 3, marginTop: 0, marginBottom: 1 },
                                    '& ol': { paddingLeft: 3, marginTop: 0, marginBottom: 1 },
                                    '& p': { marginTop: 1, marginBottom: 1 }
                                }}>
                                    <ReactMarkdown rehypePlugins={[rehypeRaw, rehypeSanitize]}>
                                        {message.content}
                                    </ReactMarkdown>
                                </Box>
                            )}
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
                
                {/* Loading spinner when processing */}
                {isProcessing && (
                    <Fade in={isProcessing} timeout={300}>
                        <Box
                            sx={{
                                display: 'flex',
                                justifyContent: 'flex-start',
                                mb: 2
                            }}
                        >
                            <Paper
                                elevation={2}
                                sx={{
                                    p: 2,
                                    maxWidth: '70%',
                                    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                                    borderRadius: 3,
                                    border: '1px solid rgba(255, 255, 255, 0.2)'
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <PsychologyIcon sx={{ 
                                        color: theme.palette.primary.main,
                                        animation: 'pulse 1.5s ease-in-out infinite'
                                    }} />
                                    <Box>
                                        <Typography variant="body2" sx={{ 
                                            color: theme.palette.text.secondary,
                                            fontStyle: 'italic'
                                        }}>
                                            The assistant is thinking...
                                        </Typography>
                                        <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                                            <CircularProgress size={16} thickness={4} />
                                            <Typography variant="caption" sx={{ 
                                                color: theme.palette.text.secondary,
                                                alignSelf: 'center',
                                                ml: 1
                                            }}>
                                                Generando respuesta
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>
                            </Paper>
                        </Box>
                    </Fade>
                )}
                
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
                    placeholder={isProcessing ? "The assistant is responding..." : "Type your message..."}
                    disabled={!connected || isProcessing}
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
                    disabled={!connected || !newMessage.trim() || isProcessing}
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