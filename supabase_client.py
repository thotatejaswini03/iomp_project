"""
supabase_client.py
------------------
Supports local .env and Streamlit Cloud secrets.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
_client: Client = None

def _get_credentials():
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return url, key
    except Exception:
        pass
    return os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_KEY", "")

def get_client() -> Client:
    global _client
    if _client is None:
        url, key = _get_credentials()
        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials.\n"
                "Set SUPABASE_URL and SUPABASE_KEY in .env or Streamlit Cloud Secrets."
            )
        _client = create_client(url, key)
    return _client
