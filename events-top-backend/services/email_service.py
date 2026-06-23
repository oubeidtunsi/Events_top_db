import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


class EmailService:

    SMTP_TIMEOUT_SECONDS = 20
    last_error = None

    @staticmethod
    def generate_otp(length=6):
        return ''.join(
            random.choices(
                string.digits,
                k=length
            )
        )

    @staticmethod
    def is_configured():
        return bool(
            Config.EMAIL_ADDRESS and
            Config.EMAIL_PASSWORD
        )

    @staticmethod
    def get_last_error():
        return EmailService.last_error or "Errore sconosciuto"

    @staticmethod
    def _send_html(recipient_email, subject, html_body):

        EmailService.last_error = None

        if not EmailService.is_configured():

            EmailService.last_error = (
                "EMAIL_ADDRESS o EMAIL_PASSWORD mancanti"
            )

            print(
                f"[EmailService] {EmailService.last_error}"
            )

            return False

        msg = MIMEMultipart("alternative")

        msg["Subject"] = subject
        msg["From"] = Config.EMAIL_ADDRESS
        msg["To"] = recipient_email

        msg.attach(
            MIMEText(
                html_body,
                "html"
            )
        )

        payload = msg.as_string()

        for port in EmailService._smtp_ports():

            if EmailService._send_with_port(
                recipient_email,
                payload,
                port
            ):

                return True

        return False

    @staticmethod
    def _smtp_ports():
        return [Config.SMTP_PORT]

    @staticmethod
    def _send_with_port(
        recipient_email,
        payload,
        port
    ):

        try:

            print(
                f"[EmailService] Connessione a {Config.SMTP_HOST}:{port}"
            )

            server = smtplib.SMTP_SSL(
                Config.SMTP_HOST,
                int(port),
                timeout=EmailService.SMTP_TIMEOUT_SECONDS
            )

            with server:

                server.login(
                    Config.EMAIL_ADDRESS,
                    Config.EMAIL_PASSWORD
                )

                server.sendmail(
                    Config.EMAIL_ADDRESS,
                    recipient_email,
                    payload
                )

                print(
                    "[EmailService] Email inviata"
                )

            return True

        except Exception as e:

            EmailService.last_error = (
                f"{Config.SMTP_HOST}:{port} - {str(e)}"
            )

            print(
                f"[EmailService] {EmailService.last_error}"
            )

            return False

    @staticmethod
    def send_otp(
        recipient_email,
        otp_code,
        username
    ):

        html = f"""
        <html>
        <body>

        <h2>Ciao {username}!</h2>

        <p>
        Il tuo codice verifica per
        <strong>DropBy</strong> è:
        </p>

        <h1 style="letter-spacing:8px;color:#7B1FA2;">
        {otp_code}
        </h1>

        <p>
        Il codice scade tra
        <strong>10 minuti</strong>
        </p>

        <p style="color:#999;font-size:12px;">
        Se non hai richiesto questa registrazione,
        ignora questa email.
        </p>

        </body>
        </html>
        """

        return EmailService._send_html(
            recipient_email,
            "DropBy - Codice verifica",
            html
        )

    @staticmethod
    def send_coupon_email(
        recipient_email,
        username,
        coupon_code,
        discount,
        html_body
    ):

        return EmailService._send_html(
            recipient_email,
            f"DropBy - Coupon {coupon_code}",
            html_body
        )
