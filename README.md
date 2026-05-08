# Astro Server

Proxy seguro entre tu widget GHL y la Astrologer API de RapidAPI.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/planets` | Posiciones planetarias actuales |
| POST | `/chart` | Fase lunar con fecha y lugar específicos |
| GET | `/health` | Verificar que el servidor está vivo |

### POST /chart — body de ejemplo
```json
{
  "year": 1993,
  "month": 10,
  "day": 10,
  "hour": 12,
  "minute": 12,
  "latitude": 51.5074,
  "longitude": -0.1276,
  "timezone": "Europe/London"
}
```

---

## Deploy en Railway (paso a paso)

### 1. Instalar Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login
```bash
railway login
```
Se abre el navegador para autenticarse.

### 3. Crear proyecto nuevo
```bash
cd astro-server
railway init
```
Elegí "Create new project" y dale un nombre (ej: `astro-server`).

### 4. Configurar la variable de entorno en Railway
```bash
railway variables set RAPIDAPI_KEY=tu_key_aqui
```
**Importante:** Railway asigna `PORT` automáticamente — no hace falta setearlo.

### 5. Deploy
```bash
railway up
```

### 6. Obtener tu URL pública
```bash
railway open
```
O desde el dashboard en railway.app. La URL queda algo como:
`https://astro-server-production-xxxx.up.railway.app`

### 7. Probar
```bash
curl https://tu-url.up.railway.app/health
curl https://tu-url.up.railway.app/planets
```

---

## Desarrollo local

```bash
npm install
npm run dev
```

El servidor arranca en `http://localhost:3000`.
