import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.client import get_postgres_client, Base
from src.models.session import ChatSession

def run():
    print("Connecting to Supabase...")
    Session = get_postgres_client()
    engine = Session.kw['bind']
    
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Done!")

if __name__ == "__main__":
    run()
