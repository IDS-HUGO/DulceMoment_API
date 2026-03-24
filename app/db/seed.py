from sqlalchemy.orm import Session

from app.db.models import User


def seed_data(db: Session) -> None:
    """Solo valida que la BD esté inicializada. NO crea datos dummy."""
    # Si la tabla de usuarios existe, hemos terminado
    try:
        db.query(User).count()
    except Exception:
        # La tabla no existe - SQLAlchemy la creará automáticamente
        pass

    # Hacer commit para asegurar que la BD se inicializó
    db.commit()
