from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./arinc429_dev.db"
    serial_enabled: bool = False
    serial_port: str = "/dev/ttyUSB0"
    serial_baudrate: int = 100_000
    audio_enabled: bool = False
    audio_sample_rate: int = 44_100
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
