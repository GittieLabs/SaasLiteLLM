#!/usr/bin/env python3
"""
Safe script to reset admin users without affecting other data.

This script:
- Deletes only admin_users, admin_sessions, and admin_audit_log tables
- Leaves all other data intact (organizations, teams, model_groups, credits, jobs, etc.)
- Can be run safely in production environments

Usage:
    python3 scripts/reset_admin_users.py [--confirm]
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("❌ Error: DATABASE_URL environment variable not set")
    print("Set it using: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

# Create engine
engine = create_engine(database_url)


def reset_admin_users(confirm: bool = False):
    """
    Reset admin users by clearing admin-related tables only.

    Args:
        confirm: If True, proceed without prompting
    """
    if not confirm:
        print("\n" + "="*70)
        print("ADMIN USER RESET")
        print("="*70)
        print("\nThis will delete:")
        print("  - All admin users")
        print("  - All admin sessions")
        print("  - All admin audit logs")
        print("\nThis will NOT affect:")
        print("  ✓ Organizations")
        print("  ✓ Teams")
        print("  ✓ Model groups")
        print("  ✓ Credits")
        print("  ✓ Jobs")
        print("  ✓ Virtual keys")
        print("  ✓ Any other business data")
        print("\n" + "="*70)

        response = input("\nProceed with reset? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("❌ Reset cancelled.")
            return False

    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            try:
                # Delete in correct order (respecting foreign keys)
                result1 = conn.execute(text("DELETE FROM admin_sessions"))
                deleted_sessions = result1.rowcount

                result2 = conn.execute(text("DELETE FROM admin_audit_log"))
                deleted_logs = result2.rowcount

                result3 = conn.execute(text("DELETE FROM admin_users"))
                deleted_users = result3.rowcount

                # Verify tables are empty
                count_result = conn.execute(text("SELECT COUNT(*) FROM admin_users"))
                remaining_users = count_result.scalar()

                if remaining_users > 0:
                    trans.rollback()
                    print(f"❌ Error: {remaining_users} admin users still exist after deletion!")
                    return False

                # Commit transaction
                trans.commit()

                print("\n✅ Admin users reset successfully!")
                print(f"\nDeleted:")
                print(f"  - {deleted_users} admin users")
                print(f"  - {deleted_sessions} sessions")
                print(f"  - {deleted_logs} audit log entries")
                print(f"\nRemaining admin users: {remaining_users}")
                print("\n🔄 Visit the admin dashboard to create a new owner account.")

                return True

            except Exception as e:
                trans.rollback()
                print(f"❌ Error during reset: {e}")
                return False

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Reset admin users without affecting other data"
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    success = reset_admin_users(confirm=args.confirm)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
