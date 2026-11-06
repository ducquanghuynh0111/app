"""Reset the local owner password from an interactive terminal.

The password is never accepted as a command argument or printed to stdout.
"""

import getpass
import sys

import app


def main() -> int:
    if not sys.stdin.isatty():
        print("Run this command in an interactive PowerShell window.")
        return 2
    if not app.DB.is_file():
        print("Restaurant database not found. Start the web app and create the owner first.")
        return 2

    with app.db() as con:
        owner = con.execute(
            "SELECT id FROM users WHERE username=? AND role=? AND active=1",
            ("owner", "owner"),
        ).fetchone()
        if owner is None:
            print("Active owner account not found.")
            return 2

    try:
        password = getpass.getpass("New owner password (12-200 characters): ")
        confirmation = getpass.getpass("Repeat new password: ")
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 1
    if password != confirmation:
        print("Passwords did not match; nothing changed.")
        return 1
    if not 12 <= len(password) <= 200 or password != password.strip():
        print("Use 12-200 characters without leading or trailing spaces.")
        return 1

    with app.db() as con:
        result = con.execute(
            "UPDATE users SET password_hash=? WHERE id=? AND username=? AND role=? AND active=1",
            (app.password_hash(password), owner["id"], "owner", "owner"),
        )
        if result.rowcount != 1:
            print("Owner account changed during reset; nothing changed.")
            return 1
        con.execute("DELETE FROM sessions WHERE user_id=?", (owner["id"],))
        app.audit(con, owner["id"], "password-reset-local", "users", owner["id"])
    print("Owner password updated. Existing sessions were signed out.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
