#!/usr/bin/env python3
"""
Add provider credentials to the database with encryption
Usage: python3 scripts/add_provider_credentials.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.provider_credentials import ProviderCredential, ProviderType
from utils.encryption import encrypt_api_key
import getpass

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:oeqioGrcPaPHGkbLSvpOiVubZEuKSiJS@switchback.proxy.rlwy.net:24546/railway"
)

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def add_credential(
    organization_id: str,
    provider: str,
    api_key: str,
    credential_name: str,
    api_base: str = None
):
    """
    Add a provider credential with encrypted API key
    """
    session = Session()

    try:
        # Validate provider
        try:
            provider_enum = ProviderType(provider.lower())
        except ValueError:
            print(f"❌ Invalid provider: {provider}")
            print(f"   Must be one of: openai, anthropic, gemini, fireworks")
            return False

        # Create credential
        credential = ProviderCredential(
            organization_id=organization_id,
            provider=provider_enum,
            credential_name=credential_name,
            api_base=api_base,
            is_active=True
        )

        # Encrypt and set API key
        print(f"🔐 Encrypting {provider} API key...")
        credential.set_api_key(api_key)

        # Save to database
        session.add(credential)
        session.commit()

        print(f"✅ Successfully added {provider} credential for organization '{organization_id}'")
        print(f"   Credential ID: {credential.credential_id}")
        print(f"   Name: {credential_name}")
        print(f"   Status: Active")

        return True

    except Exception as e:
        session.rollback()
        print(f"❌ Error adding credential: {str(e)}")
        return False

    finally:
        session.close()


def main():
    print("=" * 60)
    print("Provider Credentials Setup")
    print("=" * 60)
    print()

    # Organization ID
    organization_id = "ktg"
    print(f"Organization ID: {organization_id}")
    print()

    # Track which providers to add
    providers_to_add = []

    # Ask which providers to add
    print("Which providers do you want to add credentials for?")
    print()

    for provider in ["openai", "anthropic", "gemini", "fireworks"]:
        response = input(f"Add {provider.upper()}? (y/n): ").strip().lower()
        if response == 'y':
            providers_to_add.append(provider)

    print()

    if not providers_to_add:
        print("No providers selected. Exiting.")
        return

    # Add credentials for each provider
    for provider in providers_to_add:
        print("-" * 60)
        print(f"Adding {provider.upper()} credential")
        print("-" * 60)

        # Get API key (hidden input)
        api_key = getpass.getpass(f"Enter {provider.upper()} API key: ")

        if not api_key:
            print(f"⚠️  No API key provided for {provider}, skipping...")
            print()
            continue

        # Optional API base
        api_base = None
        if provider in ["openai"]:
            custom_base = input(f"Custom API base URL (press Enter to skip): ").strip()
            if custom_base:
                api_base = custom_base

        # Credential name
        credential_name = f"Production {provider.upper()} Key"

        # Add to database
        success = add_credential(
            organization_id=organization_id,
            provider=provider,
            api_key=api_key,
            credential_name=credential_name,
            api_base=api_base
        )

        print()

    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)

    # Show summary
    session = Session()
    try:
        credentials = session.query(ProviderCredential).filter(
            ProviderCredential.organization_id == organization_id,
            ProviderCredential.is_active == True
        ).all()

        print()
        print("Active credentials:")
        for cred in credentials:
            print(f"  • {cred.provider.value}: {cred.credential_name}")

    finally:
        session.close()


if __name__ == "__main__":
    # Check for encryption key
    if not os.environ.get("ENCRYPTION_KEY"):
        print("⚠️  WARNING: ENCRYPTION_KEY environment variable not set.")
        print("   Using development default key (NOT SECURE FOR PRODUCTION).")
        print()
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Exiting. Set ENCRYPTION_KEY environment variable and try again.")
            sys.exit(1)
        print()

    main()
