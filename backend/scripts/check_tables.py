import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    res = supabase.table("Games").select("*", count="exact").limit(1).execute()
    print("Games table found!")
except Exception as e:
    print(f"Games table not found: {e}")

try:
    res = supabase.table("games").select("*", count="exact").limit(1).execute()
    print("games table found!")
except Exception as e:
    print(f"games table not found: {e}")
