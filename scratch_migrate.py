import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.client import Base, get_postgres_client


def run():
    print("Connecting to Supabase...")
    session_factory = get_postgres_client()
    engine = session_factory.kw["bind"]

    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Done!")


if __name__ == "__main__":
    run()
