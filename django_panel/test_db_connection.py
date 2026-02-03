"""
تست اتصال به دیتابیس PostgreSQL
"""
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host='666dc316-12f4-49f3-987f-ca1a0781a9fa.hadb.ir',
        port=26641,
        database='postgres',
        user='postgres',
        password='04cTAnvcHRbwr0T9cXXB',
        connect_timeout=10
    )
    print("Successfully connected to PostgreSQL!")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"PostgreSQL Version: {version[0]}")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"Error connecting to PostgreSQL:")
    print(f"   {e}")
    print("\nSolutions:")
    print("   1. Check if PostgreSQL server is accessible")
    print("   2. Check if your IP is whitelisted")
    print("   3. Check firewall settings")
    print("   4. You can use SQLite for development")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
