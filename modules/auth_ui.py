import streamlit as st
from firebase_auth import goa_police_auth
from user_data import store_police_officer_data, get_police_officer_data, update_last_login, check_username_availability

# Define police ranks
POLICE_RANKS = [
    "Constable",
    "Head Constable (HC)", 
    "Assistant Sub-Inspector (ASI)",
    "Sub-Inspector (SI)",
    "Inspector"
]

DEPARTMENTS = [
    "Traffic Police",
    "Criminal Investigation", 
    "Cyber Crime",
    "Narcotics",
    "Women's Cell", 
    "Special Branch",
    "Armed Police",
    "Railway Police"
]

def initialize_session_state():
    """Initialize session state variables"""
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    if 'officer_data' not in st.session_state:
        st.session_state.officer_data = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

def signup_form():
    """Display police officer registration form"""
    st.subheader("🚔 Police Officer Registration")
    st.markdown("*Register your official account for Goa Police Dashboard*")
    
    with st.form("officer_signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name*", placeholder="Enter your first name")
            rank = st.selectbox("Rank*", POLICE_RANKS, index=0)
            badge_number = st.text_input("Badge Number*", placeholder="Enter your badge number")
            password = st.text_input("Create Password*", type="password", 
                                   help="Minimum 6 characters")
        
        with col2:
            last_name = st.text_input("Last Name*", placeholder="Enter your last name")
            department = st.selectbox("Department*", DEPARTMENTS, index=0)
            station = st.text_input("Police Station", placeholder="Your assigned station")
            confirm_password = st.text_input("Confirm Password*", type="password")
        
        # Additional fields
        phone = st.text_input("Contact Number", placeholder="Mobile number for official use")
        
        st.markdown("---")
        st.markdown("**Login Credentials Preview:**")
        if first_name and last_name and rank:
            st.info(f"Your login name will be: **{first_name} {last_name}** with rank **{rank}**")
        
        signup_button = st.form_submit_button("🚔 Register as Police Officer", use_container_width=True)
        
        if signup_button:
            # Validation
            required_fields = [first_name, last_name, rank, badge_number, password, department]
            if not all(required_fields):
                st.error("❌ Please fill in all required fields marked with *")
                return
            
            if password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            if len(badge_number) < 3:
                st.error("❌ Please enter a valid badge number")
                return
            
            # Check if name-rank combination is available
            is_available = check_username_availability(first_name, last_name, rank)
            if not is_available:
                st.error("❌ This name and rank combination is already registered. Please check your details or contact administrator.")
                return
            
            # Create account
            with st.spinner("Creating your police officer account..."):
                result = goa_police_auth.sign_up(
                    first_name=first_name,
                    last_name=last_name, 
                    rank=rank,
                    badge_number=badge_number,
                    password=password,
                    department=department
                )
            
            if result["success"]:
                user_data = result["user"]
                user_id = user_data["localId"]
                
                # Store additional officer data in Firestore
                store_result = store_police_officer_data(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    rank=rank,
                    badge_number=badge_number,
                    department=department,
                    synthetic_email=user_data["synthetic_email"]
                )
                
                if store_result["success"]:
                    st.success("✅ Police officer account created successfully! 🎉")
                    st.balloons()
                    st.info("📝 **Your Login Credentials:**")
                    st.markdown(f"- **Name:** {first_name} {last_name}")
                    st.markdown(f"- **Rank:** {rank}")
                    st.markdown(f"- **Password:** [Your chosen password]")
                    st.markdown("---")
                    st.info("🔄 Please switch to the Login tab to access your account")
                else:
                    st.warning("⚠️ Account created but failed to store additional data. Please contact administrator.")
            else:
                st.error(f"❌ Failed to create account: {result['error']}")

def login_form():
    """Display police officer login form"""
    st.subheader("🚔 Police Officer Login")
    st.markdown("*Access your Goa Police Dashboard*")
    
    with st.form("officer_login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", placeholder="Enter your first name")
            rank = st.selectbox("Your Rank", POLICE_RANKS, index=0)
        
        with col2:
            last_name = st.text_input("Last Name", placeholder="Enter your last name") 
            password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            login_button = st.form_submit_button("🔐 Login to Dashboard", use_container_width=True)
        
        with col2:
            forgot_password = st.form_submit_button("🔄 Reset Password")
        
        if login_button:
            if not all([first_name, last_name, rank, password]):
                st.error("❌ Please fill in all fields")
                return
                
            with st.spinner("Authenticating police officer..."):
                result = goa_police_auth.sign_in_with_name(first_name, last_name, rank, password)
            
            if result["success"]:
                user_data = result["user"]
                user_id = user_data["localId"]
                
                # Update session state
                st.session_state.authentication_status = True
                st.session_state.user_id = user_id
                st.session_state.officer_data = user_data
                
                # Update last login in Firestore
                update_last_login(user_id)
                
                st.success("✅ Login successful! Welcome to Goa Police Dashboard 🚔")
                st.rerun()
            else:
                st.error(f"❌ Login failed: {result['error']}")
        
        if forgot_password:
            if first_name and last_name and rank:
                st.info("🔧 Password reset functionality will be handled by administrator. Please contact your superior officer.")
            else:
                st.error("❌ Please enter your name and rank first")

def logout():
    """Logout officer and clear session state"""
    st.session_state.authentication_status = None
    st.session_state.officer_data = None
    st.session_state.user_id = None
    st.success("✅ Logged out successfully")
    st.rerun()

def show_officer_info():
    """Display logged-in officer information"""
    if st.session_state.authentication_status:
        user_id = st.session_state.user_id
        
        # Get officer data from Firestore
        officer_info = get_police_officer_data(user_id)
        
        if officer_info["success"]:
            data = officer_info["data"]
            
            with st.sidebar:
                st.success("🚔 **AUTHENTICATED OFFICER**")
                st.markdown("---")
                st.write(f"**👤 Name:** {data.get('display_name', 'Officer')}")
                st.write(f"**🏆 Rank:** {data.get('rank', 'N/A')}")
                st.write(f"**🛡️ Badge:** {data.get('badge_number', 'N/A')}")
                st.write(f"**🏢 Department:** {data.get('department', 'N/A')}")
                st.write(f"**📊 Login Count:** {data.get('login_count', 0)}")
                
                st.markdown("---")
                if st.button("🚪 Logout", use_container_width=True):
                    logout()
        else:
            st.sidebar.error("❌ Failed to load officer data")
