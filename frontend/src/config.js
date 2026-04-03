// This file exports configuration values for your frontend application.
// It checks for a REACT_APP_API_BASE_URL environment variable (which should be
// defined in your .env.development or .env.production file). If it's not present,
// it falls back to a localhost URL for development.

console.log('Current NODE_ENV:', process.env.NODE_ENV);

// Determine if we're in test environment
const isTest = process.env.REACT_APP_ENVIRONMENT === 'test';

const config = {
    // API calls base URL
    API_BASE_URL: process.env.REACT_APP_API_URL ||
        (isTest ? 'http://test-ec2-ip:8000/api/v1' :
            (process.env.NODE_ENV === 'production' ?
                '/api/v1' : 'http://localhost:8000/api/v1')),

    // For WebSocket connections - use secure WebSockets (wss://) in production
    WS_BASE_URL: process.env.REACT_APP_WS_URL ||
        (isTest ? 'ws://test-ec2-ip:8000/api/v1' :
            (process.env.NODE_ENV === 'production' ?
                'wss://' + window.location.host + '/api/v1' :
                'ws://localhost:8000/api/v1')),

    APP_URL: process.env.REACT_APP_URL ||
        (isTest ? 'https://test.ponder.school' : 'http://localhost:3000'),
    BASE_PATH: process.env.REACT_APP_BASE_PATH || '',
    PUBLIC_URL: process.env.PUBLIC_URL || ''
};

console.log('Config loaded:', config);

export default config;
