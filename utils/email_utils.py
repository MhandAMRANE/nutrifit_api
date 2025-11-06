import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAIL_USERNAME = "mhandamrane25@gmail.com"
MAIL_PASSWORD = "phsslvujiztfanba"  # ton mot de passe d'application sans espaces
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_confirmation_email(to_email: str, code: str):
    subject = "Votre code de confirmation - NutriFit"
    body = f"""
    <html>
    <body>
        <h2>Bienvenue sur NutriFit !</h2>
        <p>Merci pour votre inscription.</p>
        <p>Voici votre code de confirmation :</p>
        <h2 style="color:blue;">{code}</h2>
        <p>Ce code expire dans 15 minutes.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = MAIL_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email envoyé à {to_email}")
    except Exception as e:
        print(f" Erreur lors de l'envoi du mail : {e}")
