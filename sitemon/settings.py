
from pydantic import BaseSettings


class Settings(BaseSettings):
    kafka_broker: str
    postgres_dsn: str


settings = Settings(_env_file='.env')