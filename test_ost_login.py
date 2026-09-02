"""Interactive Standard Bank OST login test.

Usage:
    python test_ost_login.py

Prompts for your OST username and password (password is hidden while typing),
then attempts a real login against the live portal. Nothing is logged or saved.
"""
from getpass import getpass

from jse_adapter import StandardBankOSTAdapter


def main():
    print("Standard Bank OST login test")
    print("=" * 60)
    username = input("OST username: ").strip()
    password = getpass("OST password (hidden): ")

    if not username or not password:
        print("Username and password are both required.")
        return

    adapter = StandardBankOSTAdapter(username=username, password=password)
    print("\nAttempting login against live portal...")

    try:
        ok = adapter.login()
    except Exception as exc:
        print(f"Login raised an error: {type(exc).__name__}: {exc}")
        return

    if ok:
        print("LOGIN SUCCESSFUL — authenticated session established.")
        try:
            summary = adapter.get_portfolio_summary()
            print(f"Portfolio summary (stub): {summary}")
        except Exception as exc:
            print(f"Portfolio fetch not implemented yet: {exc}")
    else:
        print("LOGIN FAILED — portal rejected the credentials or the flow changed.")
        print("Possible causes: wrong credentials, OTP/2FA required, or updated form contract.")


if __name__ == "__main__":
    main()
