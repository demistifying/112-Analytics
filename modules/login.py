# modules/login.py
import pandas as pd

def check_credentials(username, password, filepath="data/users.xlsx"):
    try:
        df = pd.read_excel(filepath)
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Normalize values
        df['username'] = df['username'].astype(str).str.strip().str.lower()
        df['password'] = df['password'].astype(str).str.strip()

        username = str(username).strip().lower()
        password = str(password).strip()

        user = df[(df['username'] == username) & (df['password'] == password)]

        if not user.empty:
            return user.iloc[0].to_dict()
        return None
    except Exception as e:
        print("Error reading users file:", e)
        return None
