import stripe
import os
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Clé secrète Stripe (mode sandbox/test)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_REMPLACE_PAR_TA_CLE_STRIPE")

# Montants autorisés en centimes (EUR)
ALLOWED_AMOUNTS = {
    500: "5€",
    1000: "10€",
    2000: "20€",
    5000: "50€",
}


def create_payment_intent(amount_cents: int, currency: str = "eur") -> dict:
    """
    Crée un PaymentIntent Stripe en mode sandbox.
    Retourne le client_secret pour confirmer côté frontend.
    """
    if amount_cents not in ALLOWED_AMOUNTS:
        raise HTTPException(
            status_code=400,
            detail=f"Montant invalide. Montants autorisés : {list(ALLOWED_AMOUNTS.keys())}",
        )

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            payment_method_types=["card"],
            metadata={
                "mode": "sandbox",
                "description": "NutriFit - Donation simulée (test)",
            },
        )
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount_cents,
            "currency": currency,
            "status": intent.status,
        }
    except stripe.error.AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Clé Stripe invalide. Vérifie ta STRIPE_SECRET_KEY dans le .env",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Erreur Stripe : {str(e)}")


def confirm_payment_intent(payment_intent_id: str) -> dict:
    """
    Récupère le statut d'un PaymentIntent (pour vérification après confirmation côté client).
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Erreur Stripe : {str(e)}")