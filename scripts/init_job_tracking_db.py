#!/usr/bin/env python3
"""
Initialize job tracking database schema.
Run this after LiteLLM has created its own tables.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from models.job_tracking import Base
from config.settings import settings


def init_database():
    """Create all job tracking tables"""
    print("🗄️  Initializing job tracking database schema...")

    # Create engine
    engine = create_engine(settings.database_url, echo=True)

    # Create all tables
    Base.metadata.create_all(engine)

    print("✅ Job tracking tables created successfully!")
    print("\nCreated tables:")
    print("  - jobs")
    print("  - llm_calls")
    print("  - job_cost_summaries")
    print("  - team_usage_summaries")
    print("  - webhook_registrations")

    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('jobs', 'llm_calls', 'job_cost_summaries', 'team_usage_summaries', 'webhook_registrations')
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]
        print(f"\n✅ Verified {len(tables)} tables exist in database")
        for table in tables:
            print(f"  ✓ {table}")


if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
