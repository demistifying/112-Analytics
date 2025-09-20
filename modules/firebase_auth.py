import streamlit as st
import requests
import json
from typing import Dict, Optional
import re

class GoaPoliceAuth:
    def __init__(self):
        self.api_key = st.secrets["firebase"]["web_api_key"]
        self.base_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        
    def create_synthetic_email(self, first_name: str, last_name: str, rank: str) -> str:
        """Create a synthetic email from name and rank for Firebase Auth"""
        # Clean names and rank (remove special characters, spaces, convert to lowercase)
        clean_first = re.sub(r'[^a-zA-Z0-9]', '', first_name.lower())
        clean_last = re.sub(r'[^a-zA-Z0-9]', '', last_name.lower())
        clean_rank = re.sub(r'[^a-zA-Z0-9]', '', rank.lower())
        
        # Create unique email format: firstname.lastname.rank@goapolice.internal
        synthetic_email = f"{clean_first}.{clean_last}.{clean_rank}@goapolice.internal"
        return synthetic_email
    
    def sign_up(self, first_name: str, last_name: str, rank: str, badge_number: str, password: str, department: str) -> Dict:
        """Create a new police officer account"""
        # Create synthetic email for Firebase
        synthetic_email = self.create_synthetic_email(first_name, last_name, rank)
        display_name = f"{first_name} {last_name}"
        
        url = f"{self.base_url}:signUp?key={self.api_key}"
        
        payload = {
            "email": synthetic_email,
            "password": password,
            "displayName": display_name,
            "returnSecureToken": True
        }
        
        response = requests.post(url, data=json.dumps(payload))
        
        if response.status_code == 200:
            user_data = response.json()
            # Add custom fields to the response
            user_data['first_name'] = first_name
            user_data['last_name'] = last_name
            user_data['rank'] = rank
            user_data['badge_number'] = badge_number
            user_data['department'] = department
            user_data['synthetic_email'] = synthetic_email
            return {"success": True, "user": user_data}
        else:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            
            # Handle duplicate username scenario
            if "EMAIL_EXISTS" in error_message:
                return {"success": False, "error": "This name and rank combination already exists. Please choose a different combination."}
            
            return {"success": False, "error": error_message}
    
    def sign_in_with_name(self, first_name: str, last_name: str, rank: str, password: str) -> Dict:
        """Sign in using name, rank and password"""
        # Create the same synthetic email format
        synthetic_email = self.create_synthetic_email(first_name, last_name, rank)
        
        url = f"{self.base_url}:signInWithPassword?key={self.api_key}"
        
        payload = {
            "email": synthetic_email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, data=json.dumps(payload))
        
        if response.status_code == 200:
            user_data = response.json()
            return {"success": True, "user": user_data}
        else:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            
            if "EMAIL_NOT_FOUND" in error_message or "INVALID_PASSWORD" in error_message:
                return {"success": False, "error": "Invalid name, rank, or password. Please check your credentials."}
            
            return {"success": False, "error": error_message}
    
    def send_password_reset(self, first_name: str, last_name: str, rank: str) -> Dict:
        """Send password reset (won't work with synthetic emails, but kept for completeness)"""
        synthetic_email = self.create_synthetic_email(first_name, last_name, rank)
        
        url = f"{self.base_url}:sendOobCode?key={self.api_key}"
        
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": synthetic_email
        }
        
        response = requests.post(url, data=json.dumps(payload))
        
        if response.status_code == 200:
            return {"success": True}
        else:
            return {"success": False, "error": "Password reset not available. Please contact administrator."}

# Initialize auth instance
goa_police_auth = GoaPoliceAuth()
