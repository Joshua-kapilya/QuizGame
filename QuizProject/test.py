import psycopg2
from urllib.parse import urlparse

DATABASE_URL = 'postgresql://postgres:ForgotKaps15%25%25@db.afuznkimztlkijkvkggf.supabase.co:5432/postgres'

url = urlparse(DATABASE_URL)

conn = psycopg2.connect(
    dbname=url.path[1:],        # removes the leading /
    user=url.username,
    password=url.password,
    host=url.hostname,          # psycopg2 will resolve IPv4 automatically
    port=url.port,
    sslmode='require'           # Supabase requires SSL
)

print("Connected via IPv4!")
