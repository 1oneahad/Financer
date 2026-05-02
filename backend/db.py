import os

import httpx
from dotenv import load_dotenv
from supabase import ClientOptions, create_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

http_client = httpx.Client(http2=False, timeout=httpx.Timeout(30.0, connect=10.0))
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions(httpx_client=http_client, postgrest_client_timeout=30),
)
