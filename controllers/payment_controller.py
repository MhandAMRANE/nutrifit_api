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

# ──────────────────────────────────────────────────────────────
# Mapping officiel : numéro de carte test Stripe → payment method
# Source : https://docs.stripe.com/testing#cards
# Seuls ces numéros exacts seront acceptés.
# ──────────────────────────────────────────────────────────────
TEST_CARD_TO_PAYMENT_METHOD = {
    "4242424242424242": "pm_card_visa",                        # ✅ Succès
    "4000056655665556": "pm_card_visa_debit",                  # ✅ Succès (Visa Debit)
    "5555555555554444": "pm_card_mastercard",                  # ✅ Succès (Mastercard)
    "4000000000000077": "pm_card_bypassPending",               # ✅ Succès immédiat
    "4000000000009995": "pm_card_visa_chargeDeclined",         # ❌ Refusé (fonds insuffisants)
    "4000000000000002": "pm_card_chargeDeclined",              # ❌ Refusé (générique)
    "4000000000009987": "pm_card_chargeDeclinedLostCard",      # ❌ Carte perdue
    "4000000000009979": "pm_card_chargeDeclinedStolenCard",    # ❌ Carte volée
    "4000002500003155": "pm_card_threeDSecureRequired",        # 🔐 3D Secure obligatoire
    "4000002760003184": "pm_card_authenticationRequired",      # 🔐 Authentification requise
}


def create_and_confirm_donation(
    amount_cents: int,
    card_number: str,
    currency: str = "eur",
) -> dict:
    """
    Crée ET confirme un PaymentIntent Stripe server-side.

    Le numéro de carte est mappé vers un payment method de test Stripe officiel.
    Si le numéro ne correspond à aucune carte de test → erreur 400.
    Le résultat (succès / refus) vient directement de Stripe.
    """
    # 1. Valider le montant
    if amount_cents not in ALLOWED_AMOUNTS:
        raise HTTPException(
            status_code=400,
            detail=f"Montant invalide. Montants autorisés (en centimes) : {list(ALLOWED_AMOUNTS.keys())}",
        )

    # 2. Nettoyer et valider le numéro de carte
    clean_card = card_number.replace(" ", "").replace("-", "")

    if clean_card not in TEST_CARD_TO_PAYMENT_METHOD:
        raise HTTPException(
            status_code=400,
            detail=(
                "Carte invalide. Utilise uniquement les cartes de test Stripe officielles. "
                "Exemples : 4242 4242 4242 4242 (succès), 4000 0000 0000 9995 (refusé)."
            ),
        )

    payment_method_id = TEST_CARD_TO_PAYMENT_METHOD[clean_card]

    # 3. Créer + confirmer le PaymentIntent via Stripe (tout server-side)
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            payment_method=payment_method_id,
            confirm=True,
            # return_url requis pour les cartes nécessitant une redirection (3DS)
            return_url="https://nutrifit.app/donation/return",
            metadata={
                "mode": "sandbox",
                "description": "NutriFit - Donation simulée (test)",
            },
        )

        # Statuts Stripe possibles après confirmation :
        # "succeeded"         → paiement réussi
        # "requires_action"   → 3D Secure nécessaire (simulé comme succès en test)
        # "requires_payment_method" → carte refusée
        success = intent.status in ("succeeded", "requires_action")

        return {
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency,
            "success": success,
            "error": None,
        }

    except stripe.error.CardError as e:
        # Stripe a refusé la carte (ex: fonds insuffisants, carte perdue...)
        err = e.error
        return {
            "payment_intent_id": None,
            "status": "failed",
            "amount": amount_cents,
            "currency": currency,
            "success": False,
            "error": err.message if hasattr(err, "message") else str(e),
            "decline_code": err.decline_code if hasattr(err, "decline_code") else None,
        }

    except stripe.error.AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Clé Stripe invalide. Vérifie ta STRIPE_SECRET_KEY dans le .env",
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Erreur Stripe : {str(e)}")