import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime

def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def store_police_officer_data(user_id: str, first_name: str, last_name: str, rank: str, 
                             badge_number: str, department: str, synthetic_email: str):
    """Store police officer data in Firestore"""
    try:
        db = initialize_firebase()
        
        # Create a unique username for search purposes
        username = f"{first_name.lower()}.{last_name.lower()}.{rank.lower()}"
        
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "display_name": f"{first_name} {last_name}",
            "rank": rank,
            "badge_number": badge_number,
            "department": department,
            "username": username,  # For easy searching
            "synthetic_email": synthetic_email,  # Store the synthetic email used
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "user_type": "police_officer",
            "active": True,
            "login_count": 1
        }
        
        # Store user data
        db.collection("police_officers").document(user_id).set(user_data)
        
        # Also store in usernames collection for quick lookup
        db.collection("usernames").document(username).set({
            "user_id": user_id,
            "display_name": f"{first_name} {last_name}",
            "rank": rank,
            "created_at": datetime.now()
        })
        
        return {"success": True, "message": "Police officer data stored successfully"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_police_officer_data(user_id: str):
    """Retrieve police officer data from Firestore"""
    try:
        db = initialize_firebase()
        
        officer_ref = db.collection("police_officers").document(user_id)
        officer_doc = officer_ref.get()
        
        if officer_doc.exists:
            return {"success": True, "data": officer_doc.to_dict()}
        else:
            return {"success": False, "error": "Police officer not found"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_last_login(user_id: str):
    """Update officer's last login timestamp and increment login count"""
    try:
        db = initialize_firebase()
        
        officer_ref = db.collection("police_officers").document(user_id)
        officer_ref.update({
            "last_login": datetime.now(),
            "login_count": firestore.Increment(1)
        })
        
        return {"success": True}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_username_availability(first_name: str, last_name: str, rank: str):
    """Check if the name-rank combination is already taken"""
    try:
        db = initialize_firebase()
        username = f"{first_name.lower()}.{last_name.lower()}.{rank.lower()}"
        
        username_ref = db.collection("usernames").document(username)
        username_doc = username_ref.get()
        
        return not username_doc.exists  # True if available, False if taken
    
    except Exception as e:
        return False  # Assume not available on error
