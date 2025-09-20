import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import re

# Updated Police ranks for signup
POLICE_RANKS = [
    "Director General of Police",
    "Inspector General of Police",
    "Dy. Inspector General of Police",
    "Deputy Commissioner of Police (Selection Grade)",
    "Deputy Commissioner of Police (Junior Management Grade)",
    "Assistant Superintendent of Police",
    "Dy. Superintendent of Police (SDPO)",
    "Police Inspector (P.I.)",
    "Assistant Police Inspector (A.P.I.)",
    "Police Sub Inspector (P.S.I.)",
    "Assistant Police Sub Inspector (A.S.I.)",
    "Head Constable (H.C.)"
]

TOP_OFFICER_RANKS = POLICE_RANKS[:5]  # First 5 ranks

def initialize_session_state():
    """Initialize session state variables for authentication"""
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'show_profile_menu' not in st.session_state:
        st.session_state.show_profile_menu = False
    if 'profile_action' not in st.session_state:
        st.session_state.profile_action = None

def validate_username(username):
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{4,20}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""

def signup_form():
    """Handle user signup"""
    with st.form("signup_form"):
        st.subheader("Create New Account")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
        with col2:
            last_name = st.text_input("Last Name")
            
        username = st.text_input("Username")
        rank = st.selectbox("Select Rank", options=POLICE_RANKS)

        # Police station selection for registration
        station_category = st.selectbox(
            "Select Police Station Category",
            ["North District police stations", "South District police stations", "Other police Stations"]
        )

        if station_category == "North District police stations":
            police_station = st.selectbox("Select Police Station", NORTH_DISTRICT_POLICE_STATIONS)
        elif station_category == "South District police stations":
            police_station = st.selectbox("Select Police Station", SOUTH_DISTRICT_POLICE_STATIONS)
        else:
            police_station = st.selectbox("Select Police Station", OTHER_POLICE_STATIONS)
        
        col3, col4 = st.columns(2)
        with col3:
            password = st.text_input("Create Password", type="password")
        with col4:
            confirm_password = st.text_input("Confirm Password", type="password")
            
        submit = st.form_submit_button("Create Account")

        if submit:
            if not first_name or not last_name:
                st.error("Please enter your full name")
                return
                
            if not validate_username(username):
                st.error("Username must be 4-20 characters long and contain only letters, numbers, and underscores")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            is_valid_password, msg = validate_password(password)
            if not is_valid_password:
                st.error(msg)
                return
            
            try:
                # Create user in Firebase Authentication
                user = auth.create_user(
                    uid=username,  # Using username as UID for simplicity
                    password=password
                )
                
                # Store additional user data in Firestore
                db = firestore.client()
                db.collection('users').document(username).set({
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': username,
                    'rank': rank,
                    'police_station_category': station_category,
                    'police_station': police_station,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
                
                st.success("Account created successfully! Please log in.")
            except Exception as e:
                st.error(f"Error creating account: {str(e)}")

def login_form():
    """Handle user login"""
    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submit = st.form_submit_button("Login")

        if submit:
            try:
                db = firestore.client()
                user_doc = db.collection('users').document(username).get()
                
                if not user_doc.exists:
                    st.error("Invalid username or password")
                    return
                
                user_data = user_doc.to_dict()
                st.session_state.authentication_status = True
                st.session_state.username = username
                st.session_state.user_id = username
                st.session_state.user_data = user_data
                
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error("Invalid username or password")

def show_user_info():
    """Show logged in user info and profile dropdown menu"""
    if st.session_state.user_data:
        user_data = st.session_state.user_data

        # Create a sidebar for profile management instead of popover
        with st.sidebar:
            st.markdown("---")
            st.subheader("👤 Profile Menu")
            
            # Profile action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("👤", help="View Profile", key="view_profile_btn"):
                    st.session_state.profile_action = "profile"
            with col2:
                if st.button("🔑", help="Change Password", key="change_pass_btn"):
                    st.session_state.profile_action = "password"
            with col3:
                if st.button("🚪", help="Logout", key="logout_btn"):
                    st.session_state.profile_action = "logout"

        # Handle profile actions in main area
        if st.session_state.profile_action == "profile":
            with st.expander("👤 Profile Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("First Name", value=user_data.get('first_name', ''), disabled=True, key="profile_fname")
                    st.text_input("Username", value=user_data.get('username', ''), disabled=True, key="profile_username")
                    st.text_input("Police Station", value=user_data.get('police_station', ''), disabled=True, key="profile_station")
                with col2:
                    st.text_input("Last Name", value=user_data.get('last_name', ''), disabled=True, key="profile_lname")
                    st.text_input("Rank", value=user_data.get('rank', ''), disabled=True, key="profile_rank")
                
                if st.button("Close Profile", key="close_profile"):
                    st.session_state.profile_action = None
                    st.rerun()
        
        elif st.session_state.profile_action == "password":
            with st.expander("🔑 Change Password", expanded=True):
                with st.form("change_password_form"):
                    st.subheader("Change Password")
                    current_password = st.text_input("Current Password", type="password")
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")

                    col1, col2 = st.columns(2)
                    with col1:
                        submit_change = st.form_submit_button("Update Password")
                    with col2:
                        cancel_change = st.form_submit_button("Cancel")

                    if submit_change:
                        if new_password != confirm_password:
                            st.error("New passwords do not match!")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters long!")
                        else:
                            is_valid, msg = validate_password(new_password)
                            if not is_valid:
                                st.error(msg)
                            else:
                                try:
                                    # Update password in Firebase Auth
                                    auth.update_user(
                                        st.session_state.user_id,
                                        password=new_password
                                    )
                                    st.success("Password updated successfully!")
                                    st.session_state.profile_action = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating password: {str(e)}")

                    if cancel_change:
                        st.session_state.profile_action = None
                        st.rerun()
        
        elif st.session_state.profile_action == "logout":
            with st.expander("🚪 Logout Confirmation", expanded=True):
                st.warning("⚠️ Are you sure you want to logout?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Logout", type="primary", key="confirm_logout_btn"):
                        # Clear all session state
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.success("Logged out successfully!")
                        st.rerun()
                with col2:
                    if st.button("Cancel", key="cancel_logout_btn"):
                        st.session_state.profile_action = None
                        st.rerun()

def notification_center():
    """Notification center for top officers to send alerts and sub officers to view them."""
    db = firestore.client()
    user_data = st.session_state.user_data
    rank = user_data.get("rank", "")

    st.header("🚨 Notification Center")

    # Top officers can create alerts
    if rank in TOP_OFFICER_RANKS:
        st.subheader("Create Alert for Sub Officers")
        with st.form("create_alert_form"):
            alert_title = st.text_input("Alert Title")
            alert_message = st.text_area("Alert Message")
            caller_name = st.text_input("Name of the Caller")
            caller_location = st.text_input("Location of the Caller")
            location = st.text_input("Deployment Location (optional)")
            submit_alert = st.form_submit_button("Send Alert")

            if submit_alert and alert_title and alert_message:
                # Store alert in Firestore
                db.collection("alerts").add({
                    "title": alert_title,
                    "message": alert_message,
                    "caller_name": caller_name,
                    "caller_location": caller_location,
                    "location": location,
                    "from_officer": user_data["username"],
                    "from_rank": rank,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "active": True
                })
                st.success("Alert sent to sub officers!")

    # Sub officers see alerts - Modified query to work without complex index
    else:
        st.subheader("Alerts from Top Officers")
        try:
            # Simple query without ordering first
            alerts_ref = db.collection("alerts").where("active", "==", True).limit(10)
            alerts = alerts_ref.stream()
            
            # Process results in memory
            alert_list = []
            for alert in alerts:
                alert_data = alert.to_dict()
                alert_data['id'] = alert.id
                if 'timestamp' in alert_data:  # Check if timestamp exists
                    alert_list.append(alert_data)
            
            # Sort in memory by timestamp if available
            if alert_list:
                try:
                    alert_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                except:
                    # If sorting fails, just show the alerts as they are
                    pass
            
            # Display alerts
            if alert_list:
                for alert_data in alert_list[:10]:
                    with st.container():
                        st.markdown(f"""
        **{alert_data.get('title', 'N/A')}**  
        {alert_data.get('message', 'N/A')}  
        👤 **Caller Name:** {alert_data.get('caller_name', 'N/A')}  
        📍 **Caller Location:** {alert_data.get('caller_location', 'N/A')}  
        🚓 **Deployment Location:** {alert_data.get('location', 'N/A')}  
        👮 **Sent by:** {alert_data.get('from_rank', 'N/A')} ({alert_data.get('from_officer', 'N/A')})
        """)
                        st.markdown("---")
            else:
                st.info("No active alerts at the moment.")
                
        except Exception as e:
            st.error(f"Error loading alerts: {str(e)}")
            st.info("Please try refreshing the page.")

# Police station lists
NORTH_DISTRICT_POLICE_STATIONS = [
    "Panaji Police Station",
    "Old Goa Police Station",
    "Agacaim Police Station",
    "Mapusa Police Station",
    "Anjuna Police Station",
    "Pernem Police Station",
    "Colvale Police Station",
    "Porvorim Police Station",
    "Calangute Police Station",
    "Saligao Police Station",
    "Bicholim Police Station",
    "Valpoi Police Station",
    "Mopa Police Station",
    "Mandrem Police Station"
]

SOUTH_DISTRICT_POLICE_STATIONS = [
    "Margao Police Station",
    "Colva Police Station",
    "Curchorem Police Station",
    "Canacona Police Station",
    "Sanguem Police Station",
    "Quepem Police Station",
    "Maina Curtorim Police Station",
    "Fatorda Police Station",
    "Ponda Police Station"
]

OTHER_POLICE_STATIONS = [
    "Traffic Police Station",
    "Cyber Crime Police Station",
    "Women Police Station"
]