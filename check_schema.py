import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/reporting_db")

def check_schema():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check test_cases_structured table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'test_cases_structured'
            ORDER BY ordinal_position;
        """)
        
        print("test_cases_structured columns:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        print("\n" + "="*50 + "\n")
        
        # Check test_type_summary table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'test_type_summary'
            ORDER BY ordinal_position;
        """)
        
        print("test_type_summary columns:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        print("\n" + "="*50 + "\n")
        
        # Check transit_metrics_daily table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'transit_metrics_daily'
            ORDER BY ordinal_position;
        """)
        
        print("transit_metrics_daily columns:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
