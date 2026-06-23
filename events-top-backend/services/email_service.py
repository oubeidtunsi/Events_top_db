import os
import random
import string
import requests

from config import Config


class EmailService:

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
            os.getenv("BREVO_API_KEY")
        )

    @staticmethod
    def get_last_error():

        return EmailService.last_error or "Errore sconosciuto"

    @staticmethod
    def _send_html(
        recipient_email,
        subject,
        html_body
    ):

        EmailService.last_error = None

        api_key = os.getenv(
            "BREVO_API_KEY"
        )

        if not api_key:

            EmailService.last_error = (
                "BREVO_API_KEY mancante"
            )

            return False

        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "name": "DropBy",
                "email": Config.EMAIL_ADDRESS
            },
            "to": [
                {
                    "email": recipient_email
                }
            ],
            "subject": subject,
            "htmlContent": html_body
        }

        try:

            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers=headers,
                json=payload,
                timeout=20
            )

            if response.status_code in [200, 201]:

                return True

            EmailService.last_error = response.text

            print(
                f"[EmailService] {response.text}"
            )

            return False

        except Exception as e:

            EmailService.last_error = str(e)

            print(
                f"[EmailService] {str(e)}"
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
        <h2>Ciao {username}</h2>
        <p>Il tuo codice OTP:</p>
        <h1>{otp_code}</h1>
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
