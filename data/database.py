import sqlite3
import pandas as pd
import os
from .vaccine_knowledge import get_vaccines
from .phc_definitions import get_all_phcs
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cold_chain.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create Inventory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phc_id TEXT,
            vaccine_name TEXT,
            batch_id TEXT,
            expiry_date TEXT,
            quantity INTEGER,
            status TEXT DEFAULT 'OK'
        )
    ''')
    
    # Create Sensor Data Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phc_id TEXT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL,
            is_anomaly INTEGER DEFAULT 0
        )
    ''')
    
    # Create Breaches Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS breaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phc_id TEXT,
            timestamp TEXT,
            temperature REAL,
            type TEXT
        )
    ''')
    
    # Quarantine Action Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quarantine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phc_id TEXT,
            phc_name TEXT,
            batch_id TEXT,
            vaccine_name TEXT,
            quantity INTEGER,
            officer_phone TEXT,
            actioned_at TEXT,
            whatsapp_sent INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    
def seed_inventory():
    """Seeds the inventory table with realistic default values if empty."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory")
    count = cursor.fetchone()[0]
    
    if count == 0:
        phcs = get_all_phcs()
        vaccines = get_vaccines()
        
        inventory_data = []
        for phc in phcs:
            for vac in vaccines:
                # 1-3 batches per vaccine per PHC
                num_batches = random.randint(1, 3)
                for i in range(num_batches):
                    batch_id = f"BATCH-{vac[:3].upper()}-{random.randint(1000, 9999)}"
                    exp_date = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
                    quantity = random.randint(50, 500)
                    inventory_data.append((phc["id"], vac, batch_id, exp_date, quantity, 'OK'))
        
        cursor.executemany("INSERT INTO inventory (phc_id, vaccine_name, batch_id, expiry_date, quantity, status) VALUES (?, ?, ?, ?, ?, ?)", inventory_data)
        conn.commit()
        
    conn.close()

def get_inventory_df(phc_id=None):
    conn = get_connection()
    if phc_id:
        df = pd.read_sql_query(f"SELECT * FROM inventory WHERE phc_id='{phc_id}'", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    return df

def update_inventory_status(batch_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET status=? WHERE batch_id=?", (new_status, batch_id))
    conn.commit()
    conn.close()

def get_sensor_data_df(phc_id, limit=1000):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM sensor_data WHERE phc_id='{phc_id}' ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp') # Sort oldest to newest for plotting
    return df

def get_all_recent_sensor_data():
    conn = get_connection()
    # Get the latest reading for each PHC
    query = '''
    SELECT s1.*
    FROM sensor_data s1
    INNER JOIN (
        SELECT phc_id, MAX(timestamp) as max_ts
        FROM sensor_data
        GROUP BY phc_id
    ) s2 ON s1.phc_id = s2.phc_id AND s1.timestamp = s2.max_ts
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def log_quarantine_action(phc_id, phc_name, batch_id, vaccine_name, quantity, officer_phone):
    """Records a quarantine action in the log."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quarantine_log (phc_id, phc_name, batch_id, vaccine_name, quantity, officer_phone, actioned_at, whatsapp_sent) VALUES (?,?,?,?,?,?,?,1)",
        (phc_id, phc_name, batch_id, vaccine_name, quantity, officer_phone, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    # Mark the batch as quarantined in inventory
    cursor.execute("UPDATE inventory SET status='QUARANTINED' WHERE batch_id=?", (batch_id,))
    conn.commit()
    conn.close()

def get_quarantine_log():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM quarantine_log ORDER BY actioned_at DESC", conn)
    conn.close()
    return df

# Ensure DB is initialized to prevent missing table errors on first load
init_db()
