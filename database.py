import psycopg2

username = "doadmin"
password = "AVNS_pqrCZr0OCoMDCJRywMe"
host = "trial-rocket-do-user-13833772-0.b.db.ondigitalocean.com"
port = 25060
database = "defaultdb"
sslmode = "require"

conn = None  # Initialize conn outside the try block

try:
    conn = psycopg2.connect(
        user=username,
        password=password,
        host=host,
        port=port,
        database=database,
        sslmode=sslmode,
    )
    print("Connection succeeded!")

    # Optionally, perform a simple query to further validate
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        result = cur.fetchone()
        if result == (1,):
            print("Connection and query successful!")
        else:
            print("Query failed.")

except psycopg2.Error as e:
    print(f"Connection failed: {e}")

finally:
    if conn:
        conn.close()