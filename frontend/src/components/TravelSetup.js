import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  Grid,
  Alert,
  Snackbar
} from '@mui/material';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TravelSetup = ({ onSetupComplete, onCancel }) => {
  const [formData, setFormData] = useState({
    start_date: '',
    total_days: 7,
    country: 'thailand',
    origin_city: '',
    companions: 'solo',
    preferences: {}
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      // Validar datos
      if (!formData.start_date || !formData.country) {
        setError('Por favor completa todos los campos obligatorios');
        return;
      }

      // Convertir fecha a ISO
      const startDate = new Date(formData.start_date);

      // El backend espera TravelCreate: { title, destination, start_date?, ... }
      const travelPayload = {
        title: `Viaje a ${formData.country}`,
        destination: formData.country,
        start_date: startDate.toISOString()
      };

      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/travels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(travelPayload)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Error al crear el viaje');
      }

      const result = await response.json();
      const travelId = result._id || result.id;
      if (!travelId) {
        throw new Error('No se pudo obtener el ID del viaje');
      }

      setShowSuccess(true);

      // Devolver al padre los datos de setup y el ID creado
      onSetupComplete({
        start_date: travelPayload.start_date,
        total_days: formData.total_days,
        country: formData.country,
        origin_city: formData.origin_city,
        companions: formData.companions,
        preferences: formData.preferences,
        travel_id: travelId
      });
    } catch (error) {
      console.error('Error en setup:', error);
      setError(error.message || 'No se pudo guardar la configuración del viaje');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
      <Paper 
        elevation={3} 
        sx={{ 
          maxWidth: 600, 
          mx: 'auto', 
          p: 4,
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom align="center" color="primary">
          Configura tu Viaje
        </Typography>
        
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Cuéntanos sobre tu próximo viaje para crear un itinerario perfecto
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Fecha de inicio"
              type="date"
              value={formData.start_date}
              onChange={(e) => handleInputChange('start_date', e.target.value)}
              InputLabelProps={{
                shrink: true,
              }}
              inputProps={{
                min: new Date().toISOString().split('T')[0]
              }}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Duración del viaje (días)"
              type="number"
              value={formData.total_days}
              onChange={(e) => handleInputChange('total_days', parseInt(e.target.value))}
              inputProps={{ min: 1, max: 30 }}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth required>
              <InputLabel>País de destino</InputLabel>
              <Select
                value={formData.country}
                onChange={(e) => handleInputChange('country', e.target.value)}
                label="País de destino"
              >
                <MenuItem value="thailand">Tailandia</MenuItem>
                <MenuItem value="japan">Japón</MenuItem>
                <MenuItem value="spain">España</MenuItem>
                <MenuItem value="france">Francia</MenuItem>
                <MenuItem value="italy">Italia</MenuItem>
                <MenuItem value="germany">Alemania</MenuItem>
                <MenuItem value="uk">Reino Unido</MenuItem>
                <MenuItem value="usa">Estados Unidos</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Ciudad de origen"
              placeholder="Madrid, Barcelona, etc."
              value={formData.origin_city}
              onChange={(e) => handleInputChange('origin_city', e.target.value)}
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Tipo de viaje</InputLabel>
              <Select
                value={formData.companions}
                onChange={(e) => handleInputChange('companions', e.target.value)}
                label="Tipo de viaje"
              >
                <MenuItem value="solo">Solo</MenuItem>
                <MenuItem value="pareja">Pareja</MenuItem>
                <MenuItem value="familia">Familia</MenuItem>
                <MenuItem value="amigos">Amigos</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={isLoading}
                size="large"
                sx={{ px: 4 }}
              >
                {isLoading ? 'Guardando...' : 'Configurar Viaje'}
              </Button>
              
              <Button
                variant="outlined"
                onClick={onCancel}
                size="large"
                sx={{ px: 4 }}
              >
                Cancelar
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={() => setError('')}
      >
        <Alert severity="error" onClose={() => setError('')}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar 
        open={showSuccess} 
        autoHideDuration={3000} 
        onClose={() => setShowSuccess(false)}
      >
        <Alert severity="success" onClose={() => setShowSuccess(false)}>
          Configuración guardada exitosamente
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default TravelSetup; 