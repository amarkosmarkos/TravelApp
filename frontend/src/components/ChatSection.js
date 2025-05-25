import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Button, Typography, Paper, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const ChatSection = ({ onTravelResponse }) => {
    const [message, setMessage] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const messagesEndRef = useRef(null);

    // Verificar el token al montar el componente
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            setError('No se encontró el token de autenticación. Por favor, inicia sesión nuevamente.');
        }
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatHistory]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!message.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No se encontró el token de autenticación. Por favor, inicia sesión nuevamente.');
            }

            // Asegurarnos de que el historial tenga el formato correcto
            const formattedHistory = chatHistory.map(msg => ({
                role: msg.role || 'user',
                content: msg.content || msg.text || ''
            }));

            const requestData = {
                message: message.trim(),
                history: formattedHistory
            };

            console.log('Token:', token);
            console.log('Enviando datos al servidor:', JSON.stringify(requestData, null, 2));

            // Primero intentamos el endpoint de travel
            const travelResponse = await fetch('http://localhost:8000/api/travel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: message.trim() })
            });

            if (travelResponse.ok) {
                const travelData = await travelResponse.json();
                console.log('Respuesta del endpoint travel:', travelData);
                
                // Si hay una respuesta del travel endpoint, la pasamos al componente padre
                if (onTravelResponse) {
                    onTravelResponse(travelData);
                }

                // Actualizamos el historial con la respuesta del travel
                setChatHistory(prev => [...prev, 
                    { role: 'user', content: message.trim() },
                    { role: 'assistant', content: travelData.user_message }
                ]);
            } else {
                // Si el endpoint de travel falla, intentamos el endpoint de chat normal
                const chatResponse = await fetch('http://localhost:8000/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(requestData)
                });

                const chatData = await chatResponse.json();
                console.log('Respuesta completa del servidor:', chatData);

                if (!chatResponse.ok) {
                    throw new Error(chatData.detail || 'Error al enviar el mensaje');
                }

                if (!chatData.history || !Array.isArray(chatData.history)) {
                    throw new Error('Formato de respuesta inválido del servidor');
                }

                setChatHistory(chatData.history);
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
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Paper 
                elevation={3} 
                sx={{ 
                    flex: 1, 
                    mb: 2, 
                    p: 2, 
                    overflow: 'auto',
                    backgroundColor: '#f5f5f5'
                }}
            >
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
                                {msg.content || msg.text}
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
            </Paper>
            <Box 
                component="form" 
                onSubmit={handleSubmit}
                sx={{ 
                    display: 'flex', 
                    gap: 1,
                    backgroundColor: '#ffffff',
                    p: 2,
                    borderRadius: 1
                }}
            >
                <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Escribe tu mensaje..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    disabled={isLoading}
                    sx={{ backgroundColor: '#ffffff' }}
                />
                <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={isLoading || !message.trim()}
                    sx={{ minWidth: '100px' }}
                >
                    {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
                </Button>
            </Box>
        </Box>
    );
};

export default ChatSection; 