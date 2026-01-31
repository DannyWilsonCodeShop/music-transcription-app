// Simple CORS fix - Test the API directly with a local proxy
const https = require('https');
const http = require('http');
const url = require('url');

const TARGET_API = 'https://rzx9drt3z1.execute-api.us-east-1.amazonaws.com/prod';
const PORT = 3001;

// CORS headers
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Max-Age': '86400'
};

const server = http.createServer((req, res) => {
  console.log(`${req.method} ${req.url}`);

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(200, CORS_HEADERS);
    res.end();
    return;
  }

  // Proxy to target API
  const targetUrl = TARGET_API + req.url;
  const parsedUrl = url.parse(targetUrl);
  
  const options = {
    hostname: parsedUrl.hostname,
    port: parsedUrl.port || 443,
    path: parsedUrl.path,
    method: req.method,
    headers: {
      ...req.headers,
      host: parsedUrl.hostname
    }
  };

  const proxyReq = https.request(options, (proxyRes) => {
    // Add CORS headers to response
    const responseHeaders = {
      ...proxyRes.headers,
      ...CORS_HEADERS
    };
    
    res.writeHead(proxyRes.statusCode, responseHeaders);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err);
    res.writeHead(500, CORS_HEADERS);
    res.end(JSON.stringify({ error: 'Proxy error', message: err.message }));
  });

  // Forward request body
  req.pipe(proxyReq);
});

server.listen(PORT, () => {
  console.log(`🌐 CORS proxy server running on http://localhost:${PORT}`);
  console.log(`📡 Proxying to: ${TARGET_API}`);
  console.log('');
  console.log('🔧 Update your frontend to use: http://localhost:3001');
  console.log('');
  console.log('📝 Test with:');
  console.log(`curl -X POST http://localhost:${PORT}/jobs \\`);
  console.log(`  -H 'Content-Type: application/json' \\`);
  console.log(`  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=CDdvReNKKuk"}'`);
});