#!/bin/bash
# Script para eliminar y recrear la base de datos SQLite para pruebas limpias

DB_FILE="dulcemoment.db"

if [ -f "$DB_FILE" ]; then
    echo "Eliminando base de datos existente: $DB_FILE"
    rm "$DB_FILE"
else
    echo "No existe base de datos previa."
fi

# Ejecutar migraciones automáticas (si usas Alembic, ajusta aquí)
# Para SQLAlchemy puro:
python3 -c "from app.db.database import Base, engine; Base.metadata.create_all(engine)"

echo "Base de datos recreada vacía."
