#!/usr/bin/env python3
"""
Utilitaire pour générer une SECRET_KEY sécurisée pour ton app.
Usage: python generate_secrets.py
"""

import secrets
import sys

def generate_secret_key(length: int = 32) -> str:
    """Générer une clé secrète aléatoire sécurisée."""
    return secrets.token_hex(length)

def main():
    print("=" * 60)
    print("Générateur de SECRET_KEY pour FastAPI")
    print("=" * 60)
    print()
    
    secret_key = generate_secret_key()
    
    print("🔐 Nouvelle SECRET_KEY générée :")
    print(f"   {secret_key}")
    print()
    print("➡️  À copier dans Railway → Variables → SECRET_KEY")
    print()
    
    # Aussi générer une valeur de démonstration pour .env.example si besoin
    print("💡 Conseil: Utilise cette clé dans:")
    print("   - Railway / production")
    print("   - Ne partage JAMAIS cette clé")
    print()

if __name__ == "__main__":
    main()
