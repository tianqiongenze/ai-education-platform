#!/usr/bin/env python3
"""Create Lecture-P1 to P6 users via JupyterHub database, running inside the hub pod."""
import json
import os
import sys
import time
import sqlite3
DB_PATH = "/srv/jupyterhub/jupyterhub.sqlite"

def create_users_directly():
    """Create users directly in the JupyterHub database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if users table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not c.fetchone():
        print("Users table not found!")
        return
    
    # Create Lecture users
    users = ["Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"]
    for username in users:
        try:
            c.execute("INSERT INTO users (name, admin) VALUES (?, ?)", (username, 1))
            print(f"Created admin user: {username}")
        except sqlite3.IntegrityError:
            # User already exists, update admin flag
            c.execute("UPDATE users SET admin = 1 WHERE name = ?", (username,))
            print(f"Updated existing user to admin: {username}")
    
    conn.commit()
    
    # Verify
    c.execute("SELECT name, admin FROM users")
    all_users = c.fetchall()
    print(f"\nAll users in database ({len(all_users)}):")
    for name, admin in all_users:
        print(f"  {name} {'(admin)' if admin else ''}")
    
    conn.close()

if __name__ == "__main__":
    create_users_directly()
    print("\nDone! Users created. They can now log in with password ide2026.")
    print("Their pods will be created automatically on first login.")
