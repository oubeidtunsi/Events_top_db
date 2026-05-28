import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


class EmailService:
    SMTP_TIMEOUT_SECONDS = 10
    last_error = None

    @staticmethod
    def generate_otp(length=6):
        """Genera un codice OTP numerico."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def is_configured() -> bool:
        return bool(Config.EMAIL_ADDRESS and Config.EMAIL_PASSWORD)

    @staticmethod
    def get_last_error() -> str:
        return EmailService.last_error or "errore sconosciuto"

    @staticmethod
    def _send_html(recipient_email: str, subject: str, html_body: str) -> bool:
        EmailService.last_error = None
        if not EmailService.is_configured():
            EmailService.last_error = "EMAIL_ADDRESS o EMAIL_PASSWORD mancanti"
            print(f"[EmailService] {EmailService.last_error}")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = Config.EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_body, "html"))
        payload = msg.as_string()

        for port in EmailService._smtp_ports():
            if EmailService._send_with_port(recipient_email, payload, port):
                return True

        return False

    @staticmethod
    def _smtp_ports():
        ports = [Config.SMTP_PORT]
        if Config.SMTP_HOST == "smtp.gmail.com":
            for fallback_port in (587, 465):
                if fallback_port not in ports:
                    ports.append(fallback_port)
        return ports

    @staticmethod
    def _send_with_port(recipient_email: str, payload: str, port: int) -> bool:
        try:
            if int(port) == 465:
                server = smtplib.SMTP_SSL(
                    Config.SMTP_HOST,
                    port,
                    timeout=EmailService.SMTP_TIMEOUT_SECONDS
                )
            else:
                server = smtplib.SMTP(
                    Config.SMTP_HOST,
                    port,
                    timeout=EmailService.SMTP_TIMEOUT_SECONDS
                )

            with server:
                if int(port) != 465:
                    server.starttls()
                server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_ADDRESS, recipient_email, payload)

            return True
        except Exception as e:
            EmailService.last_error = f"{Config.SMTP_HOST}:{port} - {e}"
            print(f"[EmailService] Errore invio email su {EmailService.last_error}")
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
