#!/usr/bin/env python3
"""
Create SQLite database with separate tables for each category.
Each category can have its own structure and additional fields.
"""

import sqlite3
import os

def create_database():
    # Ensure db directory exists
    os.makedirs('db', exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect('db/sims3_tracker.db')
    cursor = conn.cursor()
    
    # Get SQLite version for confirmation
    cursor.execute("SELECT sqlite_version();")
    version = cursor.fetchone()
    print(f"Opened SQLite database with version {version[0]} successfully.")
    
    # Drop existing tables if they exist
    tables_to_drop = [
        'categories', 'goals', 'saves', 'progress',
        'lifetime_wishes', 'collections', 'skills', 'careers'
    ]
    
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Create saves table (this is shared across all categories)
    cursor.execute('''
        CREATE TABLE saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_date DATE DEFAULT CURRENT_DATE,
            is_active BOOLEAN DEFAULT 0
        )
    ''')
    
    # Create lifetime_wishes table
    cursor.execute('''
        CREATE TABLE lifetime_wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            completion_type TEXT NOT NULL DEFAULT 'Checkmark',
            icon_name TEXT DEFAULT 'PLACEHOLDER',
            description TEXT,
            created_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Create lifetime_wishes_progress table (links saves to lifetime wishes)
    cursor.execute('''
        CREATE TABLE lifetime_wishes_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            save_id INTEGER NOT NULL,
            lifetime_wish_id INTEGER NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_date DATE,
            notes TEXT,
            FOREIGN KEY (save_id) REFERENCES saves (id) ON DELETE CASCADE,
            FOREIGN KEY (lifetime_wish_id) REFERENCES lifetime_wishes (id) ON DELETE CASCADE,
            UNIQUE(save_id, lifetime_wish_id)
        )
    ''')
    
    # Create collections table (for future expansion)
    cursor.execute('''
        CREATE TABLE collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            collection_type TEXT NOT NULL, -- gems, insects, fish, etc.
            completion_type TEXT NOT NULL DEFAULT 'Progress Bar',
            icon_name TEXT DEFAULT 'PLACEHOLDER',
            total_items INTEGER DEFAULT 0,
            description TEXT,
            created_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Create collections_progress table
    cursor.execute('''
        CREATE TABLE collections_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            save_id INTEGER NOT NULL,
            collection_id INTEGER NOT NULL,
            items_collected INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            completed_date DATE,
            notes TEXT,
            FOREIGN KEY (save_id) REFERENCES saves (id) ON DELETE CASCADE,
            FOREIGN KEY (collection_id) REFERENCES collections (id) ON DELETE CASCADE,
            UNIQUE(save_id, collection_id)
        )
    ''')
    
    # Create skills table (for future expansion)
    cursor.execute('''
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            max_level INTEGER DEFAULT 10,
            completion_type TEXT NOT NULL DEFAULT 'Progress Bar',
            icon_name TEXT DEFAULT 'PLACEHOLDER',
            description TEXT,
            created_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Create skills_progress table
    cursor.execute('''
        CREATE TABLE skills_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            save_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            current_level INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            completed_date DATE,
            notes TEXT,
            FOREIGN KEY (save_id) REFERENCES saves (id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE,
            UNIQUE(save_id, skill_id)
        )
    ''')
    
    # Create careers table (for future expansion)
    cursor.execute('''
        CREATE TABLE careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            max_level INTEGER DEFAULT 10,
            completion_type TEXT NOT NULL DEFAULT 'Progress Bar',
            icon_name TEXT DEFAULT 'PLACEHOLDER',
            description TEXT,
            created_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Create careers_progress table
    cursor.execute('''
        CREATE TABLE careers_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            save_id INTEGER NOT NULL,
            career_id INTEGER NOT NULL,
            current_level INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            completed_date DATE,
            notes TEXT,
            FOREIGN KEY (save_id) REFERENCES saves (id) ON DELETE CASCADE,
            FOREIGN KEY (career_id) REFERENCES careers (id) ON DELETE CASCADE,
            UNIQUE(save_id, career_id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX idx_lifetime_wishes_source ON lifetime_wishes(source)')
    cursor.execute('CREATE INDEX idx_lifetime_wishes_progress_save ON lifetime_wishes_progress(save_id)')
    cursor.execute('CREATE INDEX idx_collections_progress_save ON collections_progress(save_id)')
    cursor.execute('CREATE INDEX idx_skills_progress_save ON skills_progress(save_id)')
    cursor.execute('CREATE INDEX idx_careers_progress_save ON careers_progress(save_id)')
    
    # Insert a default save file
    cursor.execute('''
        INSERT INTO saves (name, description, is_active) 
        VALUES ('My Main Save', 'Default save file for tracking progress', 1)
    ''')
    
    # Commit changes
    conn.commit()
    
    print("Database tables created successfully!")
    print("\nCreated tables:")
    print("- saves: Manage different save files")
    print("- lifetime_wishes: Store all lifetime wishes")
    print("- lifetime_wishes_progress: Track progress per save")
    print("- collections: Store collections (for future use)")
    print("- collections_progress: Track collection progress per save")
    print("- skills: Store skills (for future use)")
    print("- skills_progress: Track skill progress per save")
    print("- careers: Store careers (for future use)")
    print("- careers_progress: Track career progress per save")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    create_database()
