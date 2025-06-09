import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Button, Typography, Paper, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const ChatSection = ({ onTravelResponse, travelId }) => {
    const [message, setMessage] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [wsConnected, setWsConnected] = useState(false);
    const messagesEndRef = useRef(null);
    const wsRef = useRef(null);

    // Inicializar WebSocket
    useEffect(() => {
        if (!travelId) return;

        const ws = new WebSocket(`ws://localhost:8000/ws/${travelId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('WebSocket connected');
            setWsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    setChatHistory(prev => [...prev, {
                        role: 'assistant',
                        content: data.data.message
                    }]);
                }
            } catch (err) {
                console.error('Error processing WebSocket message:', err);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setError('Error de conexión con el servidor');
            setWsConnected(false);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setWsConnected(false);
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [travelId]);

    // Cargar mensajes del viaje cuando cambia el travelId
    useEffect(() => {
        const loadChatHistory = async () => {
            if (!travelId) {
                setChatHistory([]);
                return;
            }

            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    throw new Error('No se encontró el token de autenticación');
                }

                const response = await fetch(`http://localhost:8000/travels/${travelId}/messages`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Error al cargar los mensajes');
                }

                const messages = await response.json();
                setChatHistory(messages.map(msg => ({
                    role: msg.is_user ? 'user' : 'assistant',
                    content: msg.message
                })));
            } catch (err) {
                console.error('Error al cargar el historial:', err);
                setError(err.message);
            }
        };

        loadChatHistory();
    }, [travelId]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatHistory]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!message.trim() || !travelId) return;

        setIsLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No se encontró el token de autenticación');
            }

            // Guardar el mensaje del usuario
            const userMessageResponse = await fetch(`http://localhost:8000/travels/${travelId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message.trim(),
                    is_user: true,
                    travel_id: travelId
                })
            });

            if (!userMessageResponse.ok) {
                throw new Error('Error al guardar el mensaje');
            }

            // Agregar mensaje del usuario al historial
            setChatHistory(prev => [...prev, { role: 'user', content: message.trim() }]);

            // Enviar mensaje a través de WebSocket
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({
                    type: 'message',
                    message: message.trim(),
                    travel_id: travelId
                }));
            }

            setMessage('');
        } catch (err) {
            console.error('Error en el chat:', err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            gap: 2,
            minHeight: 0
        }}>
            <Paper 
                elevation={3} 
                sx={{ 
                    flex: 1,
                    p: 2,
                    overflow: 'hidden',
                    backgroundColor: '#f5f5f5',
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: 0,
                    maxHeight: 'calc(100vh - 200px)'
                }}
            >
                <Box sx={{ 
                    flex: 1, 
                    overflow: 'auto',
                    minHeight: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    mb: 2
                }}>
                    {!travelId && (
                        <Typography variant="body1" sx={{ textAlign: 'center', color: 'text.secondary', my: 2 }}>
                            Selecciona un viaje para comenzar a chatear
                        </Typography>
                    )}
                    {!wsConnected && travelId && (
                        <Typography variant="body2" color="error" sx={{ textAlign: 'center', my: 1 }}>
                            Reconectando al servidor...
                        </Typography>
                    )}
                    {chatHistory.map((msg, index) => (
                        <Box
                            key={index}
                            sx={{
                                display: 'flex',
                                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                mb: 2
                            }}
                        >
                            <Paper
                                elevation={1}
                                sx={{
                                    p: 2,
                                    maxWidth: '70%',
                                    backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#ffffff'
                                }}
                            >
                                <Typography variant="body1">
                                    {msg.content}
                                </Typography>
                            </Paper>
                        </Box>
                    ))}
                    {error && (
                        <Typography color="error" sx={{ mt: 2 }}>
                            {error}
                        </Typography>
                    )}
                    <div ref={messagesEndRef} />
                </Box>
                
                <Box 
                    component="form" 
                    onSubmit={handleSubmit}
                    sx={{ 
                        display: 'flex',
                        position: 'relative',
                        backgroundColor: '#ffffff',
                        borderRadius: 1,
                        border: '1px solid rgba(0, 0, 0, 0.12)',
                        '&:hover': {
                            border: '1px solid rgba(0, 0, 0, 0.24)'
                        }
                    }}
                >
                    <TextField
                        fullWidth
                        variant="standard"
                        placeholder={travelId ? "Escribe tu mensaje..." : "Selecciona un viaje para chatear"}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        disabled={isLoading || !travelId || !wsConnected}
                        sx={{ 
                            backgroundColor: '#ffffff',
                            '& .MuiInputBase-root': {
                                padding: '8px 12px'
                            },
                            '& .MuiInputBase-input': {
                                paddingRight: '48px'
                            }
                        }}
                    />
                    <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        disabled={isLoading || !message.trim() || !travelId || !wsConnected}
                        sx={{ 
                            position: 'absolute',
                            right: 4,
                            top: '50%',
                            transform: 'translateY(-50%)',
                            minWidth: '40px',
                            width: '40px',
                            height: '40px',
                            borderRadius: '50%',
                            p: 0
                        }}
                    >
                        {isLoading ? (
                            <CircularProgress size={24} color="inherit" />
                        ) : (
                            <SendIcon />
                        )}
                    </Button>
                </Box>
            </Paper>
        </Box>
    );
};

export default ChatSection; 