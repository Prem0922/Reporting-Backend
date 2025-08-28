#!/usr/bin/env python3
"""
Script to clear all generated data from the PostgreSQL reporting database.
This will delete all data from all tables except the database structure itself.
"""

import os
from database_postgresql import db, engine
from sqlalchemy import text

def clear_all_data():
    """Clear all data from all tables in the database"""
    
    try:
        # Connect to database
        with engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            tables = [row[0] for row in result]
            
            print("Found tables:", tables)
            
            # Clear data from each table
            for table_name in tables:
                if table_name not in ['alembic_version']:  # Skip migration table
                    conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
                    print(f"Cleared data from table: {table_name}")
            
            # Commit changes
            conn.commit()
        
        print("\n✅ All data has been successfully cleared from the database!")
        print("The database structure remains intact.")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return False

def clear_specific_table(table_name):
    """Clear data from a specific table"""
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            """), {"table_name": table_name})
            
            if not result.fetchone():
                print(f"Table '{table_name}' not found!")
                return False
            
            # Clear data from specific table
            conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
            conn.commit()
        
        print(f"✅ Data cleared from table: {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing table {table_name}: {e}")
        return False

def show_table_info():
    """Show information about tables and their row counts"""
    
    try:
        with engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            tables = [row[0] for row in result]
            
            print("\n📊 Current Database Status:")
            print("-" * 50)
            
            for table_name in tables:
                if table_name not in ['alembic_version']:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = count_result.fetchone()[0]
                    print(f"{table_name:25} | {count:5} rows")
        
    except Exception as e:
        print(f"❌ Error getting table info: {e}")

if __name__ == "__main__":
    import sys
    
    print("🗑️  Reporting Database Data Cleaner")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "show" or command == "info":
            show_table_info()
        elif command == "table" and len(sys.argv) > 2:
            table_name = sys.argv[2]
            clear_specific_table(table_name)
        else:
            print("Usage:")
            print("  python clear_data.py              # Clear all data")
            print("  python clear_data.py show         # Show table info")
            print("  python clear_data.py table <name> # Clear specific table")
    else:
        # Show current status first
        show_table_info()
        
        # Ask for confirmation
        response = input("\n⚠️  Are you sure you want to clear ALL data? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            clear_all_data()
            print("\n📊 Final status:")
            show_table_info()
        else:
            print("Operation cancelled.")
