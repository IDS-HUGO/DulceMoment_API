from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DulceMoment API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./dulcemoment.db"
    cors_origins: str = "*"
    stripe_secret_key: str = ""
    stripe_currency: str = "mxn"
    stripe_connected_account_id: str = ""
    stripe_webhook_secret: str = ""
    platform_fee_percent: float = 5.0
    payment_provider: str = "mercadopago"
    mercadopago_public_key: str = ""
    mercadopago_access_token: str = ""
    mercadopago_client_id: str = ""
    mercadopago_client_secret: str = ""
    enable_fake_payments: bool = True
    firebase_service_account_path: str = ""
    jwt_secret_key: str = "dulcemoment-change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    jwt_refresh_expire_minutes: int = 60 * 24 * 30
    cloudinary_url: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_folder: str = "dulcemoment"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_allow_all(self) -> bool:
        value = self.cors_origins.strip()
        return value == "*" or value.lower() == "all"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
