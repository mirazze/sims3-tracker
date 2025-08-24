#!/usr/bin/env python3
"""
Load lifetime wishes from CSV into the new database structure.
"""

import sqlite3
import csv
import os
import glob

def find_icon_file(name):
    """
    Find the corresponding icon file for a lifetime wish.
    Returns the filename if found, 'PLACEHOLDER' if not found.
    """
    # Convert name to potential filename patterns
    # Remove special characters and convert to lowercase
    clean_name = name.lower()
    clean_name = clean_name.replace("'", "")
    clean_name = clean_name.replace('"', '')
    clean_name = clean_name.replace(',', '')
    clean_name = clean_name.replace(':', '')
    clean_name = clean_name.replace('-', '_')
    clean_name = clean_name.replace(' ', '_')
    clean_name = clean_name.replace('__', '_')
    
    # Look for icon files in the icons/lifetime_wishes directory
    icon_dir = "icons/lifetime_wishes"
    if not os.path.exists(icon_dir):
        return "PLACEHOLDER"
    
    # Get all PNG files in the directory
    png_files = glob.glob(os.path.join(icon_dir, "*.png"))
    
    # Extract just the filenames without path
    icon_files = [os.path.basename(f) for f in png_files]
    
    # Try different matching patterns
    patterns_to_try = [
        f"{clean_name}.png",
        f"w_lifetime_{clean_name}.png",
        f"w_{clean_name}.png",
    ]
    
    # Also try some specific mappings for known files
    specific_mappings = {
        "season_traveler": "seasoned_traveler.png",
        "fashion_phenomenon": "w_lifetime_stylist.png",
        "paranormal_profiteer": "w_lifetime_ghosthunter.png",
        "nectar_making": "nectar_making.png",
        # Add more specific mappings as needed
    }
    
    if clean_name in specific_mappings:
        if specific_mappings[clean_name] in icon_files:
            return specific_mappings[clean_name]
    
    # Try each pattern
    for pattern in patterns_to_try:
        if pattern in icon_files:
            return pattern
    
    # Try partial matching (icon filename contains part of the name)
    name_parts = clean_name.split('_')
    for icon_file in icon_files:
        icon_base = icon_file.replace('.png', '')
        # Check if any significant part of the name matches
        for part in name_parts:
            if len(part) > 3 and part in icon_base:
                return icon_file
    
    return "PLACEHOLDER"

def load_lifetime_wishes():
    """Load lifetime wishes from CSV file."""
    
    # Connect to database
    conn = sqlite3.connect('db/sims3_tracker.db')
    cursor = conn.cursor()
    
    # Clear existing lifetime wishes
    cursor.execute("DELETE FROM lifetime_wishes")
    
    csv_file = "data/lifetime_wishes.csv"
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    loaded_count = 0
    icon_count = 0
    placeholder_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            name = row['Name'].strip()
            source = row['Source'].strip()
            completion_type = row['Completion_Type'].strip()
            
            # Find icon
            icon_name = find_icon_file(name)
            if icon_name != "PLACEHOLDER":
                icon_count += 1
            else:
                placeholder_count += 1
            
            # Insert into database
            cursor.execute('''
                INSERT INTO lifetime_wishes (name, source, completion_type, icon_name)
                VALUES (?, ?, ?, ?)
            ''', (name, source, completion_type, icon_name))
            
            loaded_count += 1
    
    # Commit changes
    conn.commit()
    
    print(f"Successfully loaded {loaded_count} lifetime wishes!")
    print(f"Found icons for {icon_count} lifetime wishes")
    print(f"Using placeholders for {placeholder_count} lifetime wishes")
    
    # Display some examples organized by source
    print("\nLoaded Lifetime Wishes by Source:")
    
    cursor.execute('''
        SELECT source, COUNT(*) as count 
        FROM lifetime_wishes 
        GROUP BY source 
        ORDER BY source
    ''')
    
    sources = cursor.fetchall()
    for source, count in sources:
        print(f"\n  {source}: {count} wishes")
        
        # Show first few wishes from each source
        cursor.execute('''
            SELECT name, icon_name 
            FROM lifetime_wishes 
            WHERE source = ? 
            ORDER BY name 
            LIMIT 5
        ''', (source,))
        
        wishes = cursor.fetchall()
        for wish_name, icon_name in wishes:
            icon_display = f"📁 {icon_name}" if icon_name != "PLACEHOLDER" else f"🔲 {icon_name}"
            print(f"    {icon_display} {wish_name}")
        
        # If there are more than 5, show count
        if count > 5:
            print(f"    ... and {count - 5} more")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    load_lifetime_wishes()
