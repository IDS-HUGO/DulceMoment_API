from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DulceMoment API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./dulcemoment.db"
    cors_origins: str = "http://10.0.2.2:8000,http://localhost:8000"
    stripe_secret_key: str = ""
    stripe_currency: str = "mxn"
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
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
