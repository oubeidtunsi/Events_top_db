from repositories.auth_repository import AuthRepository
from repositories.coupons_repository import CouponsRepository
from services.email_service import EmailService
from database import Database
from datetime import datetime


class CouponsService:
    """Gestisce la logica di creazione e invio coupon via email."""

    @staticmethod
    def create_coupon(code: str, discount_value: str, description: str = None, 
                      cost_points: int = 100, max_redemptions: int = None, expires_at: datetime = None) -> int:
        """
        Crea un nuovo coupon nel sistema.

        Args:
            code (str): Codice coupon univoco (es. "SAVE20")
            discount_value (str): Valore sconto (es. "20%", "€5", "FREE_DELIVERY")
            description (str): Descrizione del coupon
            cost_points (int): Punti game necessari per riscattare
            max_redemptions (int): Numero massimo di riscatti totali
            expires_at (datetime): Data di scadenza

        Returns:
            int: ID del coupon creato

        Raises:
            ValueError: Se il codice è duplicato o parametri non validi
        """
        if not code or len(code) > 50:
            raise ValueError("Codice coupon non valido")
        
        coupon_id = CouponsRepository.create_coupon(
            code=code,
            discount_value=discount_value,
            description=description,
            cost_points=cost_points,
            max_redemptions=max_redemptions,
            expires_at=expires_at
        )
        return coupon_id

    @staticmethod
    def redeem_coupon(user_id: int, coupon_code: str) -> dict:
        """
        Riscatta un coupon per l'utente e invia email.
        Verifica punti, limite riscatti, scadenza e no-duplicati.

        Args:
            user_id (int): ID dell'utente
            coupon_code (str): Codice del coupon

        Returns:
            dict: {'message': '...', 'coupon_code': '...', 'discount_value': '...', 
                   'points_remaining': ...}

        Raises:
            ValueError: Se verifica fallisce
        """
        # 1. Recupera utente
        user = AuthRepository.find_by_id(user_id)
        if not user:
            raise ValueError("Utente non trovato")

        email_address = user.get('email')
        username = user.get('username') or 'Utente'
        if not email_address:
            raise ValueError("Email utente non trovata")

        # 2. Recupera coupon dal database
        coupon = CouponsRepository.find_by_code(coupon_code)
        if not coupon:
            raise ValueError(f"Coupon '{coupon_code}' non trovato")

        # 3. Verifica coupon attivo
        if not coupon.get('is_active'):
            raise ValueError("Coupon non è attivo")

        # 4. Verifica scadenza
        if coupon.get('expires_at'):
            from datetime import datetime
            expires_at = coupon['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at < datetime.now():
                raise ValueError("Coupon è scaduto")

        # 5. Verifica limite riscatti
        max_redemptions = coupon.get('max_redemptions')
        if max_redemptions and coupon.get('redemption_count', 0) >= max_redemptions:
            raise ValueError("Limite di riscatti raggiunto per questo coupon")

        # 6. Verifica se utente ha già riscattato questo coupon
        already_redeemed = CouponsRepository.check_user_redemption(user_id, coupon['id'])
        if already_redeemed:
            raise ValueError("Hai già riscattato questo coupon")

        # 7. Verifica punti sufficienti
        cost_points = coupon.get('cost_points', 100)
        total_score = user.get('total_score') or 0
        if total_score < cost_points:
            raise ValueError(
                f"Punti insufficienti: hai {total_score} punti, servono almeno {cost_points}"
            )

        # 8. Componi e invia email
        discount_str = coupon.get('discount_value', 'SCONTO')
        html_body = CouponsService._compose_coupon_email(username, coupon_code, discount_str)

        email_sent = EmailService.send_coupon_email(
            recipient_email=email_address,
            username=username,
            coupon_code=coupon_code,
            discount=discount_str,
            html_body=html_body
        )

        if not email_sent:
            raise ValueError("Errore durante l'invio dell'email")

        # 9. Registra il riscatto nel database
        redemption_id = CouponsRepository.redeem_coupon(user_id, coupon['id'])

        # 10. Marca email come inviata
        CouponsRepository.mark_email_sent(redemption_id)

        # 11. Decrementa punti dall'utente
        CouponsService._deduct_points(user_id, cost_points)

        return {
            'message': f'Coupon "{coupon_code}" riscattato e inviato con successo!',
            'coupon_code': coupon_code,
            'discount_value': discount_str,
            'points_deducted': cost_points,
            'points_remaining': max(0, total_score - cost_points)
        }


    @staticmethod
    def get_available_coupons() -> list:
        """
        Recupera lista di coupon disponibili (attivi e non scaduti).

        Returns:
            list: Lista di coupon disponibili
        """
        coupons = CouponsRepository.find_active_coupons()
        
        # Filtra coupon scaduti
        available = []
        for coupon in coupons:
            if coupon.get('expires_at'):
                from datetime import datetime
                expires_at = coupon['expires_at']
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if expires_at < datetime.now():
                    continue
            available.append(coupon)
        
        return available

    @staticmethod
    def get_user_history(user_id: int) -> list:
        """
        Recupera storico riscatti dell'utente.

        Args:
            user_id (int): ID dell'utente

        Returns:
            list: Storico dei coupon riscattati
        """
        return CouponsRepository.get_user_redemptions(user_id)

    @staticmethod
    def _compose_coupon_email(username: str, coupon_code: str, discount: str) -> str:
        """Compone il corpo HTML dell'email del coupon."""
        return f"""
        <html><body style="font-family: Arial, sans-serif; color: #333;">
          <h2>Ciao {username}! 🎉</h2>
          <p>Hai sbloccato un coupon speciale per DropBy!</p>
          
          <div style="background-color: #7B1FA2; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">Il tuo codice coupon:</p>
            <h1 style="margin: 10px 0; font-size: 36px; letter-spacing: 4px;">{coupon_code}</h1>
            <p style="margin: 10px 0; font-size: 18px;"><strong>Sconto: {discount}</strong></p>
          </div>
          
          <p>Usa questo codice al prossimo acquisto e goditi il tuo sconto esclusivo!</p>
          
          <p style="color: #999; font-size: 12px; margin-top: 30px;">
            Il coupon è personale e valido solo per il tuo account DropBy.
          </p>
        </body></html>
        """

    @staticmethod
    def _deduct_points(user_id: int, points: int) -> None:
        """Decrementa i punti dell'utente nel database."""
        conn = Database().get_connection()
        conn.run(
            """
            UPDATE users
            SET total_score = GREATEST(0, COALESCE(total_score, 0) - :points)
            WHERE id = :id
            """,
            points=points, id=user_id
        )
        conn.run("COMMIT")
