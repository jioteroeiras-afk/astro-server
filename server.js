require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const RAPIDAPI_KEY = process.env.RAPIDAPI_KEY;

app.use(cors());
app.use(express.json());

const rapidApiHeaders = {
  'Content-Type': 'application/json',
  'x-rapidapi-host': 'astrologer.p.rapidapi.com',
  'x-rapidapi-key': RAPIDAPI_KEY,
};

// GET /planets — posiciones planetarias actuales (ahora mismo en GMT)
app.get('/planets', async (req, res) => {
  if (!RAPIDAPI_KEY) {
    return res.status(500).json({ error: 'RAPIDAPI_KEY no configurada' });
  }

  try {
    const response = await fetch('https://astrologer.p.rapidapi.com/api/v5/now/context', {
      method: 'POST',
      headers: rapidApiHeaders,
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      const text = await response.text();
      return res.status(response.status).json({ error: text });
    }

    const data = await response.json();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /chart — carta natal / posiciones para fecha y lugar específicos
// Body: { year, month, day, hour, minute, latitude, longitude, timezone }
app.post('/chart', async (req, res) => {
  if (!RAPIDAPI_KEY) {
    return res.status(500).json({ error: 'RAPIDAPI_KEY no configurada' });
  }

  const { year, month, day, hour, minute, latitude, longitude, timezone, location_precision } = req.body;

  if (!year || !month || !day || latitude == null || longitude == null || !timezone) {
    return res.status(400).json({
      error: 'Campos requeridos: year, month, day, latitude, longitude, timezone',
    });
  }

  try {
    const response = await fetch('https://astrologer.p.rapidapi.com/api/v5/moon-phase/context', {
      method: 'POST',
      headers: rapidApiHeaders,
      body: JSON.stringify({
        year,
        month,
        day,
        hour: hour ?? 12,
        minute: minute ?? 0,
        latitude,
        longitude,
        timezone,
        location_precision: location_precision ?? 4,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      return res.status(response.status).json({ error: text });
    }

    const data = await response.json();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /natal — carta natal con Kerykeion (Python subprocess)
app.post('/natal', (req, res) => {
  const python = spawn('python3', [path.join(__dirname, 'natal.py')]);
  let stdout = '';
  let stderr = '';

  python.stdin.write(JSON.stringify(req.body));
  python.stdin.end();

  python.stdout.on('data', (d) => { stdout += d.toString(); });
  python.stderr.on('data', (d) => { stderr += d.toString(); });

  python.on('close', (code) => {
    if (code !== 0) {
      console.error('natal.py error:', stderr);
      return res.status(500).json({ error: stderr || 'Error calculando carta natal' });
    }
    try {
      res.json(JSON.parse(stdout));
    } catch (e) {
      res.status(500).json({ error: 'Respuesta inválida del cálculo' });
    }
  });
});

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

app.listen(PORT, () => {
  console.log(`Astro server corriendo en http://localhost:${PORT}`);
  console.log(`RAPIDAPI_KEY: ${RAPIDAPI_KEY ? '✓ configurada' : '✗ FALTA — setear en .env'}`);
});
