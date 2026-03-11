import os

# Force-disable Streamlit telemetry regardless of launch directory/config precedence.
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

import streamlit as st

from utils.auth import authenticate, register_user, log_login

st.set_page_config(
    page_title="PaperIQ Pro",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

for k, v in {
    "logged_in": False,
    "username": "",
    "role": "User",
    "papers": [],
    "chat_history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def login_page() -> None:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* Modern LIGHT login background */
        .stApp {
            background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 50%, #F1F5F9 100%) !important;
            min-height: 100vh;
        }
        
        /* Login container */
        .login-container {
            background: linear-gradient(155deg, #FFFFFF 0%, #F8FAFC 50%, #EFF6FF 100%);
            border-radius: 28px;
            padding: 3.5rem;
            box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.2), 0 0 1px rgba(30, 58, 138, 0.3);
            border: 1px solid #E2E8F0;
            position: relative;
            overflow: hidden;
        }
        .login-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(30, 58, 138, 0.03) 0%, transparent 50%);
            pointer-events: none;
        }
        
        /* Input styling */
        .stTextInput > label {
            font-weight: 600 !important;
            color: #475569 !important;
            font-size: 0.85rem !important;
            margin-bottom: 8px !important;
            display: block !important;
        }
        .stTextInput > div > div > input {
            border-radius: 12px;
            padding: 14px 16px;
            border: 2px solid #E2E8F0;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            background: #FFFFFF !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #1E3A8A;
            box-shadow: 0 0 0 4px rgba(30, 58, 138, 0.15);
            outline: none;
        }
        .stTextInput > div > div > input::placeholder {
            color: #94A3B8;
        }
        
        /* Selectbox */
        .stSelectbox > label {
            font-weight: 600 !important;
            color: #475569 !important;
            font-size: 0.85rem !important;
            margin-bottom: 8px !important;
            display: block !important;
        }
        .stSelectbox > div > div > div {
            border-radius: 12px;
            padding: 14px 16px;
            border: 2px solid #E2E8F0;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            background: #FFFFFF !important;
        }
        
        /* Primary button */
        .stButton > button {
            border-radius: 12px;
            padding: 14px 24px;
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%) !important;
            border: none !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            color: white !important;
            width: 100%;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 14px rgba(30, 58, 138, 0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(30, 58, 138, 0.4) !important;
        }
        
        /* Alert styling */
        .stAlert {
            border-radius: 12px !important;
            padding: 14px 18px !important;
            border: none !important;
        }
        
        /* Logo */
        .login-logo {
            width: 90px;
            height: 90px;
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #60A5FA 100%);
            border-radius: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
            box-shadow: 0 16px 40px rgba(30, 58, 138, 0.4);
            position: relative;
            overflow: hidden;
        }
        .login-logo::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }
        @keyframes shine {
            0% { transform: translateX(-100%) rotate(45deg); }
            100% { transform: translateX(100%) rotate(45deg); }
        }
        .login-logo svg {
            position: relative;
            z-index: 1;
        }
        .login-title {
            font-family: 'Poppins', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #3B82F6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 8px;
            letter-spacing: -0.02em;
        }
        .login-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #64748B;
            margin: 0 0 28px;
            font-weight: 500;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: #F1F5F9;
            border-radius: 12px;
            padding: 4px;
            gap: 4px;
            margin-bottom: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            font-weight: 600;
            color: #64748B;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(30, 58, 138, 0.25);
        }
        
        /* Divider */
        .divider {
            display: flex;
            align-items: center;
            text-align: center;
            margin: 20px 0;
            color: #94A3B8;
            font-size: 0.8rem;
        }
        .divider::before, .divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #E2E8F0;
        }
        .divider span {
            padding: 0 10px;
        }
        
        .system-note {
            text-align: center;
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid #E2E8F0;
            font-size: 0.75rem;
            color: #94A3B8;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <div style="text-align:center;">
                <div class="login-logo">
                    <svg width="48" height="48" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 10C8 8.89543 8.89543 8 10 8H26C27.1046 8 28 8.89543 28 10V26C28 27.1046 27.1046 28 26 28H10C8.89543 28 8 27.1046 8 26V10Z" fill="white" fill-opacity="0.95"/>
                        <path d="M12 14H24M12 18H20M12 22H22" stroke="#1E3A8A" stroke-width="2" stroke-linecap="round"/>
                        <circle cx="24" cy="22" r="4" fill="#3B82F6"/>
                        <path d="M22.5 22L23.5 23L25.5 21" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <h1 class="login-title">PaperIQ Pro</h1>
                <p class="login-subtitle">AI-Powered Research Insight Platform</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Modern tab design
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            with st.form("login_form"):
                selected_role = st.selectbox("Sign in as", ["User", "Researcher", "Admin"], key="login_role")
                username = st.text_input("Username", placeholder="Enter your username", key="login_user")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                
                if submitted:
                    if username.strip() and password:
                        ok, role = authenticate(username, password)
                        if ok:
                            if role not in {"User", "Researcher", "Admin"}:
                                st.error("Unsupported account role.")
                            elif role != selected_role:
                                st.error(f"This account is registered as '{role}'. Select '{role}' and try again.")
                            else:
                                st.session_state.logged_in = True
                                st.session_state.username = username.strip()
                                st.session_state.role = role
                                # Log the login
                                log_login(username.strip(), role)
                                st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please enter both username and password.")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
                new_password = st.text_input("Password", type="password", placeholder="Create password (min 6 chars)", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="reg_confirm")
                role = st.selectbox("Account Type", ["User", "Researcher"], key="reg_role")
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if reg_submitted:
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif not new_username.strip():
                        st.error("Please enter a username.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        created, msg = register_user(new_username, new_password, role)
                        if created:
                            st.success("Account created! Please sign in.")
                        else:
                            st.error(msg)
        
        st.markdown("""
        <div class="system-note">
            Admin accounts are system-managed
        </div>
        """, unsafe_allow_html=True)


if not st.session_state.logged_in:
    login_page()
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@500;600;700&display=swap');
        [data-testid="stHeader"] {display: none !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        html, body, [class*="css"], .stMarkdown, .stTextInput, .stButton, .stSelectbox, .stRadio {
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Poppins', 'Inter', 'Segoe UI', sans-serif !important;
        }
        
        /* Light Sidebar - Modern SaaS Style */
        section[data-testid="stSidebar"], [data-testid="stSidebar"], div[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 10% 8%, rgba(30, 58, 138, 0.14) 0%, transparent 44%),
                radial-gradient(circle at 88% 92%, rgba(37, 99, 235, 0.12) 0%, transparent 40%),
                linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            border-right: 1px solid #E2E8F0 !important;
        }
        
        [data-testid="stSidebar"] .stRadio label {
            padding: 0.75rem 1rem;
            border-radius: 12px;
            font-weight: 500;
            color: #475569;
            transition: all 0.2s ease;
            margin-bottom: 0.25rem;
            background: transparent;
        }
        
        [data-testid="stSidebar"] .stRadio label:hover {
            background: linear-gradient(135deg, rgba(30, 58, 138, 0.16), rgba(37, 99, 235, 0.10));
            color: #0F172A !important;
            transform: translateX(4px);
        }
        
        [data-testid="stSidebar"] .stRadio [aria-checked="true"] label {
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%) !important;
            color: #fff !important;
            box-shadow: 0 6px 16px rgba(30, 58, 138, 0.32) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    role = st.session_state.role
    if role == "Admin":
        from pages.admin_page import show
    elif role == "Researcher":
        from pages.researcher_page import show
    else:
        from pages.user_page import show
    show()
