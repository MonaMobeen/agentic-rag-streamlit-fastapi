import json
import os

import bcrypt


USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def signup(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()

    if not username or not password:
        return False, "Username and password cannot be empty."

    users = _load_users()

    if username in users:
        return False, "This username is already taken."

    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    users[username] = hashed.decode("utf-8")

    _save_users(users)

    return True, "Account created successfully."


def login(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()

    users = _load_users()

    if username not in users:
        return False, "No account found with this username."

    stored_hash = users[username].encode("utf-8")

    if bcrypt.checkpw(
        password.encode("utf-8"),
        stored_hash
    ):
        return True, "Login successful."

    return False, "Incorrect password."


# Test code
if __name__ == "__main__":
    print(signup("mona", "test123"))
    print(login("mona", "test123"))
    print(login("mona", "wrongpass"))