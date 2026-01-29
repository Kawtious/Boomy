import os

from dotenv import load_dotenv
from vault.exceptions.invalid_environment_variable import InvalidEnvironmentVariable
from vault.exceptions.missing_environment_variable import MissingEnvironmentVariable

load_dotenv()


class Config:
    PROJECT_ROOT = os.getenv("PROJECT_ROOT")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    if not PROJECT_ROOT:
        raise MissingEnvironmentVariable("PROJECT_ROOT")

    env_path = None

    match ENVIRONMENT.lower():
        case "development":
            env_path = os.path.join(PROJECT_ROOT, ".env.dev")
        case "development-remote":
            env_path = os.path.join(PROJECT_ROOT, ".env.dev.remote")
        case "production":
            env_path = os.path.join(PROJECT_ROOT, ".env.prod")

    if not os.path.isfile(env_path):
        raise FileNotFoundError(f"Environment file not found: {env_path}")

    load_dotenv(env_path)

    BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    OWNER_ID = os.getenv("OWNER_ID")
    DATABASE_CONNECTION = os.getenv("DATABASE_CONNECTION")

    if not BOT_TOKEN:
        raise MissingEnvironmentVariable("DISCORD_BOT_TOKEN")
    if not OWNER_ID:
        raise MissingEnvironmentVariable("OWNER_ID")
    if not OWNER_ID.isdigit():
        raise InvalidEnvironmentVariable("OWNER_ID", "must be a numeric Discord user ID.")
    if not DATABASE_CONNECTION:
        raise MissingEnvironmentVariable("DATABASE_CONNECTION")

    CAFE_API = os.getenv("CAFE_API", "http://localhost:8000")
    BOOMY_API = os.getenv("BOOMY_API", "http://localhost:8001")
    BERRY_API = os.getenv("BERRY_API", "http://localhost:8002")
    JAX_API = os.getenv("JAX_API", "http://localhost:8003")

    OWNER_ID = int(OWNER_ID)

    ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
