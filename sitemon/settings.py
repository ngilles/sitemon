
from pydantic import BaseSettings


class Settings(BaseSettings):
    kafka_broker: str
    postgres_dsn: str

    scan_interval: int = 60


settings = Settings(_env_file='.env')