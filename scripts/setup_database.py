"""
Database setup script.
Run once to create all tables.

Why PostgreSQL?
- Persistent storage — survives restarts
- Handles concurrent reads/writes
- Standard in production systems
- Docker makes it easy to run locally
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    conn = psycopg2.connect(os.getenv("POSTGRES_URL"))
    cursor = conn.cursor()

    # Portfolio holdings table
    # Stores every stock the user owns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            quantity FLOAT NOT NULL,
            avg_buy_price FLOAT NOT NULL,
            buy_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactions table
    # Complete history of every buy/sell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            action VARCHAR(10) NOT NULL,
            quantity FLOAT NOT NULL,
            price FLOAT NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables created successfully")

if __name__ == "__main__":
    setup_database()