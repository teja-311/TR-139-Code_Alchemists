import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import get_connection

def run_anomaly_detection():
    print("Running Isolation Forest Anomaly Detection on Sensor Data...")
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
    
    if df.empty:
        print("No data to process.")
        conn.close()
        return
        
    features = ['temperature', 'humidity']
    X = df[features]
    
    # We expect anomalies to be rare (e.g., 2% of the time)
    iso_forest = IsolationForest(contamination=0.02, random_state=42)
    df['anomaly_score'] = iso_forest.fit_predict(X)
    
    # IsolationForest outputs -1 for anomalies and 1 for normal data
    df['is_anomaly'] = df['anomaly_score'].apply(lambda x: 1 if x == -1 else 0)
    
    # Further filter: anomalies must violate the 2-8 C threshold to be official "breaches"
    df.loc[(df['is_anomaly'] == 1) & (df['temperature'] >= 2.0) & (df['temperature'] <= 8.0), 'is_anomaly'] = 0
    
    # Save the updated is_anomaly flag back to the db (for simplicity we can write back the whole frame or just update)
    print("Updating database with anomaly flags...")
    # Update is slow row by row, let's just push it to a new table or overwrite
    df.drop(columns=['anomaly_score'], inplace=True)
    df.to_sql('sensor_data', conn, if_exists='replace', index=False)
    
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_sensor_phc_id ON sensor_data(phc_id);
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_sensor_ts ON sensor_data(timestamp);
    ''')
    
    # Extract breaches
    extract_breach_events(df, conn)
    
    conn.close()
    print("Anomaly detection completed.")

def extract_breach_events(df, conn):
    """
    Groups contiguous anomaly rows into singular breach events.
    """
    print("Extracting breach events...")
    # Clear old breaches
    conn.execute("DELETE FROM breaches")
    
    breaches = []
    
    # Sort just in case
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['phc_id', 'timestamp'])
    
    for phc_id, group in df.groupby('phc_id'):
        group = group.reset_index(drop=True)
        
        in_breach = False
        breach_start = None
        max_t = -999
        min_t = 999
        
        for idx, row in group.iterrows():
            if row['is_anomaly'] == 1:
                if not in_breach:
                    in_breach = True
                    breach_start = row['timestamp']
                    max_t = row['temperature']
                    min_t = row['temperature']
                else:
                    if row['temperature'] > max_t: max_t = row['temperature']
                    if row['temperature'] < min_t: min_t = row['temperature']
            else:
                if in_breach:
                    # Breach ended
                    b_type = "HOT" if max_t > 8.0 else "COLD"
                    # Log the breach with the max/min extreme that occurred
                    xtreme_temp = max_t if b_type == "HOT" else min_t
                    breaches.append((phc_id, breach_start.strftime('%Y-%m-%d %H:%M:%S'), xtreme_temp, b_type))
                    in_breach = False
                    
        # Close breach if ended on last row
        if in_breach:
            b_type = "HOT" if max_t > 8.0 else "COLD"
            xtreme_temp = max_t if b_type == "HOT" else min_t
            breaches.append((phc_id, breach_start.strftime('%Y-%m-%d %H:%M:%S'), xtreme_temp, b_type))

    if breaches:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO breaches (phc_id, timestamp, temperature, type) VALUES (?, ?, ?, ?)", breaches)
        conn.commit()

if __name__ == "__main__":
    run_anomaly_detection()
