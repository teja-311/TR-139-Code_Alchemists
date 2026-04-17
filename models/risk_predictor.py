"""
models/risk_predictor.py

Predicts the probability of a cold-chain breach in the next 24 hours for
a given PHC using a Random Forest classifier trained on engineered features
from the historical sensor telemetry stored in SQLite.

Feature engineering produces one row per calendar *day* per PHC:
    - avg_temp         : mean temperature during the day
    - max_temp         : max temperature (hottest moment)
    - temp_variance    : variance — high variance = unstable fridge
    - breach_count     : number of breach events that already happened that day
    - night_max_temp   : max temp between 22:00-06:00 (power failure window)
    - trend_slope      : linear regression slope of temperature over the day
    - hour_of_peak     : hour of the day when the maximum temperature occurred

Target: did a breach happen the *following* day?  (label_next_day_breach)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import get_connection


# ── Feature Engineering ────────────────────────────────────────────────────────

def _build_daily_features(df_sensor: pd.DataFrame, df_breaches: pd.DataFrame, phc_id: str) -> pd.DataFrame:
    """Returns a dataframe with one row per calendar day containing engineered features."""
    df = df_sensor[df_sensor['phc_id'] == phc_id].copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour

    # Count breaches per day for this PHC
    dbr = df_breaches[df_breaches['phc_id'] == phc_id].copy()
    dbr['timestamp'] = pd.to_datetime(dbr['timestamp'])
    dbr['date'] = dbr['timestamp'].dt.date
    daily_breaches = dbr.groupby('date').size().reset_index(name='breach_count')

    rows = []
    for date, grp in df.groupby('date'):
        night = grp[grp['hour'].isin(list(range(0, 6)) + list(range(22, 24)))]
        peak_hour = int(grp.loc[grp['temperature'].idxmax(), 'hour']) if not grp.empty else 12

        # Linear trend slope via numpy polyfit
        temps = grp.sort_values('timestamp')['temperature'].values
        slope = 0.0
        if len(temps) > 1:
            xs = np.arange(len(temps), dtype=float)
            try:
                slope = float(np.polyfit(xs, temps, 1)[0])
            except Exception:
                slope = 0.0

        b_count = int(daily_breaches[daily_breaches['date'] == date]['breach_count'].values[0]) \
            if date in daily_breaches['date'].values else 0

        rows.append({
            'date': date,
            'avg_temp': grp['temperature'].mean(),
            'max_temp': grp['temperature'].max(),
            'min_temp': grp['temperature'].min(),
            'temp_variance': grp['temperature'].var(),
            'breach_count': b_count,
            'night_max_temp': night['temperature'].max() if not night.empty else grp['temperature'].mean(),
            'trend_slope': slope,
            'hour_of_peak': peak_hour,
            'avg_humidity': grp['humidity'].mean(),
        })

    feature_df = pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    return feature_df


def _add_breach_labels(feature_df: pd.DataFrame) -> pd.DataFrame:
    """Shift breach_count by -1 to create label: did a breach happen tomorrow?"""
    feature_df = feature_df.copy()
    feature_df['label_next_day_breach'] = (feature_df['breach_count'].shift(-1) > 0).astype(int)
    feature_df = feature_df.dropna()
    return feature_df


# ── Main Prediction Function ───────────────────────────────────────────────────

FEATURE_COLS = [
    'avg_temp', 'max_temp', 'min_temp', 'temp_variance',
    'breach_count', 'night_max_temp', 'trend_slope',
    'hour_of_peak', 'avg_humidity'
]


def predict_tomorrow_risk(phc_id: str) -> dict:
    """
    Returns a dict with:
        probability      : float 0-1, chance of breach tomorrow
        risk_level       : "LOW" / "MEDIUM" / "HIGH" / "CRITICAL"
        primary_factor   : human-readable top driver
        top_features     : list of (feature_name, importance) tuples
        today_stats      : dict of today's sensor summary
        enough_data      : bool — False when less than 7 days of history available
    """
    conn = get_connection()
    df_sensor = pd.read_sql_query(
        f"SELECT * FROM sensor_data WHERE phc_id='{phc_id}' ORDER BY timestamp", conn)
    df_breaches = pd.read_sql_query(
        f"SELECT * FROM breaches WHERE phc_id='{phc_id}' ORDER BY timestamp", conn)
    conn.close()

    if df_sensor.empty:
        return {'enough_data': False, 'probability': 0.0, 'risk_level': 'UNKNOWN',
                'primary_factor': 'No sensor data available', 'top_features': [], 'today_stats': {}}

    feature_df = _build_daily_features(df_sensor, df_breaches, phc_id)
    labeled = _add_breach_labels(feature_df)

    # Need at least 7 labelled rows to train meaningfully
    if len(labeled) < 7:
        # Fallback: rule-based score
        today_row = feature_df.iloc[-1]
        score = _rule_based_score(today_row)
        return _build_result(score, today_row, feature_df, enough_data=False)

    X = labeled[FEATURE_COLS].values
    y = labeled['label_next_day_breach'].values

    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=5,
        class_weight='balanced',
        random_state=42
    )
    clf.fit(X, y)

    # Predict on today (last row of feature_df — no label needed)
    today_row = feature_df.iloc[-1]
    today_X = today_row[FEATURE_COLS].values.reshape(1, -1)
    proba = float(clf.predict_proba(today_X)[0][1])

    # Feature importances
    importances = list(zip(FEATURE_COLS, clf.feature_importances_.tolist()))
    importances.sort(key=lambda x: x[1], reverse=True)

    return _build_result(proba, today_row, feature_df, enough_data=True,
                         top_features=importances[:4])


def _rule_based_score(today_row) -> float:
    """Simple heuristic when not enough training data exists."""
    score = 0.0
    if today_row['max_temp'] > 8.0:
        score += 0.35
    if today_row['temp_variance'] > 2.0:
        score += 0.20
    if today_row['breach_count'] > 0:
        score += 0.25
    if today_row['trend_slope'] > 0.05:
        score += 0.15
    if today_row['night_max_temp'] > 9.0:
        score += 0.15
    return min(score, 0.95)


def _build_result(probability: float, today_row, feature_df, enough_data: bool,
                  top_features=None) -> dict:
    if top_features is None:
        top_features = []

    if probability < 0.30:
        risk_level = "LOW"
    elif probability < 0.55:
        risk_level = "MEDIUM"
    elif probability < 0.75:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Determine primary human-readable factor
    primary = "stable thermal pattern observed"
    if today_row['max_temp'] > 9.0:
        primary = f"today's peak temperature reached {today_row['max_temp']:.1f}°C"
    elif today_row['temp_variance'] > 2.5:
        primary = f"high temperature variance ({today_row['temp_variance']:.2f}°C²) detected"
    elif today_row['breach_count'] > 0:
        primary = f"{int(today_row['breach_count'])} breach event(s) already recorded today"
    elif today_row['trend_slope'] > 0.05:
        primary = "rising temperature trend throughout the day"
    elif today_row['night_max_temp'] > 9.0:
        primary = f"overnight temperature spike to {today_row['night_max_temp']:.1f}°C"

    today_stats = {
        'avg_temp': round(float(today_row['avg_temp']), 2),
        'max_temp': round(float(today_row['max_temp']), 2),
        'min_temp': round(float(today_row['min_temp']), 2),
        'temp_variance': round(float(today_row['temp_variance']), 3),
        'breach_count_today': int(today_row['breach_count']),
        'trend_slope': round(float(today_row['trend_slope']), 4),
        'night_max_temp': round(float(today_row['night_max_temp']), 2),
    }

    return {
        'probability': round(probability, 4),
        'risk_level': risk_level,
        'primary_factor': primary,
        'top_features': top_features,
        'today_stats': today_stats,
        'enough_data': enough_data,
    }
