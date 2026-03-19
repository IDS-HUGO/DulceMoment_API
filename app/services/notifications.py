from typing import Iterable

from app.core.config import settings
from app.db.models import DeviceToken

_firebase_app_ready = False


def _initialize_firebase() -> bool:
    global _firebase_app_ready
    if _firebase_app_ready:
        return True

    if not settings.firebase_service_account_path:
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(settings.firebase_service_account_path)
        firebase_admin.initialize_app(cred)
        _firebase_app_ready = True
        return True
    except Exception:
        return False


def send_push_to_tokens(tokens: Iterable[str], title: str, body: str, data: dict[str, str] | None = None) -> int:
    token_list = [token for token in tokens if token]
    if not token_list:
        return 0

    if not _initialize_firebase():
        return len(token_list)

    from firebase_admin import messaging

    sent = 0
    for token in token_list:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )
            messaging.send(message)
            sent += 1
        except Exception:
            continue
    return sent


def tokens_for_user_ids(db, user_ids: list[int]) -> list[str]:
    rows = db.query(DeviceToken).filter(DeviceToken.user_id.in_(user_ids)).all()
    return [row.token for row in rows]
