import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


class EmailService:

    @staticmethod
    def generate_otp(length=6):
        """Genera un codice OTP numerico."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def send_otp(recipient_email: str, otp_code: str, username: str) -> bool:
        """
        Invia il codice OTP via Gmail SMTP.
        Richiede in config.py:
            EMAIL_ADDRESS  = "tuaemail@gmail.com"
            EMAIL_PASSWORD = "app_password_gmail"   ← NON la password normale
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "DropBy – Codice di verifica"
            msg["From"]    = Config.EMAIL_ADDRESS
            msg["To"]      = recipient_email

            html = f"""
            <html><body>
              <h2>Ciao {username}!</h2>
              <p>Il tuo codice di verifica per <strong>DropBy</strong> è:</p>
              <h1 style="letter-spacing:8px;color:#7B1FA2;">{otp_code}</h1>
              <p>Il codice scade tra <strong>10 minuti</strong>.</p>
              <p style="color:#999;font-size:12px;">
                Se non hai richiesto questa registrazione, ignora questa email.
              </p>
            </body></html>
            """
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_ADDRESS, recipient_email, msg.as_string())

            return True

        except Exception as e:
            print(f"[EmailService] Errore invio email: {e}")
            return False

    @staticmethod
    def send_coupon_email(recipient_email: str, username: str,
                          coupon_code: str, discount: str, html_body: str) -> bool:
        """Invia l'email con il coupon riscattato via Gmail SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"DropBy – Il tuo coupon {coupon_code}"
            msg["From"]    = Config.EMAIL_ADDRESS
            msg["To"]      = recipient_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_ADDRESS, recipient_email, msg.as_string())

            return True

        except Exception as e:
            print(f"[EmailService] Errore invio coupon email: {e}")
            return False