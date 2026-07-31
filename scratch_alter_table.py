import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from src.core.client import get_postgres_client


def run():
    print("Connecting to Supabase...")
    session_factory = get_postgres_client()
    engine = session_factory.kw["bind"]

    print("Adding updated_at column...")
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS "
                "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"
            )
        )
        conn.commit()
    print("Done!")

if __name__ == "__main__":
    run()
