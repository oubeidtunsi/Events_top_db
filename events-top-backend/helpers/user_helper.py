import re
from datetime import datetime


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_username(username):
    pattern = r"^[a-zA-Z0-9._-]{3,30}$"
    return re.match(pattern, username) is not None


def is_valid_birth_date(date_of_birth):
    try:
        parsed_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        return False

    return parsed_date < datetime.today().date()


def normalize_user_payload(data):
    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or data.get("surname") or "").strip()
    full_name = (data.get("name") or "").strip()

    if full_name and (not first_name and not last_name):
        parts = full_name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    if not full_name:
        full_name = " ".join(part for part in [first_name, last_name] if part).strip()

    return {
        "firstName": first_name,
        "lastName": last_name,
        "name": full_name,
        "username": (data.get("username") or "").strip(),
        "email": (data.get("email") or "").strip(),
        "dateOfBirth": (data.get("dateOfBirth") or data.get("birthDate") or "").strip(),
        "password": data.get("password") or "",
    }


def serialize_public_user(user):
    return {
        "id": user["id"],
        "firstName": user["first_name"],
        "lastName": user["last_name"],
        "name": user["full_name"],
        "username": user["username"],
        "email": user["email"],
        "dateOfBirth": user["date_of_birth"].isoformat(),
    }
