/*
 Reliable Axios mock adapter for auth endpoints when REACT_APP_MOCK is enabled.
 Ensures Login works without a backend.
*/

import axios from 'axios';

(function initAxiosDemoMock() {
  try {
    const flag = ((typeof process !== 'undefined' && process && process.env && process.env.REACT_APP_MOCK)
      || (typeof window !== 'undefined' && window.REACT_APP_MOCK));
    const isMock = String(flag || '').toLowerCase() === 'true';
    if (!isMock) return;

    const originalAdapter = axios.defaults.adapter;
    const demoUserId = 'demo-user-1';

    axios.defaults.adapter = async function demoAdapter(config) {
      try {
        const url = new URL(config.url, window.location.origin);
        const path = url.pathname;
        const method = String(config.method || 'get').toUpperCase();

        // Mock token endpoint
        if (path.endsWith('/api/auth/token') && method === 'POST') {
          return Promise.resolve({
            data: { access_token: 'demo-token', token_type: 'bearer' },
            status: 200,
            statusText: 'OK',
            headers: { 'content-type': 'application/json' },
            config,
            request: {}
          });
        }

        // Mock me endpoint
        if (path.endsWith('/api/auth/me') && method === 'GET') {
          return Promise.resolve({
            data: { id: demoUserId, email: 'demo@user.com', name: 'Demo User' },
            status: 200,
            statusText: 'OK',
            headers: { 'content-type': 'application/json' },
            config,
            request: {}
          });
        }

        // Fallback to real adapter
        return originalAdapter(config);
      } catch (e) {
        return Promise.reject(e);
      }
    };

    // Optional: set a default Authorization header so protected routes work immediately
    if (!axios.defaults.headers.common['Authorization']) {
      axios.defaults.headers.common['Authorization'] = 'Bearer demo-token';
    }

    console.info('[DEMO MOCK] Axios auth adapter enabled');
  } catch (e) {
    console.warn('[DEMO MOCK] Failed to initialize Axios mock:', e);
  }
})();


