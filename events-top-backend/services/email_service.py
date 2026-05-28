import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


class EmailService:

    @staticmethod
    def generate_otp(length=6):
        """Genera un codice OTP numerico."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def is_configured() -> bool:
        return bool(Config.EMAIL_ADDRESS and Config.EMAIL_PASSWORD)

    @staticmethod
    def _send_html(recipient_email: str, subject: str, html_body: str) -> bool:
        if not EmailService.is_configured():
            print("[EmailService] EMAIL_ADDRESS o EMAIL_PASSWORD mancanti")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = Config.EMAIL_ADDRESS
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_ADDRESS, recipient_email, msg.as_string())

            return True
        except Exception as e:
            print(f"[EmailService] Errore invio email: {e}")
            return False

    @staticmethod
    def send_otp(recipient_email: str, otp_code: str, username: str) -> bool:
        html = f"""
        <html><body>
          <h2>Ciao {username}!</h2>
          <p>Il tuo codice di verifica per <strong>DropBy</strong> e':</p>
          <h1 style="letter-spacing:8px;color:#7B1FA2;">{otp_code}</h1>
          <p>Il codice scade tra <strong>10 minuti</strong>.</p>
          <p style="color:#999;font-size:12px;">
            Se non hai richiesto questa registrazione, ignora questa email.
          </p>
        </body></html>
        """
        return EmailService._send_html(
            recipient_email,
            "DropBy - Codice di verifica",
            html
        )

    @staticmethod
    def send_coupon_email(recipient_email: str, username: str,
                          coupon_code: str, discount: str, html_body: str) -> bool:
        return EmailService._send_html(
            recipient_email,
            f"DropBy - Il tuo coupon {coupon_code}",
            html_body
        )
