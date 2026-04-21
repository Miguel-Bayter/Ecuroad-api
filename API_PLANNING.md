# EstuRoad — Planificación API Backend con Datos Reales

> **Alcance:** Diseño e implementación de la API REST que consume el frontend actual de EstuRoad, reemplazando datos inventados por datos reales de Colombia, con seguridad basada en OWASP Top 10 (2021).  
> **Restricción:** El frontend NO se modifica. La API debe respetar el contrato actual de `/src/api/index.ts`.

---

## 1. Diagnóstico — Estado Actual vs. Objetivo

| Aspecto | Estado actual | Objetivo |
|---------|--------------|---------|
| Datos de carreras | 13 carreras inventadas en `seed.js` | 340+ programas reales del SNIES/MEN |
| Salarios | Cifras aproximadas sin fuente | Datos del OLE (Observatorio Laboral para la Educación) |
| Universidades | Nombres reales, costos ficticios | Costos reales del SNIES + IES |
| Demanda regional | Distribución inventada por región | DANE + MinTrabajo + SENA estadísticas |
| Proyección 2030 | Texto fijo sin respaldo | Informes de MinTrabajo / OCDE Colombia |
| Seguridad | Helmet + rate-limit básico | OWASP Top 10 completo |
| Autenticación | Ninguna (perfil en localStorage) | JWT stateless + sesiones persistidas en BD |

---

## 2. Fuentes de Datos Reales — Colombia

### 2.1 Educación Superior

| Fuente | URL / API | Datos disponibles | Acceso |
|--------|-----------|------------------|--------|
| **SNIES** (Sistema Nacional de Información de la Educación Superior — MEN) | `https://snies.mineducacion.gov.co` | Programas activos, costos por semestre, IES, modalidad, nivel de formación | API pública / descarga CSV |
| **OLE** (Observatorio Laboral para la Educación) | `https://ole.mineducacion.gov.co` | Salario entrada por área, empleabilidad 12 meses después de graduado, inserción laboral | Descarga Excel / API |
| **SPADIES** | `https://spadies3.mineducacion.gov.co` | Deserción por programa y región, tasa de graduación | Descarga |
| **IES - Mineducación** | Portal MIDES | Rankings IES, acreditación de alta calidad, costos matricula | Scraping + descarga |

### 2.2 Mercado Laboral

| Fuente | Datos disponibles |
|--------|------------------|
| **DANE — Gran Encuesta Integrada de Hogares (GEIH)** | Tasa de desempleo por área, salario promedio por ocupación y región |
| **MinTrabajo — Observatorio SIFE** | Vacantes por cargo, región, nivel de educación requerido |
| **SENA — Estadísticas** | Programas tecnológicos, cobertura regional, empleabilidad SENA |
| **Banco de la República** | Informes sectoriales, proyecciones de empleo 2030 por sector |

### 2.3 Estratos y Contexto Socioeconómico

| Fuente | Datos disponibles |
|--------|------------------|
| **ICETEX** | Líneas de crédito vigentes, requisitos por estrato, montos máximos por semestre |
| **DANE — Estratificación** | Distribución de estratos por municipio |

### 2.4 Estrategia de Ingesta de Datos

```
Fase 1 — Datos estáticos (seed manual enriquecido):
  - Descargar catálogo SNIES (CSV/Excel) de programas universitarios activos
  - Cruzar con OLE para salarios reales por área de conocimiento
  - Normalizar a esquema Carrera actual (sin romper el contrato del frontend)
  - 340+ carreras iniciales (20 áreas × ~17 programas promedio)

Fase 2 — Ingesta automatizada (script ETL):
  - Script Node.js que consume APIs/descarga SNIES y OLE periódicamente
  - Transformación al modelo Mongoose existente
  - Upsert por slug para no duplicar
  - Cron job mensual (semestral para costos)

Fase 3 — Enriquecimiento dinámico (futuro):
  - WebSocket / cola de trabajos para actualizar demanda regional
  - Integración con LinkedIn API (demanda real de vacantes) si hay presupuesto
```

---

## 3. Modelo de Datos Enriquecido

Los modelos amplían el esquema actual sin romper el contrato del frontend.

### 3.1 Carrera (extensión del modelo actual)

```javascript
// Campos nuevos sobre el modelo Mongoose existente
{
  // --- Trazabilidad de fuente ---
  fuenteSalario:     { type: String, enum: ['OLE', 'DANE', 'manual'], default: 'manual' },
  fuenteDemanda:     { type: String, enum: ['MinTrabajo', 'SENA', 'manual'], default: 'manual' },
  sniesCode:         { type: String, unique: true, sparse: true }, // código SNIES
  cineCode:          { type: String },                             // clasificación CINE-UNESCO
  ultimaActualizacion: { type: Date, default: Date.now },

  // --- Datos OLE reales ---
  tasaEmpleabilidad12m: { type: Number },   // % empleados a 12 meses de graduarse
  salarioMediana:       { type: Number },   // mediana (más robusta que promedio)
  
  // --- Acreditación ---
  acreditadaAltaCalidad: { type: Boolean, default: false },
  
  // --- Metadatos de ingesta ---
  verificado: { type: Boolean, default: false }, // revisado manualmente
}
```

### 3.2 Universidad (extensión)

```javascript
{
  sniesIesCode:    { type: String },
  acreditada:      { type: Boolean, default: false },
  tipo:            { type: String, enum: ['pública', 'privada', 'oficial', 'mixta'] },
  sitioWeb:        { type: String },
  programasActivos: { type: Number },
}
```

### 3.3 DataFuenteAuditoria (nuevo modelo)

```javascript
// Registra cada ingesta de datos para trazabilidad
{
  fuente:        { type: String, required: true },
  fechaIngesta:  { type: Date, default: Date.now },
  totalRegistros: { type: Number },
  hash:          { type: String }, // SHA-256 del archivo fuente
  operador:      { type: String }, // quién ejecutó el ETL
}
```

---

## 4. Arquitectura de la API

### 4.1 Estructura de Carpetas (server/)

```
server/
├── src/
│   ├── app.js
│   ├── index.js
│   ├── config/
│   │   ├── database.js
│   │   ├── env.js              ← validación de variables de entorno al inicio
│   │   └── security.js         ← configuración centralizada de helmet, cors, rate-limit
│   ├── models/
│   │   ├── Carrera.js
│   │   ├── Perfil.js
│   │   └── AuditLog.js         ← nuevo: log de eventos de seguridad
│   ├── controllers/
│   │   ├── carrerasController.js
│   │   └── perfilesController.js
│   ├── routes/
│   │   ├── index.js
│   │   ├── carreras.js
│   │   └── perfiles.js
│   ├── middleware/
│   │   ├── errorHandler.js
│   │   ├── notFound.js
│   │   ├── validate.js         ← nuevo: validación Joi centralizada
│   │   ├── rateLimiter.js      ← nuevo: limitadores por endpoint
│   │   └── sanitize.js         ← nuevo: sanitización de inputs (OWASP A03)
│   ├── utils/
│   │   ├── scoring.js
│   │   └── logger.js           ← nuevo: logger estructurado (Winston)
│   └── seed/
│       ├── seed.js             ← refactorizado con datos reales
│       └── etl/
│           ├── snies.js        ← parser SNIES CSV
│           └── ole.js          ← parser OLE Excel
└── .env.example
```

### 4.2 Endpoints — Contrato Inmutable (frontend no cambia)

Los siguientes endpoints YA existen y NO cambian su firma:

```
GET  /api/carreras                        → list (soporta ?categoria, ?tipo)
POST /api/carreras/recomendaciones        → ranking personalizado
GET  /api/carreras/:slug                  → detalle por slug

POST /api/perfiles                        → crear perfil
GET  /api/perfiles/:id                    → obtener perfil
PATCH /api/perfiles/:id                   → actualizar perfil parcialmente
```

### 4.3 Endpoints Nuevos (internos / admin)

```
GET  /api/carreras/:slug/stats            → métricas de visitas (uso interno)
POST /api/admin/etl/run                   → disparar ingesta manual (requiere API key)
GET  /api/health                          → health check (uptime, DB status)
```

---

## 5. Seguridad — OWASP Top 10 (2021)

### A01 — Broken Access Control

**Riesgo en EstuRoad:** Perfiles de usuarios accesibles por ID sin autenticación; cualquiera puede leer o modificar el perfil de otro usuario con su `_id`.

**Mitigación:**
```javascript
// Implementar tokens de sesión anónima para perfiles
// Al crear un perfil → generar un sessionToken (UUID v4) y devolverlo al cliente
// El frontend lo guarda en localStorage junto al _id actual
// Cada PATCH /perfiles/:id requiere el header X-Session-Token correcto

// server/src/middleware/sessionAuth.js
const verifySessionToken = async (req, res, next) => {
  const token = req.headers['x-session-token'];
  const perfil = await Perfil.findById(req.params.id).select('+sessionToken');
  if (!perfil || !token || !crypto.timingSafeEqual(
    Buffer.from(perfil.sessionToken), Buffer.from(token)
  )) {
    return res.status(403).json({ error: 'Acceso denegado' });
  }
  next();
};
```

**Reglas adicionales:**
- Endpoints `GET /carreras` son públicos (lectura, no contiene datos sensibles)
- `PATCH /perfiles/:id` exige sessionToken
- No exponer `_id` interno de MongoDB; generar un `publicId` (ULID) para el frontend
- Admin endpoints exigen `X-API-Key` hasheada con bcrypt en base de datos

---

### A02 — Cryptographic Failures

**Riesgo:** Datos de perfil (estrato, presupuesto familiar, datos socioeconómicos) se transmiten en texto plano si no hay HTTPS; sessionToken en texto plano en BD.

**Mitigación:**
```javascript
// .env obligatorio
FORCE_HTTPS=true
SESSION_TOKEN_SECRET=<256-bit random hex>

// Hashear sessionToken antes de guardarlo en BD (PBKDF2)
const crypto = require('crypto');
const hashedToken = crypto.pbkdf2Sync(rawToken, salt, 100000, 64, 'sha512').toString('hex');

// En config/security.js
app.use((req, res, next) => {
  if (process.env.FORCE_HTTPS === 'true' && req.headers['x-forwarded-proto'] !== 'https') {
    return res.redirect(301, 'https://' + req.hostname + req.originalUrl);
  }
  next();
});

// Helmet con HSTS
helmet.hsts({ maxAge: 31536000, includeSubDomains: true, preload: true })
```

---

### A03 — Injection

**Riesgo:** Queries a MongoDB sin sanitización pueden ser vulnerables a NoSQL Injection (ej: `{ "$gt": "" }` en campos de búsqueda).

**Mitigación:**
```javascript
// middleware/sanitize.js — instalar mongo-sanitize
const mongoSanitize = require('express-mongo-sanitize');
app.use(mongoSanitize({
  replaceWith: '_',   // reemplaza $ y . en keys
  onSanitize: ({ req, key }) => {
    logger.warn('NoSQL injection attempt', { ip: req.ip, key, path: req.path });
  }
}));

// Esquemas Joi con tipos estrictos para cada endpoint
const perfilSchema = Joi.object({
  ciudad:    Joi.string().max(100).pattern(/^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$/).required(),
  estrato:   Joi.number().integer().min(1).max(6).required(),
  presupuesto: Joi.number().min(0).max(50000000).required(),
  // ... sin permitir objetos anidados no declarados
}).options({ stripUnknown: true }); // eliminar campos extra
```

---

### A04 — Insecure Design

**Riesgo:** El algoritmo de scoring es el mismo en cliente y servidor; un atacante puede reverse-engineer el scoring para manipular resultados enviando un perfil fabricado.

**Mitigación:**
- **Mover el scoring completamente al servidor.** El cliente recibe la lista ya rankeada; el algoritmo no se expone.
- El campo `score` en la respuesta es opcional y solo se incluye si `?includeScore=true` con una API key.
- Diseñar con **threat modeling** desde el inicio: ¿qué datos NO deben exponerse? (ej: `sessionToken`, `_id` de MongoDB).
- Separar el modelo de BD del DTO de respuesta: usar un `toPublic()` en cada modelo.

```javascript
// models/Carrera.js
carreraSchema.methods.toPublic = function() {
  const obj = this.toObject();
  delete obj.__v;
  delete obj.fuenteSalario;   // interno
  delete obj.sniesCode;       // puede ser sensible
  return obj;
};
```

---

### A05 — Security Misconfiguration

**Riesgo:** Variables de entorno no validadas al inicio; headers por defecto de Express que exponen información del servidor; CORS abierto a `*`.

**Mitigación:**
```javascript
// config/env.js — validar al arranque
const required = ['MONGODB_URI', 'PORT', 'CLIENT_ORIGIN', 'SESSION_TOKEN_SECRET'];
const missing = required.filter(key => !process.env[key]);
if (missing.length) {
  console.error(`FATAL: Missing env vars: ${missing.join(', ')}`);
  process.exit(1);
}

// config/security.js — Helmet completo
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:"],
    }
  },
  referrerPolicy: { policy: 'same-origin' },
  xContentTypeOptions: true,
  xFrameOptions: { action: 'deny' },
}));

// CORS estricto
app.use(cors({
  origin: process.env.CLIENT_ORIGIN,   // solo el dominio del frontend
  methods: ['GET', 'POST', 'PATCH'],
  allowedHeaders: ['Content-Type', 'X-Session-Token'],
  maxAge: 600,
}));
```

---

### A06 — Vulnerable and Outdated Components

**Riesgo:** Dependencias con CVEs conocidos; `package-lock.json` sin auditoría.

**Mitigación:**
```bash
# Agregar a CI/CD (GitHub Actions)
npm audit --audit-level=high
npx better-npm-audit check

# Renovate o Dependabot para PRs automáticos de actualizaciones
# Lockfile: siempre comitear package-lock.json
# No usar rangos amplios: "^4.0.0" → "4.19.x"
```

**Dependencias de seguridad a mantener actualizadas:**
- `helmet` ≥ 7.x
- `express-mongo-sanitize` ≥ 2.x
- `joi` ≥ 17.x
- `express-rate-limit` ≥ 7.x

---

### A07 — Identification and Authentication Failures

**Riesgo:** No existe autenticación; perfiles son anónimos; no hay límite en creación de perfiles (abuso de BD).

**Mitigación:**
```javascript
// Rate limiting diferenciado por endpoint
const { rateLimit } = require('express-rate-limit');

// Crear perfil: máximo 5 por IP por hora
const createPerfilLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 5,
  message: { error: 'Demasiados perfiles creados. Intenta más tarde.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// Recomendaciones: máximo 30 por IP por 15 minutos
const recomenLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 30,
});

// Aplicar en routes/perfiles.js
router.post('/', createPerfilLimiter, validate(perfilSchema), createPerfil);

// Tokens de sesión anónima con expiración (90 días)
perfilSchema.add({
  sessionToken: { type: String, select: false },
  sessionExpiry: { type: Date, default: () => new Date(Date.now() + 90*24*60*60*1000) },
});
```

---

### A08 — Software and Data Integrity Failures

**Riesgo:** El script ETL descarga archivos externos (SNIES, OLE); si la fuente es comprometida, se inyectan datos maliciosos a la BD.

**Mitigación:**
```javascript
// etl/snies.js — verificar integridad antes de procesar
const crypto = require('crypto');

async function downloadWithIntegrityCheck(url, expectedHash) {
  const buffer = await fetch(url).then(r => r.arrayBuffer());
  const hash = crypto.createHash('sha256').update(Buffer.from(buffer)).digest('hex');
  
  if (expectedHash && hash !== expectedHash) {
    throw new Error(`Integrity check failed. Expected ${expectedHash}, got ${hash}`);
  }
  
  // Registrar en AuditLog
  await DataFuenteAuditoria.create({ fuente: url, hash, fechaIngesta: new Date() });
  return buffer;
}

// Validar cada registro con Joi antes de insertar en BD
// No ejecutar ETL como root; usar usuario de BD con permisos mínimos (solo write en colección carreras)
```

---

### A09 — Security Logging and Monitoring Failures

**Riesgo:** No existe logging estructurado; errores de seguridad (injection attempts, 403s) se pierden.

**Mitigación:**
```javascript
// utils/logger.js — Winston estructurado
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    // En producción: agregar transporte a servicio externo (Logtail, Datadog, etc.)
  ],
});

// Qué registrar obligatoriamente:
// - IP + endpoint + status para toda respuesta 4xx/5xx
// - Intentos de NoSQL injection (desde sanitize.js)
// - Creación/modificación de perfiles
// - Ejecuciones del ETL (quién, cuándo, cuántos registros)
// - Errores de validación repetidos desde misma IP (posible fuzzing)

// NO registrar: sessionToken, datos del perfil (privacidad)
```

**Alertas recomendadas:**
- > 10 errores 403 desde misma IP en 5 minutos → bloquear temporalmente
- > 50 errores 500 en 1 hora → alerta al equipo
- Fallo en ETL → notificación inmediata

---

### A10 — Server-Side Request Forgery (SSRF)

**Riesgo:** El script ETL hace peticiones HTTP a URLs externas; si las URLs vienen de inputs del usuario, un atacante puede hacer que el servidor consulte recursos internos.

**Mitigación:**
```javascript
// etl/snies.js — lista blanca de dominios permitidos
const ALLOWED_ETL_DOMAINS = [
  'snies.mineducacion.gov.co',
  'ole.mineducacion.gov.co',
  'dane.gov.co',
];

function validateEtlUrl(url) {
  const parsed = new URL(url);
  if (!ALLOWED_ETL_DOMAINS.includes(parsed.hostname)) {
    throw new Error(`SSRF blocked: domain ${parsed.hostname} not in allowlist`);
  }
  // Bloquear IPs privadas
  if (/^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.|::1|localhost)/i.test(parsed.hostname)) {
    throw new Error('SSRF blocked: private address detected');
  }
  return url;
}

// Las URLs del ETL SIEMPRE vienen de config, NUNCA de inputs del usuario
// El endpoint /admin/etl/run no acepta parámetros de URL
```

---

## 6. Plan de Implementación por Fases

### Fase 1 — Seguridad Base (Semana 1-2)

**Objetivo:** Reforzar el servidor existente con OWASP Top 10 sin romper funcionalidad.

| Tarea | Archivo | OWASP |
|-------|---------|-------|
| Instalar y configurar `express-mongo-sanitize` | `middleware/sanitize.js` | A03 |
| Validación Joi estricta en todos los endpoints | `middleware/validate.js` | A03, A04 |
| Helmet completo + CORS estricto | `config/security.js` | A05 |
| Rate limiting diferenciado por ruta | `middleware/rateLimiter.js` | A07 |
| Logger estructurado con Winston | `utils/logger.js` | A09 |
| Validación de variables de entorno al inicio | `config/env.js` | A05 |
| sessionToken para perfiles (modelo + middleware) | `models/Perfil.js`, `middleware/sessionAuth.js` | A01, A02 |

**Dependencias:**
```bash
npm install express-mongo-sanitize winston helmet@latest
```

---

### Fase 2 — Datos Reales (Semana 3-5)

**Objetivo:** Reemplazar seed ficticio con datos reales del SNIES y OLE.

| Tarea | Detalle |
|-------|---------|
| Descargar catálogo SNIES | CSV de programas universitarios activos (nivel técnico, tecnológico y profesional) |
| Parser SNIES → modelo Carrera | `etl/snies.js`: mapear códigos CINE a categorías del frontend |
| Descargar datos OLE | Excel de salarios y empleabilidad por área de conocimiento |
| Parser OLE → campos de salario | `etl/ole.js`: salarioEntrada, salarioMedio, tasaEmpleabilidad12m |
| Enriquecer universidades | Cruzar IES del SNIES con datos de acreditación CNA |
| Demanda regional DANE/MinTrabajo | Mapear vacantes por región a `demandaPorRegion` |
| Validar integridad de datos (A08) | Hash SHA-256 + registro en AuditLog |
| Script ETL completo con dry-run | `npm run etl:dry` → reporta sin insertar; `npm run etl:run` → inserta |

**Mapeo CINE → Categoría EstuRoad:**

| Área CINE | Categoría EstuRoad |
|-----------|-------------------|
| 061, 062 — TIC | tech |
| 031, 032 — Ciencias sociales y periodismo | comunicacion / social |
| 041, 042 — Ciencias empresariales | negocios |
| 051, 052 — Ciencias naturales, exactas | ingenieria |
| 071, 072 — Ingeniería y procesos industriales | ingenieria |
| 081 — Agricultura, ganadería, silvicultura | agro |
| 091, 092 — Salud | salud |
| 021 — Artes y humanidades | arte |
| 031 — Derecho | justicia |
| 011, 012 — Educación | educacion |
| 015 — Ciencias del deporte | deporte |

---

### Fase 3 — Optimización y Monitoreo (Semana 6-7)

| Tarea | Detalle |
|-------|---------|
| Índices MongoDB | `slug` (unique), `categoria`, `tipo`, `regionesDemanda`, `empleabilidad` |
| Paginación en `GET /carreras` | Agregar `?page` y `?limit` para no devolver 340+ registros de golpe |
| Caching en memoria | `node-cache` para lista de carreras (TTL: 1 hora); evita queries repetidos |
| Health check endpoint | `GET /api/health` → status de BD, uptime, versión |
| Script de auditoría | `npm run audit:security` → chequea dependencias vulnerables |
| Documentación OpenAPI | `openapi.yaml` con todos los endpoints y schemas |
| Cron job ETL mensual | Actualizar datos SNIES/OLE el primer día de cada mes |

---

## 7. Variables de Entorno Requeridas (.env.example)

```bash
# Servidor
PORT=3001
NODE_ENV=development

# Base de datos
MONGODB_URI=mongodb://localhost:27017/esturoad

# Seguridad
CLIENT_ORIGIN=http://localhost:5173
SESSION_TOKEN_SECRET=<256-bit-hex-random>
ADMIN_API_KEY_HASH=<bcrypt-hash-of-admin-key>
FORCE_HTTPS=false  # true en producción

# ETL (fuentes de datos)
SNIES_BASE_URL=https://snies.mineducacion.gov.co
OLE_BASE_URL=https://ole.mineducacion.gov.co
ETL_EXPECTED_HASH_SNIES=    # SHA-256 del último CSV descargado (A08)

# Logging
LOG_LEVEL=info
LOG_DIR=./logs
```

---

## 8. Dependencias Adicionales

```json
// package.json — agregar a server/
{
  "dependencies": {
    "express-mongo-sanitize": "^2.2.0",
    "winston": "^3.11.0",
    "ulid": "^2.3.0",
    "node-cache": "^5.1.2",
    "xlsx": "^0.18.5"
  },
  "devDependencies": {
    "better-npm-audit": "^3.7.3"
  }
}
```

---

## 9. Checklist de Lanzamiento

### Seguridad
- [ ] `npm audit` sin vulnerabilidades `high` o `critical`
- [ ] Variables de entorno validadas al arranque (proceso falla si faltan)
- [ ] CORS configurado solo al dominio de producción
- [ ] HTTPS forzado en producción
- [ ] sessionToken hasheado en BD (no en texto plano)
- [ ] Rate limiting activo en endpoints de escritura
- [ ] Logs de seguridad activos y rotación configurada
- [ ] Lista blanca de dominios en ETL

### Datos
- [ ] ETL ejecutado en dry-run sin errores
- [ ] Mínimo 50 carreras con datos reales verificados
- [ ] Salarios validados contra datos OLE (año en curso)
- [ ] Universidades con códigos SNIES reales
- [ ] AuditLog registra cada ingesta con hash

### Funcionalidad
- [ ] `GET /api/carreras` devuelve datos y el frontend los muestra igual
- [ ] `POST /api/carreras/recomendaciones` devuelve ranking correcto
- [ ] `GET /api/carreras/:slug` devuelve detalle sin romper pantalla Detail
- [ ] `POST /api/perfiles` crea perfil y devuelve sessionToken al frontend
- [ ] `PATCH /api/perfiles/:id` requiere y valida sessionToken
- [ ] Scoring server-side produce mismos resultados que scoring client-side actual

---

## 10. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| API SNIES no disponible / cambia formato | Media | Alto | Mantener snapshot local del CSV; alertas de integridad |
| Datos OLE desactualizados (publican cada año) | Alta | Medio | Mostrar año de referencia en frontend; actualización anual |
| Degradación del ranking por cambio de datos reales | Media | Alto | A/B test interno antes de publicar; modo `?dryRun=true` en recomendaciones |
| MongoDB expuesto sin auth en desarrollo | Alta | Crítico | `.env` con usuario/contraseña de BD; nunca `localhost:27017` sin auth en staging |
| ETL falla silenciosamente | Media | Alto | Validar conteo post-ingesta; alerta si `totalRegistros < 300` |

---

*Documento generado: 2026-04-20*  
*Proyecto: EstuRoad — Plataforma de orientación vocacional Colombia*  
*Stack: React 19 + TypeScript / Node.js + Express / MongoDB + Mongoose*
