import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const ChatSection = ({ travelId }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [connected, setConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const wsRef = useRef(null);
    const messagesEndRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const currentTravelIdRef = useRef(travelId);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Efecto para manejar el cambio de viaje
    useEffect(() => {
        if (travelId !== currentTravelIdRef.current) {
            console.log(`Cambiando de viaje: ${currentTravelIdRef.current} -> ${travelId}`);
            // Limpiar mensajes actuales
            setMessages([]);
            setLoading(true);
            // Actualizar la referencia del viaje actual
            currentTravelIdRef.current = travelId;
            // Cerrar conexión WebSocket existente
            if (wsRef.current) {
                wsRef.current.close();
            }
            // Cargar mensajes del nuevo viaje
            loadChatHistory();
            // Conectar WebSocket para el nuevo viaje
            connectWebSocket();
        }
    }, [travelId]);

    const connectWebSocket = useCallback(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            setError('No authentication token found');
            return;
        }

        // Limpiar timeout de reconexión anterior
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        try {
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
                        
                        // Verificar que el mensaje pertenece al viaje actual
                        if (message.travel_id === travelId) {
                            // Actualizar el mensaje del usuario con el ID real del backend
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
                                // Agregar mensaje del asistente
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

                // Solo intentar reconectar si estamos en el mismo viaje
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
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No authentication token found');
            }

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

            // Crear el mensaje del usuario con timestamp en formato ISO
            const userMessage = {
                id: `temp-${Date.now()}`,
                content: newMessage,
                is_user: true,
                timestamp: new Date().toISOString(),
                user_id: localStorage.getItem('userId'),
                travel_id: travelId
            };

            // Agregar el mensaje al estado local inmediatamente
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

            // Enviar mensaje a través de WebSocket
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

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Paper 
                elevation={3} 
                sx={{ 
                    flex: 1, 
                    p: 2, 
                    mb: 2, 
                    overflow: 'auto',
                    backgroundColor: '#f5f5f5'
                }}
            >
                {error && (
                    <Typography color="error" sx={{ mb: 2 }}>
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
                            elevation={1}
                            sx={{
                                p: 2,
                                maxWidth: '70%',
                                backgroundColor: message.is_user ? '#e3f2fd' : '#ffffff'
                            }}
                        >
                            <Typography variant="body1">
                                {message.content}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                {message.timestamp ? new Date(message.timestamp).toLocaleString('es-ES', {
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

            <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    disabled={!connected}
                    sx={{ backgroundColor: '#ffffff' }}
                />
                <Button
                    variant="contained"
                    color="primary"
                    endIcon={<SendIcon />}
                    onClick={sendMessage}
                    disabled={!connected || !newMessage.trim()}
                >
                    Send
                </Button>
            </Box>
        </Box>
    );
};

export default ChatSection; 