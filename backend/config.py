"""Database settings, read from environment variables (no secrets in code)."""
import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "research_portal")

# Cloud MySQL providers (Aiven, TiDB, PlanetScale...) require SSL.
DB_SSL = os.environ.get("DB_SSL", "false").lower() in ("1", "true", "yes")
# Optional: path to a provider CA certificate file (e.g. Aiven's ca.pem).
DB_SSL_CA = os.environ.get("DB_SSL_CA")
