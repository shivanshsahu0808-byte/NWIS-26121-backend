import sys
import os

# Parent folder ko Python path mein add karo
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database import get_connection


def load_historical_events():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            event,
            depth,
            well_id,
            severity
        FROM historical_events
        ORDER BY depth;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


if __name__ == "__main__":

    events = load_historical_events()

    print("\n===================================")
    print("      NWIS ML DATA CHECK")
    print("===================================\n")

    print("Total historical events:", len(events))

    print("\nFirst 10 records:\n")

    for event in events[:10]:
        print(event)

    print("\n===================================")