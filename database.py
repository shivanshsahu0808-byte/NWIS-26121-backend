import os
import pg8000
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():

    if DATABASE_URL:
        url = urlparse(DATABASE_URL)

        return pg8000.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port or 5432,
            database=url.path.lstrip("/")
        )

    return pg8000.connect(
        user="postgres",
        password="j6kc46S@hu",
        host="localhost",
        port=5432,
        database="nwis_db"
    )