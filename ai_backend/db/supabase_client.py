from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional[Client]:
    """
    Server-side Supabase client.

    Recommended env vars:
    - SUPABASE_URL
    - SUPABASE_SERVICE_KEY (preferred)
    Fallbacks:
    - SUPABASE_ANON_KEY
    - VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY
    """
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("VITE_SUPABASE_ANON_KEY")
    )
    if not url or not key:
        return None
    return create_client(url, key)


def require_supabase() -> Client:
    client = get_supabase_client()
    if not client:
        raise RuntimeError("Supabase client is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.")
    return client

