# modules/analysis.py
import pandas as pd

def agg_calls_by_day(df, date_col="date"):
    """Aggregates call counts by day."""
    if df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=[date_col, 'count'])
    return df.groupby(date_col).size().reset_index(name='count')

def agg_calls_by_hour(df, hour_col="hour"):
    """Aggregates call counts by hour."""
    if df.empty or hour_col not in df.columns:
        return pd.DataFrame(columns=[hour_col, 'count'])
    return df.groupby(hour_col).size().reset_index(name='count')

def category_distribution(df, category_col="category"):
    """Calculates distribution of calls by category."""
    if df.empty or category_col not in df.columns:
        return pd.DataFrame(columns=[category_col, 'count'])
    return df.groupby(category_col).size().reset_index(name='count')

def compute_kpis(df):
    """Computes key performance indicators from the dataframe."""
    if df.empty:
        return {
            "total_calls": 0,
            "avg_per_day": 0,
            "peak_hour": "N/A"
        }

    total_calls = len(df)
    
    # Avg calls per day
    if "date" in df.columns:
        days_in_range = df["date"].nunique()
        avg_per_day = round(total_calls / days_in_range) if days_in_range > 0 else 0
    else:
        avg_per_day = 0

    # Calculate Peak Call Hour
    if "hour" in df.columns and not df["hour"].empty:
        peak_hour_val = df["hour"].mode()[0]
        peak_hour = f"{int(peak_hour_val):02d}:00 - {int(peak_hour_val)+1:02d}:00"
    else:
        peak_hour = "N/A"

    return {
        "total_calls": total_calls,
        "avg_per_day": avg_per_day,
        "peak_hour": peak_hour
    }

def interpret_time_series(ts_df):
    """Generates simple text insights from time series data."""
    if ts_df.empty or len(ts_df) < 2:
        return ["Not enough data for insights."]
    
    insights = []
    peak_day = ts_df.loc[ts_df['count'].idxmax()]
    trough_day = ts_df.loc[ts_df['count'].idxmin()]

    insights.append(f"Highest traffic on **{peak_day['date'].strftime('%Y-%m-%d')}** with {peak_day['count']} calls.")
    insights.append(f"Lowest traffic on **{trough_day['date'].strftime('%Y-%m-%d')}** with {trough_day['count']} calls.")
    
    return insights

def interpret_hourly_distribution(hr_df):
    """Generates insights from hourly call distribution."""
    if hr_df.empty:
        return ["No hourly data available."]
        
    peak_hour = hr_df.loc[hr_df['count'].idxmax()]
    
    # Define time slots
    morning_hours = hr_df[(hr_df['hour'] >= 6) & (hr_df['hour'] < 12)]['count'].sum()
    afternoon_hours = hr_df[(hr_df['hour'] >= 12) & (hr_df['hour'] < 18)]['count'].sum()
    evening_hours = hr_df[(hr_df['hour'] >= 18) & (hr_df['hour'] < 24)]['count'].sum()
    night_hours = hr_df[(hr_df['hour'] >= 0) & (hr_df['hour'] < 6)]['count'].sum()
    
    slots = {"Morning (6-12)": morning_hours, "Afternoon (12-18)": afternoon_hours, 
             "Evening (18-24)": evening_hours, "Night (0-6)": night_hours}
    
    busiest_slot = max(slots, key=slots.get)
    
    insights = [f"Peak activity is around **{int(peak_hour['hour']):02d}:00**, with an average of {peak_hour['count']} calls.",
                f"The busiest time slot is **{busiest_slot}**."]
    return insights