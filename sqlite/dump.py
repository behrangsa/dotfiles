#!/usr/bin/env python3
import sqlite3
import pandas as pd
import argparse
import os
import sys


def get_all_tables(conn):
    """Get all table names from the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [table[0] for table in cursor.fetchall()]


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Export SQLite database tables to HTML files.")
    parser.add_argument("--db", "-d", required=True, help="Path to the SQLite database file")
    parser.add_argument(
        "--output", "-o", default=".", help="Output directory path (default: current directory)"
    )
    args = parser.parse_args()

    # Validate database file existence
    if not os.path.isfile(args.db):
        print(f"Error: Database file '{args.db}' not found.", file=sys.stderr)
        sys.exit(1)

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        try:
            os.makedirs(args.output)
        except OSError as e:
            print(f"Error creating output directory: {e}", file=sys.stderr)
            sys.exit(1)

    # Connect to the database
    try:
        conn = sqlite3.connect(args.db)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get all table names
        tables = get_all_tables(conn)
        if not tables:
            print("No tables found in the database.", file=sys.stderr)
            sys.exit(1)

        # Process each table
        for table_name in tables:
            try:
                df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
                output_file = os.path.join(args.output, f"{table_name}.html")
                with open(output_file, "w") as f:
                    f.write(df.to_html())
                print(f"Exported table '{table_name}' to {output_file}")
            except Exception as e:
                print(f"Error processing table '{table_name}': {e}", file=sys.stderr)
    finally:
        conn.close()

    print(f"Export complete. Processed {len(tables)} tables.")


if __name__ == "__main__":
    main()
