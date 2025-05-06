import axios from 'axios';

// Determine API base URL based on environment
const getBaseUrl = () => {
  // In production, use the relative path which will be handled by Vercel routing
  if (process.env.NODE_ENV === 'production') {
    return '/api';
  }
  
  // In development, use the local FastAPI server
  return 'http://localhost:8002';
};

// Create axios instance with proper configuration
const api = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout for API calls
});

// Add request interceptor for handling common request tasks
api.interceptors.request.use(
  (config) => {
    // Ensure all endpoints have the correct prefix
    if (!config.url.startsWith('/api/') && !config.url.startsWith('/workflow/')) {
      config.url = `/api${config.url.startsWith('/') ? '' : '/'}${config.url}`;
    }

    // MOCK DATA: Add mock=true to all requests
    if (!config.params) {
      config.params = {};
    }
    config.params.mock = 'true';
    
    // Direct endpoints to our mock data API
    if (config.url.includes('/api/events')) {
      // Redirect to mock endpoints
      config.url = config.url.replace('/api/events', '/api/mock/events');
    }
    
    // You could add auth tokens here if needed in the future
    console.log('API Request:', config.method.toUpperCase(), config.url, config.data, config.params);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for handling common response tasks
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Log API errors to help with debugging
    console.error('API Error:', error.response ? error.response.data : error.message);
    // Handle common errors (e.g., unauthorized, server errors)
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('API Error: No response received', error.request);
    } else {
      console.error('API Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
