from database import Database
from helpers.format_helper import dict_format, dict_format_single

_DATE_COALESCE = """COALESCE(
        (SELECT to_char(MIN(eri.show_date), 'YYYY-MM-DD')
         FROM event_replicas eri
         WHERE eri.event_id = e.id AND eri.show_date >= NOW()),
        NULLIF(e.event_date::TEXT, '')
    ) AS event_date"""

_CITY_COALESCE = """COALESCE(
        NULLIF(e.city, ''),
        (SELECT li.city FROM event_replicas eri
         JOIN locations li ON li.id = eri.location_id
         WHERE eri.event_id = e.id ORDER BY eri.show_date LIMIT 1)
    ) AS event_city"""


class EventProposalRepository:

    @staticmethod
    def create(from_user_id, to_user_id, event_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "INSERT INTO event_proposals (from_user_id, to_user_id, event_id) "
            "VALUES (:f, :t, :e) RETURNING id",
            f=from_user_id, t=to_user_id, e=event_id
        )
        conn.run("COMMIT")
        return rows[0][0] if rows else None

    @staticmethod
    def find_pending_for_user(user_id):
        """Proposte ricevute ancora in attesa (usato internamente)."""
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """SELECT p.id, p.status, p.event_id, p.from_user_id
               FROM event_proposals p
               WHERE p.to_user_id = :uid AND p.status = 'pending'""",
            uid=user_id
        )
        return dict_format(conn, rows)

    @staticmethod
    def find_by_event_and_to_user(event_id, to_user_id):
        """Trova la proposta pending identificata da (event_id, to_user_id)."""
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """SELECT id, from_user_id, status
               FROM event_proposals
               WHERE event_id = :eid AND to_user_id = :uid AND status = 'pending'
               ORDER BY created_at DESC LIMIT 1""",
            eid=event_id, uid=to_user_id
        )
        return dict_format_single(conn, rows)

    @staticmethod
    def find_all_for_user(user_id):
        """Tutte le proposte (inviate e ricevute) con dati utenti ed evento."""
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            f"""SELECT p.id, p.status, p.created_at,
                      p.from_user_id, uf.username AS from_username,
                      p.to_user_id,   ut.username AS to_username,
                      e.id AS event_id, e.title AS event_title,
                      {_DATE_COALESCE},
                      {_CITY_COALESCE}
               FROM event_proposals p
               JOIN users  uf ON p.from_user_id = uf.id
               JOIN users  ut ON p.to_user_id   = ut.id
               JOIN events e  ON p.event_id     = e.id
               WHERE p.from_user_id = :uid OR p.to_user_id = :uid
               ORDER BY p.created_at DESC""",
            uid=user_id
        )
        return dict_format(conn, rows)

    @staticmethod
    def find_sent_with_responses(from_user_id):
        """
        Proposte inviate da from_user_id, arricchite con l'emoji di risposta
        dell'amico proveniente da event_responses (NULL se ancora pending).
        """
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            f"""SELECT p.id, p.status, p.created_at,
                      p.to_user_id,  ut.username AS to_username,
                      e.id AS event_id, e.title AS event_title,
                      {_DATE_COALESCE},
                      {_CITY_COALESCE},
                      er.response AS response_emoji
               FROM event_proposals p
               JOIN users  ut ON p.to_user_id = ut.id
               JOIN events e  ON p.event_id   = e.id
               LEFT JOIN event_responses er
                   ON er.event_id = p.event_id AND er.user_id = p.to_user_id
               WHERE p.from_user_id = :uid
               ORDER BY p.created_at DESC""",
            uid=from_user_id
        )
        return dict_format(conn, rows)

    # event_proposals usa 'accepted'/'declined', event_responses usa 'accept'/'decline'
    _RESPONSE_VALUE = {'accepted': 'accept', 'declined': 'decline', 'maybe': 'maybe'}

    @staticmethod
    def respond_and_save(proposal_id, status, user_id, event_id, emoji):
        """
        Operazione atomica su un'unica connessione:
        1. Aggiorna event_proposals.status  (accepted/declined/maybe)
        2. Sostituisce la riga in event_responses (accept/decline/maybe)
        Un solo COMMIT garantisce che o tutto passa o niente viene persistito.
        """
        response_val = EventProposalRepository._RESPONSE_VALUE.get(status, status)
        db = Database()
        conn = db.get_connection()
        conn.run(
            "UPDATE event_proposals SET status = :status WHERE id = :id",
            status=status, id=proposal_id
        )
        conn.run(
            "DELETE FROM event_responses WHERE user_id = :uid AND event_id = :eid",
            uid=user_id, eid=event_id
        )
        conn.run(
            "INSERT INTO event_responses (event_id, user_id, response) "
            "VALUES (:eid, :uid, :resp)",
            eid=event_id, uid=user_id, resp=response_val
        )
        conn.run("COMMIT")
