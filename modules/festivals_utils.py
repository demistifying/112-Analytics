# modules/festivals_utils.py
import pandas as pd

def filter_significant_festivals(
    festivals_in_range,
    df,
    category='crime',
    top_n=10  # Parameter to get top N festivals
):
    """
    Identifies the top N festivals with the highest number of calls for a specific category.

    Args:
        festivals_in_range (list): List of tuples (name, start_ts, end_ts).
        df (pd.DataFrame): The full dataframe of calls.
        category (str): The category to check for spikes (e.g., 'crime').
        top_n (int): The number of top festivals to return.

    Returns:
        list: A list of dictionaries, each with details of a top festival,
              sorted by the highest call count day.
    """
    if df.empty or not festivals_in_range:
        return []

    # Ensure 'date' column is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Filter for the specific category
    df_cat = df[df['category'].str.lower() == category.lower()]

    if df_cat.empty:
        return []

    festival_crime_stats = []

    for name, fs, fe in festivals_in_range:
        festival_days = pd.date_range(fs, fe, freq='D')
        df_fest = df_cat[df_cat['date'].isin(festival_days)]

        if df_fest.empty:
            continue

        daily_counts = df_fest.groupby('date').size()
        max_day_count = daily_counts.max()
        max_day = daily_counts.idxmax()

        # We need a baseline to calculate percentage, even if not used for filtering
        # For simplicity, we can set a dummy baseline or calculate it as before
        baseline_avg = df_cat[~df_cat['date'].isin(festival_days)].groupby('date').size().mean()
        if pd.isna(baseline_avg) or baseline_avg == 0:
            increase_pct = 100.0  # Assign a high value if no baseline
        else:
            increase_pct = ((max_day_count - baseline_avg) / baseline_avg) * 100

        festival_crime_stats.append({
            'name': name,
            'max_day': max_day.strftime('%Y-%m-%d'),
            'max_count': int(max_day_count),
            'baseline_avg': baseline_avg,
            'max_pct': increase_pct
        })

    # --- NEW LOGIC: Sort by the max count and take the top N ---
    # Sort the list of festivals by 'max_count' in descending order
    sorted_festivals = sorted(festival_crime_stats, key=lambda x: x['max_count'], reverse=True)

    # Return the top N results
    return sorted_festivals[:top_n]