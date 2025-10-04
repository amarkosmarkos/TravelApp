import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, LinearProgress, Chip, Stack, Divider } from '@mui/material';

const methodLabels = {
  flight: 'Flight',
  train: 'Train',
  intercity_bus: 'Intercity bus',
  local_bus: 'Local bus',
  private_car: 'Private transfer',
  boat: 'Boat',
  unknown: 'Unknown'
};

export default function TransportSection({ travelId }) {
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        setLoading(true);
        setError(null);
        const token = localStorage.getItem('token');
        const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const res = await fetch(`${API_URL}/api/travels/${travelId}/transport-plan`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
          throw new Error('Error loading transport plan');
        }
        const data = await res.json();
        setPlan(data.transport_plan || null);
      } catch (e) {
        setError(e.message || 'Error');
      } finally {
        setLoading(false);
      }
    };
    if (travelId) fetchPlan();
  }, [travelId]);

  if (loading) {
    return (
      <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>Loading transport plan…</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!plan) {
    return (
      <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
        <Typography>No transport plan available.</Typography>
      </Box>
    );
  }

  const { segments = [], totals = {} } = plan;

  return (
    <Box sx={{ p: 2, height: '100%', overflow: 'auto', pb: 6 }}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>Summary</Typography>
        <Stack direction="row" spacing={2}>
          <Chip label={`Segments: ${totals.segments || 0}`} />
          <Chip label={`Total distance: ${(totals.total_distance_km || 0).toLocaleString()} km`} />
          <Chip label={`Total duration: ${totals.total_duration_h || 0} h`} />
          <Chip color="primary" label={`Budget: ${(totals.total_cost || 0).toLocaleString()} €`} />
        </Stack>
      </Paper>

      {segments.map((s, idx) => (
        <Paper key={idx} sx={{ p: 2, mb: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="subtitle1">{s.from} → {s.to}</Typography>
            <Chip label={methodLabels[s.method] || s.method} />
          </Stack>
          <Divider sx={{ my: 1 }} />
          <Stack direction="row" spacing={2}>
            <Chip label={`Distance: ${(s.distance_km || 0).toLocaleString()} km`} />
            <Chip label={`Duration: ${s.duration_h || 0} h`} />
            <Chip color="primary" label={`Cost: ${(s.estimated_cost || 0).toLocaleString()} €`} />
          </Stack>
        </Paper>
      ))}
    </Box>
  );
}


