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

const TravelSetup = ({ onSetupComplete, onCancel, travelId: existingTravelId = null }) => {
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
      // Validate data
      if (!formData.start_date || !formData.country) {
        setError('Please complete all required fields');
        return;
      }

      // Convert date to ISO
      const startDate = new Date(formData.start_date);

      // Backend expects TravelCreate: { title, destination, start_date?, ... }
      const travelPayload = {
        title: `Trip to ${formData.country}`,
        destination: formData.country,
        start_date: startDate.toISOString(),
        total_days: formData.total_days
      };

      const token = localStorage.getItem('token');
      let response, travelId
      if (existingTravelId) {
        // Update existing trip with initial configuration
        response = await fetch(`${API_URL}/api/travels/${existingTravelId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(travelPayload)
        });
      } else {
        // Create new trip
        response = await fetch(`${API_URL}/api/travels`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(travelPayload)
        });
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Error creating the trip');
      }

      const result = await response.json();
      travelId = existingTravelId || result._id || result.id;
      if (!travelId) {
        throw new Error('Could not get trip ID');
      }

      setShowSuccess(true);

      // Return setup data and created ID to parent
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
      console.error('Error in setup:', error);
      setError(error.message || 'Could not save trip configuration');
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
          Configure Your Trip
        </Typography>
        
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Tell us about your next trip to create a perfect itinerary
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Start Date"
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
              label="Trip Duration (days)"
              type="number"
              value={formData.total_days}
              onChange={(e) => handleInputChange('total_days', parseInt(e.target.value))}
              inputProps={{ min: 1, max: 30 }}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth required>
              <InputLabel>Destination Country</InputLabel>
              <Select
                value={formData.country}
                onChange={(e) => handleInputChange('country', e.target.value)}
                label="Destination Country"
              >
                <MenuItem value="thailand">Thailand</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Origin City"
              placeholder="Madrid, Barcelona, etc."
              value={formData.origin_city}
              onChange={(e) => handleInputChange('origin_city', e.target.value)}
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Trip Type</InputLabel>
              <Select
                value={formData.companions}
                onChange={(e) => handleInputChange('companions', e.target.value)}
                label="Trip Type"
              >
                <MenuItem value="solo">Solo</MenuItem>
                <MenuItem value="pareja">Couple</MenuItem>
                <MenuItem value="familia">Family</MenuItem>
                <MenuItem value="amigos">Friends</MenuItem>
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
                {isLoading ? 'Saving...' : 'Configure Trip'}
              </Button>
              
              <Button
                variant="outlined"
                onClick={onCancel}
                size="large"
                sx={{ px: 4 }}
              >
                Cancel
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
          Configuration saved successfully
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default TravelSetup; 