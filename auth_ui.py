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

        # Profile menu in top right corner
        col1, col2 = st.columns([9.8, 0.2])
        with col2:
            if st.button("👤", key="profile_btn", help="Profile Menu", use_container_width=True):
                st.session_state.show_profile_menu = True

            if st.session_state.get("show_profile_menu", False):
                with st.popover(""):
                    selected = st.radio(
                        "",
                        ["👤 Profile", "🔑 Change Password", "🚪 Logout"],
                        index=0,
                        label_visibility="collapsed",
                        key="profile_options"
                    )

                    if selected == "👤 Profile":
                        st.subheader("Profile Information")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.text_input("First Name", value=user_data['first_name'], disabled=True)
                            st.text_input("Username", value=user_data['username'], disabled=True)
                        with col2:
                            st.text_input("Last Name", value=user_data['last_name'], disabled=True)
                            st.text_input("Rank", value=user_data['rank'], disabled=True)

                    elif selected == "🔑 Change Password":
                        with st.form("change_password_form"):
                            st.subheader("Change Password")
                            current_password = st.text_input("Current Password", type="password")
                            new_password = st.text_input("New Password", type="password")
                            confirm_password = st.text_input("Confirm New Password", type="password")

                            if st.form_submit_button("Update Password"):
                                if new_password != confirm_password:
                                    st.error("New passwords do not match!")
                                    return

                                is_valid, msg = validate_password(new_password)
                                if not is_valid:
                                    st.error(msg)
                                    return

                                try:
                                    # Update password in Firebase Auth
                                    auth.update_user(
                                        st.session_state.user_id,
                                        password=new_password
                                    )
                                    st.success("Password updated successfully!")
                                except Exception as e:
                                    st.error(f"Error updating password: {str(e)}")

                    elif selected == "🚪 Logout":
                        # New logout confirmation dialog
                        st.markdown("---")
                        st.warning("Are you sure you want to logout?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yes, Logout", key="confirm_logout"):
                                # Clear all session state
                                for key in list(st.session_state.keys()):
                                    del st.session_state[key]
                                st.success("Logged out successfully!")
                                st.experimental_rerun()
                        with col2:
                            if st.button("Cancel", key="cancel_logout"):
                                st.session_state.show_profile_menu = False
                                st.rerun()

                st.session_state.show_profile_menu = False

def logout_box():
    """Show logout box and redirect to login page"""
    if st.session_state.get("show_logout_confirm", False):
        with st.form("logout_confirmation"):
            st.warning("Are you sure you want to logout?")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Yes, Logout"):
                    # Clear all session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.success("Logged out successfully!")
                    st.experimental_rerun()
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_logout_confirm = False
                    st.session_state.show_profile_menu = False
                    st.rerun()
    else:
        st.session_state.show_logout_confirm = True

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
            alerts_ref = db.collection("alerts").where("active", "==", True).order_by("timestamp", direction="DESCENDING").limit(10)
            alerts = alerts_ref.stream()
            
            # Process results in memory
            alert_list = []
            for alert in alerts:
                alert_data = alert.to_dict()
                alert_data['id'] = alert.id
                if 'timestamp' in alert_data:  # Check if timestamp exists
                    alert_list.append(alert_data)
            
            # Sort in memory
            alert_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            # Display only last 10 alerts
            if alert_list:
                for alert_data in alert_list[:10]:
                    with st.container():
                        st.markdown(f"""
        <strong style='font-size:1.1em'>{alert_data['title']}</strong><br>
        {alert_data['message']}<br>
        👤 Caller Name: {alert_data.get('caller_name', 'N/A')}<br>
        📍 Caller Location: {alert_data.get('caller_location', 'N/A')}<br>
        🚓 Deployment Location: {alert_data.get('location', 'N/A')}<br>
        👮 Sent by: {alert_data['from_rank']} ({alert_data['from_officer']})
        """, unsafe_allow_html=True)
            else:
                st.write("No active alerts.")
                
        except Exception as e:
            st.error(f"Error loading alerts: {str(e)}")
            st.write("Please try refreshing the page.")

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
    # Add your South District stations here
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
    # Add any other stations here
    "Traffic Police Station",
    "Cyber Crime Police Station",
    "Women Police Station"
]