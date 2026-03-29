"""
Database optimization script for the Stream Bill Generator
This script provides utilities for optimizing database performance.
"""
import sqlite3
import os

def add_indexes_to_db(db_path):
    """
    Add indexes to common query columns in the database
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add indexes for common query patterns
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_bills_billid ON bills(bill_id)",
            "CREATE INDEX IF NOT EXISTS idx_bills_date ON bills(bill_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_contractors_name ON contractors(name)",
            "CREATE INDEX IF NOT EXISTS idx_workorders_id ON work_orders(work_order_id)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"Added index: {index_sql}")
            except sqlite3.Error as e:
                print(f"Failed to add index {index_sql}: {e}")
        
        # Optimize database
        cursor.execute("PRAGMA optimize")
        conn.commit()
        conn.close()
        
        print("Database optimization complete")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def enable_wal_mode(db_path):
    """
    Enable WAL (Write-Ahead Logging) mode for better concurrency
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        result = cursor.fetchone()
        if result and result[0] == "wal":
            print("WAL mode enabled successfully")
        else:
            print("Failed to enable WAL mode")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Database Optimization Script")
    print("Usage: Call add_indexes_to_db('path/to/database.db') or enable_wal_mode('path/to/database.db')")