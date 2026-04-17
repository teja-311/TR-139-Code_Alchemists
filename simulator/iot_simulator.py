import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ensure we can import from parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.phc_definitions import get_all_phcs
from data.database import get_connection, init_db, seed_inventory

def generate_sensor_data(days=30, interval_minutes=15):
    print(f"Generating {days} days of IoT data...")
    init_db()
    seed_inventory()
    
    phcs = get_all_phcs()
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Calculate number of periods
    periods = int((days * 24 * 60) / interval_minutes)
    time_range = [start_time + timedelta(minutes=i*interval_minutes) for i in range(periods)]
    
    all_data = []
    
    for phc in phcs:
        print(f"Generating data for {phc['name']}...")
        
        # Base normal temperature (around 5C)
        base_temps = np.random.normal(loc=4.5, scale=1.0, size=periods)
        
        # Base normal humidity (around 50%)
        base_humid = np.random.normal(loc=50.0, scale=5.0, size=periods)
        
        df = pd.DataFrame({
            'phc_id': phc['id'],
            'timestamp': time_range,
            'temperature': np.clip(base_temps, 2.1, 7.9), # Keep mostly normal
            'humidity': np.clip(base_humid, 30, 70)
        })
        
        # Inject breaches (anomalies)
        # Randomly choose 1-3 anomaly events per PHC
        num_anomalies = np.random.randint(1, 4)
        for _ in range(num_anomalies):
            anomaly_duration_periods = np.random.randint(4, 24) # 1 to 6 hours
            anomaly_start_idx = np.random.randint(0, periods - anomaly_duration_periods)
            
            is_hot_breach = np.random.choice([True, False])
            
            if is_hot_breach:
                # Hot breach (e.g., power failure) -> Temp goes up to 12-25C
                peak_temp = np.random.uniform(10.0, 20.0)
                # Curve going up and down
                for i in range(anomaly_duration_periods):
                    factor = np.sin((i / anomaly_duration_periods) * np.pi)
                    df.loc[anomaly_start_idx + i, 'temperature'] = 8.0 + (peak_temp - 8.0) * factor
            else:
                # Cold breach (e.g., thermostat failure) -> Temp goes down to -5 - 0C
                dip_temp = np.random.uniform(-4.0, 1.0)
                for i in range(anomaly_duration_periods):
                    factor = np.sin((i / anomaly_duration_periods) * np.pi)
                    df.loc[anomaly_start_idx + i, 'temperature'] = 2.0 - (2.0 - dip_temp) * factor
                    
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        all_data.append(df)
        
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Save to SQLite
    print("Saving to database...")
    conn = get_connection()
    # To avoid huge inserts taking forever, we can do it in chunks or to_sql
    final_df.to_sql('sensor_data', conn, if_exists='replace', index=False)
    
    # Re-add indices if needed, replacing table removes them. Doing it simply:
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_sensor_phc_id ON sensor_data(phc_id);
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_sensor_ts ON sensor_data(timestamp);
    ''')
    conn.close()
    
    print("Simulation data generation complete!")

if __name__ == "__main__":
    generate_sensor_data()
