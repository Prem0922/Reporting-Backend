#!/usr/bin/env python3
"""
Drop All Tables Script for Reporting Application
Manually drops all tables in the PostgreSQL database
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/reporting_db")

def drop_all_tables():
    """Drop all tables in the database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found tables: {tables}")
        
        if not tables:
            print("No tables found to drop.")
            return True
        
        # Drop all tables with CASCADE
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"❌ Error dropping table {table}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ All tables dropped successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False

if __name__ == "__main__":
    print("🗑️ Dropping All PostgreSQL Tables")
    print("=" * 50)
    drop_all_tables()
