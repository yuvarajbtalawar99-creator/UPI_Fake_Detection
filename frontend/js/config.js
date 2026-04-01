/**
 * KAVACH – Configuration
 * API endpoints and environmental settings.
 */

window.KavachConfig = {
    // Automatically switches between localhost and production URL
    API_BASE_URL: window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1') 
        ? "http://localhost:8000" 
        : "https://webmasters-assessed-britney-instructions.trycloudflare.com"
};
