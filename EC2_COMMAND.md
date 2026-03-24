# 🚀 COMANDO DEFINITIVO PARA EC2

## Prereq: Ya tienes el repo clonado

Si ya clonaste `DulceMomentAPI`, solo necesitas ejecutar **UN COMANDO**:

```bash
cd /tu/ruta/DulceMomentAPI/backend-fastapi && bash scripts/run_ec2.sh
```

---

## ¿Qué hace el comando?

El script `run_ec2.sh` se encarga de TODO:

1. ✅ Descarga cambios del repo (`git pull`)
2. ✅ Crea el venv si no existe
3. ✅ Instala todas las dependencias
4. ✅ Copia `.env.example` → `.env` (con credenciales Cloudinary ya incluidas)
5. ✅ Verifica que Cloudinary esté configurado
6. ✅ **Inicia la API en `0.0.0.0:8000`**

---

## ✅ Cambios realizados en el código

### 1. Backend (API FastAPI)

#### ❌ Sin datos dummy
- **Archivo:** `app/db/seed.py`
- **Cambio:** Ahora la BD se inicializa vacía (sin usuarios/productos demo)
- **Resultado:** Solo creates usuarios reales

#### ❌ Error al crear vendedor → ARREGLADO
- **Archivo:** `app/api/routes.py`
- **Cambio Anterior:** Si ya existe un vendedor, retornaba error `HTTP 403`
- **Cambio Nuevo:** Si ya existe un vendedor, retorna sus datos (como si lo "recuperaras")
- **Lógica:** 
  - Primer vendedor: Se une sin problema
  - Segundo intento: Retorna el vendedor existente (sin error)

#### 🖼️ Servicio de imágenes (Cloudinary)
- **Archivo:** `scripts/setup_ec2.sh` (actualizado)
- **Cambio:** Ahora verifica automáticamente que Cloudinary esté configurado
- **Credenciales:** Ya en `.env.example` (no necesitas hacer nada más)

### 2. Frontend (Android Kotlin)

#### ✅ Contraste de formularios mejorado
- **Archivo:** 
  - `app/src/main/java/com/example/dulcemoment/ui/theme/Color.kt`
  - `app/src/main/java/com/example/dulcemoment/ui/screens/SellerModuleScreen.kt`
- **Cambios:**
  - Background: Más oscuro (de `0xFFFDFBF5` → `0xFFFAF7F0`)
  - Texto: Más oscuro (de `0xFF2A1C18` → `0xFF1F1410`)
  - Inputs: Ahora tienen `textStyle` explícito con color que contrasta
- **Resultado:** El texto es legible en los formularios

---

## 🔄 Flujo de actualización en EC2

Si necesitas actualizar la API después de nuevos cambios:

```bash
cd /tu/ruta/DulceMomentAPI/backend-fastapi
bash scripts/run_ec2.sh
```

El script **automáticamente**:
- Actualiza el código con `git pull`
- Reinstala dependencias si hay cambios
- Reinicia la API

---

## 🧪 Probar que funciona

### Crear cliente:
```bash
curl -X POST http://TU-IP-EC2:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cliente Test",
    "email": "cliente@test.com",
    "password": "123456",
    "role": "customer"
  }'
```

### Crear primer vendedor:
```bash
curl -X POST http://TU-IP-EC2:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Tienda",
    "email": "tienda@test.com",
    "password": "123456",
    "role": "store"
  }'
```

**Resultado:** Se crea el vendedor y retorna tokens.

### Intentar crear segundo vendedor:
```bash
curl -X POST http://TU-IP-EC2:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Otra Tienda",
    "email": "otra@test.com",
    "password": "123456",
    "role": "store"
  }'
```

**Resultado:** Retorna el vendedor existente (NO error). ✅

### Verificar Cloudinary:
```bash
curl http://TU-IP-EC2:8000/api/v1/media/cloudinary/status
```

**Resultado si está configurado:**
```json
{"configured": true}
```

---

## 📱 Para el Android

Asegúrate que apunta a la IP correcta de EC2:
- Busca `API_BASE_URL` en tu código
- Cambia a: `https://tu-ip-ec2.com:8000` (o la IP actual)

---

## 🛑 Si hay problemas

### Verificar logs
```bash
# Ver archivo de logs (si existe)
tail -f /var/log/dulcemoment-api.log

# O ver output de la API directamente
```

### Reiniciar la API
```bash
# Ctrl+C para parar
# Luego:
bash scripts/run_ec2.sh
```

### Verificar que el puerto 8000 esté abierto
```bash
sudo ufw allow 8000
# O en Security Group de AWS: agregar rule para puerto 8000
```

---

**¡Listo! Todo debería funcionar. Cualquier pregunta, avísame.**
