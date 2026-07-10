import sys

from sqlalchemy import create_engine, text

from core.config import config

sync_db_url = config.DATABASE_URL.replace("+aiomysql", "+pymysql")


def set_role(email: str, role: str) -> None:
    engine = create_engine(sync_db_url)
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE users SET role = :role WHERE email = :email"),
            {"role": role, "email": email},
        )
        if result.rowcount == 0:
            print(f"No user found with email '{email}'. Register them first.")
            sys.exit(1)

    print(f"User '{email}' is now '{role}'. Refresh the app (or re-fetch /auth/me) to apply.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email> [--revoke]")
        sys.exit(1)
    target_email = sys.argv[1]
    target_role = "owner" if "--revoke" in sys.argv[2:] else "admin"
    set_role(target_email, target_role)
