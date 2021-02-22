from typing import Optional

from pydantic import BaseSettings, FilePath


class Settings(BaseSettings):
    kafka_broker: str
    kafka_auth_ca: Optional[FilePath]
    kafka_access_key: Optional[FilePath]
    kafka_access_crt: Optional[FilePath]
    postgres_dsn: str

    scan_interval: int = 60


settings = Settings(_env_file='.env')
