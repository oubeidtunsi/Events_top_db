import os  # Importa il modulo standard per leggere le variabili ambiente del sistema operativo

from dotenv import load_dotenv  # Importa la funzione che carica le variabili dal file .env in locale

load_dotenv()  # Carica le variabili ambiente definite nel file .env quando lavori in locale


class Config:  # Definisce una classe di configurazione centralizzata per il backend

    SECRET_KEY = os.getenv("SECRET_KEY", "project-work-secret-key-2024")  # Legge la chiave segreta dall'ambiente oppure usa un valore locale di fallback

    DB_HOST = os.getenv("DB_HOST", "localhost")  # Legge l'host del database oppure usa localhost in sviluppo locale

    DB_PORT = os.getenv("DB_PORT", "5432")  # Legge la porta del database oppure usa 5432 come default PostgreSQL

    DB_NAME = os.getenv("DB_NAME", "events_top_db")  # Legge il nome del database oppure usa quello locale

    DB_USER = os.getenv("DB_USER", "postgres")  # Legge l'utente database oppure usa postgres in locale

    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")  # Legge la password database oppure usa postgres in locale

    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS") or os.getenv("SMTP_USERNAME")  # Legge l'indirizzo email mittente dalle variabili ambiente

    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")  # Legge la password app dell'email dalle variabili ambiente
    
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")  # Host SMTP usato per inviare email

    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # Porta SMTP usata per STARTTLS

    OTP_EXPIRY_MINUTES = 10  # Imposta la durata del codice OTP in minuti
