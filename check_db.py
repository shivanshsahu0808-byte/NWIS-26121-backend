from database import get_connection

conn = get_connection()
cur = conn.cursor()

print("\n--- WELLS ---")

cur.execute("SELECT * FROM wells;")

for row in cur.fetchall():
    print(row)


print("\n--- HISTORICAL EVENTS ---")

cur.execute("SELECT * FROM historical_events;")

for row in cur.fetchall():
    print(row)


cur.close()
conn.close()