"""Load secrets without putting them in code.

Locally: values come from a .env file (see .env.example).
Deployed: values come from the host's Secrets (Streamlit Community Cloud).
Either way they end up in os.environ, so the pipeline can read os.environ.
"""
import os

import streamlit as st
from dotenv import load_dotenv


def load_secrets() -> None:
    """Fill os.environ from .env, then from st.secrets (if any)."""
    load_dotenv()  # no error if .env is missing
    try:
        for name, value in st.secrets.items():
            if isinstance(value, str):
                os.environ.setdefault(name, value)
    except Exception:
        pass  # no secrets.toml locally: that's fine
