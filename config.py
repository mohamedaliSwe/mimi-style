import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class Config:
    """Defines a base class configurations"""

    SECRET_KEY = os.environ.get("SECRET_KEY")

    # JWT Configurations
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "JWT_Dev_Key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # SQLALCHEMY Configurations
    SQLALCHEMY_TRACK_MODIFICATIONS = bool(
        os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")
    )

    # Flask mail configurations
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_TLS = bool(os.environ.get("MAIL_USE_TLS"))
    MAIL_USE_SSL = bool(os.environ.get("MAIL_USE_SSL"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")


class DevConfig(Config):
    """Defines Development configurations"""

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "dev.db")
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestConfig(Config):
    """Defines Testing Configurations"""

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "test.db")
    DEBUG = True
    TESTING = True
    SQLALCHEMY_ECHO = True


class ProdConfig(Config):
    """Defines Production Configuration"""

    pass
