# DulceMoment Backend (FastAPI)

API para cliente y tienda con:
- catálogo de productos y opciones de personalización
- cálculo de precio por ingrediente/tamaño/forma/sabor/color
- control de stock y estado agotado
- pedidos con tracking por etapas
- pagos con tarjeta (Stripe intent y pago por tarjeta directo)
- push notifications por estado (FCM opcional)
- imágenes de producto con Cloudinary (subida por URL)
- auth de login/register con roles customer/store
- autorización JWT para endpoints protegidos

## URL de producción
- Base URL: `https://ferluna.online`
- Alternativa: `https://www.ferluna.online`

## 1) Requisitos
- Python 3.11+

## 2) Configurar entorno
```bash
cd backend-fastapi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## 3) Ejecutar
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger: http://localhost:8000/docs

Para la app Android actual se usa puerto 8002:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

## 4) Flujo recomendado (demo)
1. `POST /api/v1/auth/login` o `POST /api/v1/auth/register`.
2. `GET /api/v1/products` para catálogo.
3. `POST /api/v1/orders` para crear pedido (incluye personalización).
4. `POST /api/v1/payments/card` para cobro de tarjeta.
5. `POST /api/v1/orders/{id}/status` (solo tienda) para etapas + push.
6. `GET /api/v1/orders?customer_id=...` para logística del cliente.

## Endpoints clave por rol
- Tienda:
	- `POST /api/v1/products` (requiere `actor_user_id` de rol store)
	- `PATCH /api/v1/products/{id}` (requiere `actor_user_id` store)
	- `POST /api/v1/orders/{id}/status` (requiere `actor_user_id` store)
- Cliente:
	- `POST /api/v1/orders`
	- `GET /api/v1/orders?customer_id=<id>`
	- `POST /api/v1/payments/card`

## JWT
- `POST /api/v1/auth/login` y `POST /api/v1/auth/register` retornan `access_token` + `refresh_token`.
- `POST /api/v1/auth/refresh` rota refresh token y entrega nuevos tokens.
- `POST /api/v1/auth/logout` revoca access+refresh de la sesión actual.
- `POST /api/v1/auth/logout-all` invalida todas las sesiones del usuario (`token_version`).
- Usa header `Authorization: Bearer <token>` en endpoints protegidos.
- `GET /api/v1/auth/me` valida token y retorna usuario actual.

## 5) Notificaciones push
- Si configuras `FIREBASE_SERVICE_ACCOUNT_PATH`, se envía push real por FCM.
- Si no, la API funciona en modo fallback sin romper el flujo.

## 6) Imágenes con Cloudinary
- Opción recomendada en `.env`: `CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>`.
- Opción alternativa: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
- Endpoint tienda: `POST /api/v1/media/cloudinary/upload-url` con body `{ "source_url": "https://..." }`.
- Respuesta: URL segura de Cloudinary para guardarla en `image_url` del producto.
- Verificación rápida: `GET /api/v1/media/cloudinary/status` (rol tienda) retorna `{ "configured": true|false }`.

## 7) Pagos con tarjeta
- Producción: define `STRIPE_SECRET_KEY` y `ENABLE_FAKE_PAYMENTS=false`.
- Desarrollo: `ENABLE_FAKE_PAYMENTS=true` (aprobación simulada).

## 8) Setup rápido en Ubuntu/EC2

### Opción A: Con SQLite (desarrollo)
```bash
git clone https://github.com/IDS-HUGO/DulceMoment_API.git backend-fastapi
cd backend-fastapi
bash scripts/setup_ubuntu.sh
bash scripts/run_api.sh
```

### Opción B: Con MySQL (producción en EC2)

1. **Instalar MySQL en EC2:**
```bash
sudo apt update
sudo apt install -y mysql-server
sudo mysql_secure_installation
# Crear base de datos
sudo mysql -u root -p << EOF
CREATE DATABASE dulcemoment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dulcemoment'@'localhost' IDENTIFIED BY 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON dulcemoment_db.* TO 'dulcemoment'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

2. **Configurar API con MySQL:**
```bash
git clone https://github.com/IDS-HUGO/DulceMoment_API.git backend-fastapi
cd backend-fastapi
bash scripts/setup_ubuntu.sh
# Editar .env
nano .env
# Descomentar y actualizar DATABASE_URL a:
# DATABASE_URL=mysql+pymysql://dulcemoment:tu_contraseña_segura@localhost:3306/dulcemoment_db
bash scripts/run_api.sh
```

3. **Alternativa: Usar docker-compose** (recomendado para EC2):
```bash
# Si tienes docker-compose.yml en el repo
docker-compose up -d
```

Variables opcionales para correr:
- `HOST` (default `0.0.0.0`)
- `PORT` (default `8000`)
- `RELOAD=true` para modo desarrollo

Ejemplo:
```bash
HOST=0.0.0.0 PORT=8002 RELOAD=true bash scripts/run_api.sh
```
