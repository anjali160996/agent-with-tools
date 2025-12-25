"""
View all records in the SQLite database tables.
"""
import sqlite3
from datetime import datetime
import json

DATABASE_FILE = "test_questions.db"

def format_datetime(dt_str):
    """Format datetime string for display"""
    if dt_str:
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt_str
    return "N/A"

def print_table_header(table_name, count):
    """Print a formatted table header"""
    print("\n" + "="*80)
    print(f"TABLE: {table_name.upper()} ({count} record(s))")
    print("="*80)

def view_table(conn, table_name):
    """View all records in a table"""
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Get all records
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print_table_header(table_name, 0)
        print("(No records)")
        return
    
    print_table_header(table_name, len(rows))
    
    # Print column headers
    print(" | ".join(f"{col:20}" for col in columns))
    print("-" * 80)
    
    # Print rows
    for row in rows:
        formatted_row = []
        for i, val in enumerate(row):
            if val is None:
                formatted_row.append("NULL")
            elif columns[i] in ['created_at', 'updated_at', 'last_sync_at', 'last_staging_change_at']:
                formatted_row.append(format_datetime(val))
            elif isinstance(val, str) and len(val) > 30:
                formatted_row.append(val[:27] + "...")
            else:
                formatted_row.append(str(val))
        print(" | ".join(f"{val:20}" for val in formatted_row))

def view_association_table(conn, table_name):
    """View association table records"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print_table_header(table_name, 0)
        print("(No records)")
        return
    
    print_table_header(table_name, len(rows))
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(" | ".join(f"{col:15}" for col in columns))
    print("-" * 50)
    
    for row in rows:
        print(" | ".join(f"{str(val):15}" for val in row))

def main():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        
        print("\n" + "="*80)
        print("DATABASE RECORDS VIEWER")
        print(f"Database: {DATABASE_FILE}")
        print("="*80)
        
        # List of tables in order
        main_tables = [
            'runs',
            'question_staging',
            'answer_staging',
            'tags',
            'questions',
            'answers'
        ]
        
        association_tables = [
            'question_tags',
            'actual_question_tags'
        ]
        
        # View main tables
        for table in main_tables:
            try:
                view_table(conn, table)
            except sqlite3.OperationalError as e:
                print(f"\nError viewing {table}: {e}")
        
        # View association tables
        for table in association_tables:
            try:
                view_association_table(conn, table)
            except sqlite3.OperationalError as e:
                print(f"\nError viewing {table}: {e}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("END OF DATABASE VIEW")
        print("="*80 + "\n")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

