# modules/festivals_ics.py
import os
import requests
from ics import Calendar
from datetime import datetime
import streamlit as st

# --- Define URL and local file path ---
ICS_URL = "https://www.officeholidays.com/ics/india"
ICS_FILE_PATH = os.path.join("data", "festivals.ics")
DATA_DIR = "data"

def download_and_save_ics():
    """
    Downloads the ICS file from the URL and saves it locally.
    Returns True on success, False on failure.
    """
    try:
        # Ensure the 'data' directory exists
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        response = requests.get(ICS_URL, verify=False) # Added verify=False to bypass SSL issues
        response.raise_for_status()
        
        with open(ICS_FILE_PATH, 'w') as f:
            f.write(response.text)
        
        # The st.info message was removed from here
        return True
    except requests.exceptions.RequestException as e:
        # Errors will still be shown so you can debug if the download fails
        st.error(f"Error downloading festival calendar: {e}. Please check your internet connection.")
        return False

@st.cache_data(ttl=86400)  # cache the parsed data for 24 hours
def fetch_festivals_from_ics():
    """
    Loads festival data. If a local copy exists, it uses it.
    If not, it downloads it from the web, saves it, and then uses it.
    """
    # Check if the local file exists. If not, download it.
    if not os.path.exists(ICS_FILE_PATH):
        # The st.warning message was removed from here
        if not download_and_save_ics():
            return [] # Return empty list if download fails

    # Now, proceed with reading from the local file
    try:
        with open(ICS_FILE_PATH, 'r') as f:
            ics_content = f.read()
        
        cal = Calendar(ics_content)
        
        festivals = []
        for event in cal.events:
            if event.begin and event.end:
                start_dt = event.begin.datetime
                end_dt = event.end.datetime

                # Make datetimes timezone-naive
                if start_dt.tzinfo:
                    start_dt = start_dt.replace(tzinfo=None)
                if end_dt.tzinfo:
                    end_dt = end_dt.replace(tzinfo=None)

                festivals.append((event.name, start_dt, end_dt))
        return festivals
    except Exception as e:
        st.error(f"Error parsing local festival calendar ({ICS_FILE_PATH}): {e}")
        return []