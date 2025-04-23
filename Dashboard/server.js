const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 5000;

const isDocker = process.env.DOCKER_ENV === '1' || process.env.CONTAINER === 'true' || process.env.DOCKER_CONTAINER === 'true';
const backendApiUrl = process.env.BACKEND_API_URL && process.env.BACKEND_API_URL.trim() !== ''
  ? process.env.BACKEND_API_URL
  : (isDocker ? 'http://twitch-shorts:8000' : 'http://localhost:8000');
console.log('Proxying /api to:', backendApiUrl);
console.log('ENV:', process.env); // Debug log to show all environment variables

// Serve static files from the frontend build
app.use(express.static(path.join(__dirname, 'frontend', 'dist')));

// Proxy API requests to the backend Python API
app.use('/api', createProxyMiddleware({
  target: backendApiUrl,
  changeOrigin: true,
  // pathRewrite: { '^/api': '' }, // Removed for best practice
  logLevel: 'debug',
}));

// Fallback to index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Dashboard server running on port ${PORT}`);
});