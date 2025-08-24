import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Sims 3 Completionist Tracker",
    page_icon="🎮",
    layout="wide"
)

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('db/sims3_tracker.db')

def get_saves():
    """Get all save files."""
    conn = get_db_connection()
    query = "SELECT * FROM saves ORDER BY is_active DESC, name"
    saves = pd.read_sql_query(query, conn)
    conn.close()
    return saves

def get_active_save():
    """Get the currently active save."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM saves WHERE is_active = 1 LIMIT 1")
    save = cursor.fetchone()
    conn.close()
    if save:
        return {"id": save[0], "name": save[1], "description": save[2]}
    return None

def get_lifetime_wishes_with_progress(save_id):
    """Get all lifetime wishes with progress for a specific save."""
    conn = get_db_connection()
    query = '''
        SELECT 
            lw.id,
            lw.name,
            lw.source,
            lw.completion_type,
            lw.icon_name,
            COALESCE(lwp.completed, 0) as completed,
            lwp.completed_date,
            lwp.notes
        FROM lifetime_wishes lw
        LEFT JOIN lifetime_wishes_progress lwp ON lw.id = lwp.lifetime_wish_id AND lwp.save_id = ?
        ORDER BY lw.source, lw.name
    '''
    df = pd.read_sql_query(query, conn, params=[save_id])
    conn.close()
    return df

def update_lifetime_wish_progress(save_id, lifetime_wish_id, completed, notes=""):
    """Update progress for a lifetime wish."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    completed_date = datetime.now().strftime('%Y-%m-%d') if completed else None
    
    cursor.execute('''
        INSERT OR REPLACE INTO lifetime_wishes_progress 
        (save_id, lifetime_wish_id, completed, completed_date, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (save_id, lifetime_wish_id, completed, completed_date, notes))
    
    conn.commit()
    conn.close()

def create_new_save(name, description=""):
    """Create a new save file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO saves (name, description)
        VALUES (?, ?)
    ''', (name, description))
    
    conn.commit()
    conn.close()

def set_active_save(save_id):
    """Set a save as active."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, set all saves to inactive
    cursor.execute("UPDATE saves SET is_active = 0")
    
    # Then set the selected save as active
    cursor.execute("UPDATE saves SET is_active = 1 WHERE id = ?", (save_id,))
    
    conn.commit()
    conn.close()

def export_all_data():
    """Export all data to CSV format."""
    conn = get_db_connection()
    
    # Get all data
    saves_df = pd.read_sql_query("SELECT * FROM saves", conn)
    lifetime_wishes_df = pd.read_sql_query("SELECT * FROM lifetime_wishes", conn)
    progress_df = pd.read_sql_query('''
        SELECT 
            s.name as save_name,
            lw.name as lifetime_wish_name,
            lw.source,
            lwp.completed,
            lwp.completed_date,
            lwp.notes
        FROM lifetime_wishes_progress lwp
        JOIN saves s ON lwp.save_id = s.id
        JOIN lifetime_wishes lw ON lwp.lifetime_wish_id = lw.id
    ''', conn)
    
    conn.close()
    
    # Create a BytesIO object to store the Excel file
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        saves_df.to_excel(writer, sheet_name='Saves', index=False)
        lifetime_wishes_df.to_excel(writer, sheet_name='Lifetime Wishes', index=False)
        progress_df.to_excel(writer, sheet_name='Progress', index=False)
    
    output.seek(0)
    return output

# Main app
def main():
    st.title("🎮 Sims 3 Completionist Tracker")
    
    # Check if database exists
    if not os.path.exists('db/sims3_tracker.db'):
        st.error("Database not found! Please run the database creation script first.")
        st.code("python3 db/scripts/db_create.py")
        return
    
    # Get active save
    active_save = get_active_save()
    if not active_save:
        st.error("No active save found! Please create a save file first.")
        return
    
    st.info(f"Current Save: **{active_save['name']}**")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Progress Overview", "💾 Save Files", "✅ Lifetime Wishes", "⚙️ Manage"])
    
    with tab1:
        st.header("📊 Progress Overview")
        
        # Get lifetime wishes data
        df = get_lifetime_wishes_with_progress(active_save['id'])
        
        if df.empty:
            st.warning("No lifetime wishes found. Please load the lifetime wishes data first.")
            st.code("python3 db/scripts/load_lifetime_wishes.py")
            return
        
        # Overall stats
        total_wishes = len(df)
        completed_wishes = len(df[df['completed'] == 1])
        completion_percentage = (completed_wishes / total_wishes * 100) if total_wishes > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Lifetime Wishes", total_wishes)
        with col2:
            st.metric("Completed", completed_wishes)
        with col3:
            st.metric("Completion %", f"{completion_percentage:.1f}%")
        
        # Progress bar
        st.progress(completion_percentage / 100)
        
        # Stats by source
        st.subheader("Progress by Expansion Pack")
        source_stats = df.groupby('source').agg({
            'completed': ['count', 'sum']
        }).round(1)
        source_stats.columns = ['Total', 'Completed']
        source_stats['Completion %'] = (source_stats['Completed'] / source_stats['Total'] * 100).round(1)
        st.dataframe(source_stats, use_container_width=True)
    
    with tab2:
        st.header("💾 Save Files")
        
        saves_df = get_saves()
        
        # Display current saves
        st.subheader("Current Save Files")
        for _, save in saves_df.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                status = "🟢 Active" if save['is_active'] else "⚪ Inactive"
                st.write(f"**{save['name']}** {status}")
                if save['description']:
                    st.write(f"*{save['description']}*")
            with col2:
                if st.button("Activate", key=f"activate_{save['id']}"):
                    set_active_save(save['id'])
                    st.experimental_rerun()
            with col3:
                st.write(f"Created: {save['created_date']}")
        
        # Create new save
        st.subheader("Create New Save")
        with st.form("new_save_form"):
            new_save_name = st.text_input("Save Name", placeholder="e.g., My Second Family")
            new_save_desc = st.text_area("Description (optional)", placeholder="Brief description of this save...")
            
            if st.form_submit_button("Create Save"):
                if new_save_name.strip():
                    try:
                        create_new_save(new_save_name.strip(), new_save_desc.strip())
                        st.success(f"Created save: {new_save_name}")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error creating save: {e}")
                else:
                    st.error("Please enter a save name")
    
    with tab3:
        st.header("✅ Lifetime Wishes")
        
        # Get lifetime wishes data
        df = get_lifetime_wishes_with_progress(active_save['id'])
        
        if df.empty:
            st.warning("No lifetime wishes found. Please load the lifetime wishes data first.")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            source_filter = st.selectbox(
                "Filter by Expansion Pack",
                ["All"] + sorted(df['source'].unique().tolist())
            )
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Completed", "Not Completed"]
            )
        
        # Apply filters
        filtered_df = df.copy()
        if source_filter != "All":
            filtered_df = filtered_df[filtered_df['source'] == source_filter]
        if status_filter == "Completed":
            filtered_df = filtered_df[filtered_df['completed'] == 1]
        elif status_filter == "Not Completed":
            filtered_df = filtered_df[filtered_df['completed'] == 0]
        
        # Group by source
        sources = filtered_df['source'].unique()
        
        for source in sorted(sources):
            source_df = filtered_df[filtered_df['source'] == source]
            
            with st.expander(f"📦 {source} ({len(source_df)} wishes)", expanded=(len(sources) == 1)):
                for _, wish in source_df.iterrows():
                    col1, col2, col3 = st.columns([1, 4, 2])
                    
                    with col1:
                        # Checkbox for completion
                        completed = st.checkbox(
                            "Done",
                            value=bool(wish['completed']),
                            key=f"wish_{wish['id']}"
                        )
                        
                        # Update progress if changed
                        if completed != bool(wish['completed']):
                            update_lifetime_wish_progress(active_save['id'], wish['id'], completed)
                            st.experimental_rerun()
                    
                    with col2:
                        # Icon and name
                        icon_display = "📁" if wish['icon_name'] != "PLACEHOLDER" else "🔲"
                        st.write(f"{icon_display} **{wish['name']}**")
                        if wish['icon_name'] != "PLACEHOLDER":
                            st.caption(f"Icon: {wish['icon_name']}")
                        if wish['completed'] and wish['completed_date']:
                            st.success(f"✅ Completed on {wish['completed_date']}")
                    
                    with col3:
                        # Notes
                        notes = st.text_input(
                            "Notes",
                            value=wish['notes'] or "",
                            key=f"notes_{wish['id']}",
                            placeholder="Add notes..."
                        )
                        
                        # Update notes if changed
                        if notes != (wish['notes'] or ""):
                            update_lifetime_wish_progress(
                                active_save['id'], 
                                wish['id'], 
                                bool(wish['completed']), 
                                notes
                            )
    
    with tab4:
        st.header("⚙️ Manage Data")
        
        # Export data
        st.subheader("📤 Export Data")
        st.write("Download all your progress data as an Excel file.")
        
        if st.button("Export All Data"):
            try:
                excel_data = export_all_data()
                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=f"sims3_tracker_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error exporting data: {e}")
        
        # Database info
        st.subheader("📊 Database Information")
        
        conn = get_db_connection()
        
        # Count records in each table
        tables = ['saves', 'lifetime_wishes', 'lifetime_wishes_progress']
        for table in tables:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            st.write(f"**{table}**: {count} records")
        
        conn.close()
        
        # Reload data
        st.subheader("🔄 Reload Data")
        st.write("Reload lifetime wishes from CSV file.")
        
        if st.button("Reload Lifetime Wishes"):
            st.info("To reload data, run this command in terminal:")
            st.code("python3 db/scripts/load_lifetime_wishes.py")

if __name__ == "__main__":
    main()
