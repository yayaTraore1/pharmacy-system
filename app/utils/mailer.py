
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USER"),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
    MAIL_FROM=os.getenv("SMTP_USER"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_create_account_email(email: str, username: str, token: str):

    link = f"{BASE_URL}/auth/create-password?token={token}"

    html = f"""
    <h2>Bienvenue</h2>

    <p>Votre compte pharmacie a été créé.</p>

    <p><b>Nom utilisateur :</b> {username}</p>

    <p>Cliquez sur ce lien pour créer votre mot de passe :</p>

    <a href="{link}">Créer mon mot de passe</a>

    <p>Ce lien expire dans 1 heure.</p>
    """

    message = MessageSchema(
        subject="Création de votre compte",
        recipients=[email],
        body=html,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_reset_password_email(email: str, token: str):

    link = f"{BASE_URL}/auth/reset-password?token={token}"

    html = f"""
    <h2>Réinitialisation du mot de passe</h2>

    <p>Cliquez sur ce lien pour choisir un nouveau mot de passe :</p>

    <a href="{link}">Réinitialiser mon mot de passe</a>

    <p>Ce lien expire dans 1 heure.</p>
    """

    message = MessageSchema(
        subject="Mot de passe oublié",
        recipients=[email],
        body=html,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)