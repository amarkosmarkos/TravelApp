import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardMedia, CardContent, Button, Chip, Tabs, Tab } from '@mui/material';

const HotelsSection = ({ travelId }) => {
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCityIdx, setSelectedCityIdx] = useState(0);
  const [selectedDayIdx, setSelectedDayIdx] = useState(0);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!travelId) return;
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_URL}/api/travels/${travelId}/hotels/suggestions`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Error loading hotel suggestions');
        }
        const json = await res.json();
        setData(json.suggestions || []);
        setSelectedCityIdx(0);
        setSelectedDayIdx(0);
      } catch (e) {
        setError(e.message || 'Error loading hotel suggestions');
      } finally {
        setLoading(false);
      }
    };
    fetchSuggestions();
  }, [travelId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Typography variant="body1">Loading hotels…</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', color: 'error.main' }}>
        <Typography variant="h6">Error</Typography>
        <Typography variant="body2">{error}</Typography>
      </Box>
    );
  }

  const cities = data || [];
  const activeCity = cities[selectedCityIdx] || null;
  const days = (activeCity?.days && activeCity.days.length > 0) ? activeCity.days : [{ date: activeCity?.check_in, hotels: activeCity?.hotels || [] }];
  const activeDay = days[selectedDayIdx] || null;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
        Hotel Suggestions
      </Typography>

      {/* Tabs por ciudad */}
      <Tabs value={selectedCityIdx} onChange={(e, v) => { setSelectedCityIdx(v); setSelectedDayIdx(0); }} variant="scrollable" scrollButtons allowScrollButtonsMobile sx={{ mb: 2 }}>
        {cities.map((g, gi) => (
          <Tab key={`ct-${gi}`} label={g.city} />
        ))}
      </Tabs>

      {/* Tabs by day within the city */}
      {activeCity && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {activeCity.check_in} → {activeCity.check_out} ({activeCity.nights} nights)
          </Typography>
          <Tabs value={selectedDayIdx} onChange={(e, v) => setSelectedDayIdx(v)} variant="scrollable" scrollButtons allowScrollButtonsMobile sx={{ mb: 2 }}>
            {days.map((d, di) => (
              <Tab key={`dy-${di}`} label={d.date} />
            ))}
          </Tabs>
        </>
      )}

      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {!activeDay && (
          <Typography variant="body2" color="text.secondary">No suggestions.</Typography>
        )}
        {activeDay && (
          <Grid container spacing={2}>
            {(activeDay.hotels || []).map((h, hi) => (
              <Grid item xs={12} sm={6} md={4} key={`h-${selectedCityIdx}-${selectedDayIdx}-${hi}`}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  {h.image_url && (
                    <CardMedia component="img" height="180" image={h.image_url} alt={h.name} loading="lazy" />
                  )}
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                      {h.name}
                    </Typography>
                    {h.area && (
                      <Typography variant="body2" color="text.secondary">{h.area}</Typography>
                    )}
                    <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {h.price_tier && <Chip size="small" label={h.price_tier} />}
                    </Box>
                    {h.notes && (
                      <Typography variant="body2" sx={{ mt: 1 }}>{h.notes}</Typography>
                    )}
                  </CardContent>
                  <Box sx={{ p: 2, pt: 0 }}>
                    {h.deeplink_url && (
                      <Button fullWidth variant="contained" color="primary" href={h.deeplink_url} target="_blank" rel="noopener noreferrer">
                        Check availability
                      </Button>
                    )}
                  </Box>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Box>
  );
};

export default HotelsSection;


