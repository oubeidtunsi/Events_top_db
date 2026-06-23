import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    # Sicurezza applicazione
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "project-work-secret-key-2024"
    )

    # Database
    DB_HOST = os.getenv(
        "DB_HOST",
        "localhost"
    )

    DB_PORT = os.getenv(
        "DB_PORT",
        "5432"
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "events_top_db"
    )

    DB_USER = os.getenv(
        "DB_USER",
        "postgres"
    )

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        "postgres"
    )

    # SMTP Brevo
    SMTP_HOST = os.getenv(
        "SMTP_HOST",
        "smtp-relay.brevo.com"
    )

    SMTP_PORT = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    SMTP_USERNAME = os.getenv(
        "SMTP_USERNAME"
    )

    SMTP_PASSWORD = os.getenv(
        "SMTP_PASSWORD"
    )

    # Compatibilità col vecchio codice
    EMAIL_ADDRESS = os.getenv(
        "EMAIL_ADDRESS",
        SMTP_USERNAME
    )

    EMAIL_PASSWORD = os.getenv(
        "EMAIL_PASSWORD",
        SMTP_PASSWORD
    )

    OTP_EXPIRY_MINUTES = 10
