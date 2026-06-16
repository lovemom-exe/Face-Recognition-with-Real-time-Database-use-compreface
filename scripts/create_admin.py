from __future__ import annotations

import argparse
from getpass import getpass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import session_scope
from backend.app.models import User
from backend.app.utils.password import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an ADMIN user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--full-name", default="System Admin")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    password = args.password or getpass("Password: ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    with session_scope() as db:
        user = db.query(User).filter(User.username == args.username).first()
        if not user:
            user = User(username=args.username, full_name=args.full_name, role="ADMIN")
            db.add(user)
        user.email = args.email
        user.full_name = args.full_name
        user.role = "ADMIN"
        user.status = "ACTIVE"
        user.is_active = True
        user.password_hash = hash_password(password)
        print(f"Admin user ready: {args.username}")


if __name__ == "__main__":
    main()
