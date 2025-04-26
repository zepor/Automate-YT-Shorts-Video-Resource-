const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 5000;

const isDocker = process.env.DOCKER_ENV === '1' || process.env.CONTAINER === 'true' || process.env.DOCKER_CONTAINER === 'true';
const backendApiUrl = process.env.BACKEND_API_URL && process.env.BACKEND_API_URL.trim() !== ''
  ? process.env.BACKEND_API_URL
  : (isDocker ? 'http://twitch-shorts:8000' : 'http://localhost:8000');
console.log('Proxying /api to:', backendApiUrl);
console.log('ENV:', process.env); // Debug log to show all environment variables

const logStream = fs.createWriteStream(path.join(__dirname, 'dashboard.log'), { flags: 'a' });
app.use((req, res, next) => {
  logStream.write(`[${new Date().toISOString()}] ${req.method} ${req.url}\n`);
  next();
});

// Serve static files from the frontend build
app.use(express.static(path.join(__dirname, 'frontend', 'dist')));

// Proxy API requests to the backend Python API
app.use('/api', createProxyMiddleware({
  target: backendApiUrl,
  changeOrigin: true,
  // pathRewrite: { '^/api': '' }, // Removed for best practice
  logLevel: 'debug',
}));

// API: List all markdown files in the repo root (exclude ENV.md)
app.get('/api/markdown_files', (req, res) => {
  const repoRoot = path.join(__dirname, '..');
  fs.readdir(repoRoot, (err, files) => {
    if (err) return res.status(500).json({ error: 'Failed to list markdown files' });
    const mdFiles = files.filter(f => f.endsWith('.md') && f !== 'ENV.md');
    res.json(mdFiles);
  });
});

// API: Get content of a specific markdown file
app.get('/api/markdown_file/:filename', (req, res) => {
  const repoRoot = path.join(__dirname, '..');
  const { filename } = req.params;
  if (!filename.endsWith('.md')) return res.status(400).json({ error: 'Invalid file type' });
  const filePath = path.join(repoRoot, filename);
  if (!filePath.startsWith(repoRoot)) return res.status(400).json({ error: 'Invalid path' });
  fs.readFile(filePath, 'utf-8', (err, data) => {
    if (err) return res.status(404).json({ error: 'File not found' });
    res.type('text/markdown').send(data);
  });
});

// Fallback to index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Dashboard server running on port ${PORT}`);
});