# Configurando Cloudinary (Servicio de Imágenes) en EC2

## Paso 1: Ejecutar el setup en EC2

Cuando accedas a tu instancia EC2, ejecuta:

```bash
cd /ruta/a/tu/proyecto
bash scripts/setup_ec2.sh
```

Este script:
- ✅ Instala Python, MySQL y dependencias
- ✅ Crea el venv
- ✅ Copia `.env.example` → `.env` **con credenciales de Cloudinary ya incluidas**
- ✅ Verifica que Cloudinary esté configurado

## Paso 2: Verificar que Cloudinary esté activo

Las credenciales ya están en `.env.example`:
```
CLOUDINARY_CLOUD_NAME=root
CLOUDINARY_API_KEY=423523764535273
CLOUDINARY_API_SECRET=1M9Qb6aXwVed_hx2QwdaLLrEFCU
CLOUDINARY_FOLDER=dulcemoment
```

El script copiará estos valores automáticamente a tu `.env`.

## Paso 3: Iniciar la API

```bash
bash scripts/run_api.sh
```

## Paso 4: Probar que funciona

Haz una petición al endpoint de status de Cloudinary:

```bash
curl http://tu-ip-ec2:8000/api/v1/media/cloudinary/status
```

Deberías obtener:
```json
{"configured": true}
```

## Para subir imágenes:

```bash
curl -X POST http://tu-ip-ec2:8000/api/v1/media/cloudinary/upload-url \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://ejemplo.com/imagen.jpg"}'
```

## Si hay problemas:

1. Verifica que `.env` tenga las credenciales:
   ```bash
   grep CLOUDINARY .env
   ```

2. Reinicia la API:
   ```bash
   bash scripts/run_api.sh
   ```

3. Revisa los logs de la API para errores de Cloudinary.

---

**¡Ya está todo configurado! El servicio de imágenes debería funcionar sin necesidad de hacer nada más.**
