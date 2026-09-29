import pg8000

DB_CONFIG = {
    "user": "postgres",
    "password": "j6kc46S@hu",
    "host": "localhost",
    "port": 5432,
    "database": "nwis_db"
}


def get_connection():
    return pg8000.connect(**DB_CONFIG)