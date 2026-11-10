"""
Create a ZYNTRA root admin account from the command line.

Root admin accounts cannot be created through the website. Run this from the
backend folder with the virtual environment activated:

    python create_root_admin.py

You will be asked for a full name, email address and password (the password
is hidden while you type it).
"""
import getpass
import sys

from email_validator import EmailNotValidError, validate_email

from database import SessionLocal
from app.config import settings
from app.constants import Role
from app.models import User
from app.schemas.auth import clean_full_name, validate_password_strength
from app.services.auth_service import create_root_admin


def ask(prompt, validate):
    """Keep asking until `validate` accepts the answer."""
    while True:
        value = input(prompt).strip()
        try:
            return validate(value)
        except ValueError as error:
            print(f"  {error}")


def check_email(value):
    try:
        return validate_email(value, check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        raise ValueError("Please enter a valid email address.")


def ask_password():
    while True:
        password = getpass.getpass("Password (hidden): ")
        try:
            validate_password_strength(password)
        except ValueError as error:
            print(f"  {error}")
            continue
        if getpass.getpass("Confirm password (hidden): ") != password:
            print("  Passwords do not match. Please try again.")
            continue
        return password


def main():
    print("\nZYNTRA - create root admin account\n" + "-" * 36)
    db = SessionLocal()
    try:
        existing_admins = db.query(User).filter(User.role == Role.ROOT_ADMIN).count()
        if existing_admins:
            print(f"Warning: {existing_admins} root admin account(s) already exist.")
            if input("Create another root admin? (yes/no): ").strip().lower() not in ("y", "yes"):
                print("Cancelled. No account was created.")
                return

        full_name = ask("Full name: ", clean_full_name)
        email = ask("Email address: ", check_email)
        password = ask_password()

        try:
            user = create_root_admin(db, full_name, email, password)
        except ValueError as error:
            print(f"\nCould not create the account: {error}")
            sys.exit(1)

        print(f"\nRoot admin account created for {user.email}.")
        print(f"Log in at: {settings.frontend_url}/login")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled. No account was created.")
