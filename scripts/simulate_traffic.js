const http = require('http');

const diseases = ['healthy', 'leaf_blast', 'powdery_mildew', 'bacterial_blight'];

const generateMockData = () => {
    // Generate random H3 index (mock format)
    const h3Index = '89' + Math.floor(Math.random() * 10000000000000).toString(16).padEnd(13, '0');
    
    return JSON.stringify({
        h3_index: h3Index,
        disease_label: diseases[Math.floor(Math.random() * diseases.length)],
        confidence: Math.random(),
        timestamp: new Date().toISOString()
    });
};

const sendRequest = () => {
    const data = generateMockData();
    
    const options = {
        hostname: 'localhost',
        port: 8000,
        path: '/api/v1/telemetry/vision-sync',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(data)
        }
    };

    const req = http.request(options, (res) => {
        // We don't care much about the response for the simulation
        res.on('data', () => {});
    });

    req.on('error', (e) => {
        // Ignore connection refused if server is restarting
        if (e.code !== 'ECONNREFUSED') {
            console.error(`Problem with request: ${e.message}`);
        }
    });

    req.write(data);
    req.end();
};

console.log('Starting CropPilot telemetry traffic simulation...');
console.log('Sending randomized POST requests to /api/v1/telemetry/vision-sync');

// Send 10-30 requests every second
setInterval(() => {
    const count = Math.floor(Math.random() * 20) + 10;
    for (let i = 0; i < count; i++) {
        sendRequest();
    }
}, 1000);
