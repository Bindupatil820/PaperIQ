"""
Clean Western-style SaaS Design System for PaperIQ Pro.
Modern, minimal, professional appearance with glass cards and subtle shadows.
LIGHT THEME - Clean white/gray backgrounds with soft shadows.
ENHANCED VERSION - User-type specific styling, animations, and micro-interactions.
"""

# Design System Constants - Light Theme - Enhanced Version
COLORS = {
    # User-type specific primary colors
    "user_primary": "#1E3A8A",        # Navy blue for users
    "user_primary_dark": "#1E40AF",
    "user_primary_light": "#3B82F6",
    
    "researcher_primary": "#4F46E5",  # Indigo for researchers
    "researcher_primary_dark": "#4338CA",
    "researcher_primary_light": "#6366F1",
    
    "admin_primary": "#0F172A",       # Dark slate for admins
    "admin_primary_dark": "#020617",
    "admin_primary_light": "#334155",
    
    # Legacy support - defaults to user
    "primary": "#1E3A8A",
    "primary_dark": "#1E40AF",
    "primary_light": "#3B82F6",
    
    # Status colors (enhanced)
    "success": "#059669",
    "success_light": "#10B981",
    "success_bg": "#ECFDF5",
    
    "warning": "#D97706",
    "warning_light": "#F59E0B",
    "warning_bg": "#FFFBEB",
    
    "danger": "#DC2626",
    "danger_light": "#EF4444",
    "danger_bg": "#FEF2F2",
    
    "info": "#0EA5E9",
    "info_light": "#38BDF8",
    "info_bg": "#F0F9FF",
    
    # Neutral palette - Slate scale
    "slate_900": "#0F172A",
    "slate_800": "#1E293B",
    "slate_700": "#334155",
    "slate_600": "#475569",
    "slate_500": "#64748B",
    "slate_400": "#94A3B8",
    "slate_300": "#CBD5E1",
    "slate_200": "#E2E8F0",
    "slate_100": "#F1F5F9",
    "slate_50": "#F8FAFC",
    
    # Legacy support
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_elevated": "#FFFFFF",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_tertiary": "#94A3B8",
    "border": "#E2E8F0",
    "border_focus": "#1E3A8A",
    
    # Additional accent colors
    "accent_purple": "#7C3AED",
    "accent_blue": "#0EA5E9",
    "accent_cyan": "#06B6D4",
    "accent_teal": "#14B8A6",
    "accent_orange": "#F97316",
    "accent_pink": "#EC4899",
    "accent_lime": "#84CC16",
}

# Typography
TYPOGRAPHY = {
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "font_heading": "'Poppins', 'Inter', sans-serif",
    "font_body": "'Inter', sans-serif",
}

# Spacing
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
}

# Border Radius - More rounded for modern look
RADIUS = {
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
    "full": "9999px",
}

# Shadows - Soft and subtle for light theme
SHADOWS = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.04)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -1px rgba(0, 0, 0, 0.04)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "glass": "0 8px 32px rgba(31, 38, 135, 0.08)",
    "card": "0 2px 8px rgba(0, 0, 0, 0.04), 0 0 1px rgba(0, 0, 0, 0.1)",
}

# Section Colors for visual distinction
SECTION_COLORS = {
    "Abstract": "#1E3A8A",
    "Introduction": "#0EA5E9",
    "Background": "#06B6D4",
    "Related Work": "#8B5CF6",
    "Literature Review": "#A855F7",
    "Problem Statement": "#F97316",
    "Methodology": "#F59E0B",
    "Methods": "#F59E0B",
    "Proposed Method": "#F59E0B",
    "System Design": "#14B8A6",
    "Architecture": "#0D9488",
    "Implementation": "#0D9488",
    "Experiments": "#22C55E",
    "Experiments & Results": "#22C55E",
    "Results": "#16A34A",
    "Results & Discussion": "#16A34A",
    "Discussion": "#0EA5E9",
    "Evaluation": "#1E3A8A",
    "Analysis": "#8B5CF6",
    "Comparison": "#A855F7",
    "Conclusion": "#DC2626",
    "Future Work": "#B91C1C",
    "Limitations": "#78716C",
    "Advantages": "#059669",
    "Acknowledgements": "#94A3B8",
    "References": "#CBD5E1",
    "Claims": "#F59E0B",
}

def sec_color(name: str) -> str:
    return SECTION_COLORS.get(name, COLORS["primary"])


# CSS Styles with Clean Light Design System
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&display=swap');

:root {{
    --primary: {COLORS['primary']};
    --primary-dark: {COLORS['primary_dark']};
    --primary-light: {COLORS['primary_light']};
    --success: {COLORS['success']};
    --warning: {COLORS['warning']};
    --danger: {COLORS['danger']};
    --bg: {COLORS['background']};
    --surface: {COLORS['surface']};
    --text-primary: {COLORS['text_primary']};
    --text-secondary: {COLORS['text_secondary']};
    --text-tertiary: {COLORS['text_tertiary']};
    --border: {COLORS['border']};
    --radius-sm: {RADIUS['sm']};
    --radius-md: {RADIUS['md']};
    --radius-lg: {RADIUS['lg']};
    --shadow-sm: {SHADOWS['sm']};
    --shadow-md: {SHADOWS['md']};
    --shadow-lg: {SHADOWS['lg']};
    --shadow-xl: {SHADOWS['xl']};
    --shadow-glass: {SHADOWS['glass']};
}}

* {{
    box-sizing: border-box;
}}

html, body {{
    font-family: {TYPOGRAPHY['font_family']};
    background: {COLORS['background']} !important;
    color: {COLORS['text_primary']} !important;
    line-height: 1.6;
}}

.stApp {{
    background: {COLORS['background']} !important;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: {TYPOGRAPHY['font_heading']} !important;
}}

# MainMenu, footer, header {{ visibility: hidden !important; }}

.block-container {{
    padding: {SPACING['xl']} {SPACING['2xl']} !important;
    max-width: 1400px;
    margin: 0 auto;
}}

/* Light Sidebar - Modern SaaS Style */
section[data-testid="stSidebar"], [data-testid="stSidebar"], div[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
    border-right: 1px solid {COLORS['border']} !important;
}}

/* Sidebar branding */
[data-testid="stSidebar"] .stMarkdown {{
    color: {COLORS['text_primary']};
}}

[data-testid="stSidebar"] h1 {{
    color: {COLORS['text_primary']} !important;
    font-weight: 700 !important;
}}

[data-testid="stSidebar"] p {{
    color: {COLORS['text_tertiary']} !important;
}}

[data-testid="stSidebar"] .stRadio label {{
    padding: 0.75rem 1rem;
    border-radius: {RADIUS['md']};
    font-weight: 500;
    color: {COLORS['text_secondary']};
    transition: all 0.2s ease;
    margin-bottom: 0.25rem;
    background: transparent;
}}

[data-testid="stSidebar"] .stRadio label:hover {{
    background: {COLORS['background']};
    color: {COLORS['text_primary']};
    transform: translateX(4px);
}}

[data-testid="stSidebar"] .stRadio [aria-checked="true"] label {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_light']} 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 15px rgba(30, 58, 138, 0.25) !important;
}}

/* Sidebar divider */
[data-testid="stSidebar"] hr {{
    border: none;
    height: 1px;
    background: {COLORS['border']};
    margin: 1rem 0;
}}

/* Glass Card Style - Light theme */
.glass-card {{
    background: {COLORS['surface']};
    border-radius: {RADIUS['lg']};
    padding: {SPACING['lg']};
    box-shadow: {SHADOWS['card']};
    border: 1px solid {COLORS['border']};
    transition: all 0.2s ease;
}}

.glass-card:hover {{
    box-shadow: {SHADOWS['md']};
}}

/* Primary Button - Modern gradient */
.stButton > button {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: {RADIUS['md']} !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(30, 58, 138, 0.25) !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(30, 58, 138, 0.35) !important;
}}

/* Secondary Button */
.stButton > button[kind="secondary"] {{
    background: {COLORS['surface']} !important;
    color: {COLORS['text_secondary']} !important;
    border: 1px solid {COLORS['border']} !important;
}}

.stButton > button[kind="secondary"]:hover {{
    background: {COLORS['background']} !important;
    border-color: {COLORS['primary']} !important;
    color: {COLORS['primary']} !important;
}}

/* Modern Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {{
    border: 1px solid {COLORS['border']} !important;
    border-radius: {RADIUS['md']} !important;
    background: {COLORS['surface']} !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.15s ease;
}}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: {COLORS['primary']} !important;
    box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.12) !important;
    outline: none;
}}

.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {{
    color: {COLORS['text_tertiary']};
}}

/* Modern Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent;
    border: none;
    gap: 0.5rem;
    padding: 0;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border: none;
    border-radius: {RADIUS['md']} {RADIUS['md']} 0 0;
    color: {COLORS['text_secondary']};
    padding: 0.75rem 1.25rem;
    font-weight: 500;
    transition: all 0.15s ease;
}}

.stTabs [data-baseweb="tab"]:hover {{
    color: {COLORS['primary']};
    background: rgba(30, 58, 138, 0.05);
}}

.stTabs [aria-selected="true"] {{
    background: {COLORS['surface']} !important;
    color: {COLORS['primary']} !important;
    font-weight: 600 !important;
    box-shadow: {SHADOWS['sm']};
}}

/* Tab content background */
.stTabs [data-testid="stTabContent"] {{
    background: {COLORS['surface']};
    border-radius: {RADIUS['lg']};
    padding: {SPACING['lg']};
    box-shadow: {SHADOWS['card']};
    border: 1px solid {COLORS['border']};
}}

/* Modern Expander */
.streamlit-expanderHeader {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['md']};
    font-weight: 600;
    padding: 1rem 1.25rem;
    color: {COLORS['text_primary']};
}}

.streamlit-expanderHeader:hover {{
    border-color: {COLORS['primary']};
    background: {COLORS['background']};
}}

.streamlit-expanderContent {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-top: none;
    border-radius: 0 0 {RADIUS['md']} {RADIUS['md']};
    padding: 1rem;
}}

/* Modern Metrics */
[data-testid="metric-container"] {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['lg']};
    padding: 1.25rem;
    box-shadow: {SHADOWS['card']};
}}

[data-testid="stMetricValue"] {{
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['primary_light']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

[data-testid="stMetricLabel"] {{
    font-size: 0.75rem !important;
    color: {COLORS['text_tertiary']};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}}

/* Modern Alerts */
.stAlert {{
    border-radius: {RADIUS['md']};
    border: none;
}}

.stSuccess {{
    background: #ECFDF5;
    border-left: 4px solid {COLORS['success']};
    color: {COLORS['success']};
}}

.stWarning {{
    background: #FFFBEB;
    border-left: 4px solid {COLORS['warning']};
    color: {COLORS['warning']};
}}

.stError {{
    background: #FEF2F2;
    border-left: 4px solid {COLORS['danger']};
    color: {COLORS['danger']};
}}

.stInfo {{
    background: #EFF6FF;
    border-left: 4px solid {COLORS['primary']};
    color: {COLORS['primary']};
}}

/* Modern DataFrame */
.stDataFrame {{
    border-radius: {RADIUS['lg']};
    overflow: hidden;
    box-shadow: {SHADOWS['card']};
    border: 1px solid {COLORS['border']};
}}

/* Progress Bar */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['primary_light']}) !important;
    border-radius: {RADIUS['full']};
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ 
    background: linear-gradient(180deg, #CBD5E1, #94A3B8); 
    border-radius: 10px; 
}}

/* Clean Dividers */
hr {{
    border: none;
    height: 1px;
    background: {COLORS['border']};
    margin: 1.5rem 0;
}}

/* Custom scrollbar for sidebar */
[data-testid="stSidebar"] ::-webkit-scrollbar {{
    width: 4px;
}}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
    background: {COLORS['border']};
    border-radius: 4px;
}}

/* Better selectbox dropdown */
[data-baseweb="popover"] {{
    background: {COLORS['surface']} !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: {RADIUS['md']} !important;
    box-shadow: {SHADOWS['lg']} !important;
}}

/* Toast notifications */
[data-testid="stToast"] {{
    background: {COLORS['surface']} !important;
    border-radius: {RADIUS['md']} !important;
    box-shadow: {SHADOWS['lg']} !important;
}}

/* ============================================
   ENHANCED ANIMATIONS & MICRO-INTERACTIONS
   ============================================ */

/* Fade In Animation */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* Slide In From Right */
@keyframes slideInRight {{
    from {{ opacity: 0; transform: translateX(20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

/* Slide In From Left */
@keyframes slideInLeft {{
    from {{ opacity: 0; transform: translateX(-20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

/* Pulse Animation */
@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}

/* Glow Animation */
@keyframes glow {{
    0%, 100% {{ box-shadow: 0 0 5px rgba(59, 130, 246, 0.3); }}
    50% {{ box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }}
}}

/* Bounce Animation */
@keyframes bounce {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-5px); }}
}}

/* Shimmer Loading Effect */
@keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}

/* Enhanced Card Hover Effects */
.enhanced-card {{
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['lg']};
    background: {COLORS['surface']};
}}

.enhanced-card:hover {{
    transform: translateY(-4px);
    box-shadow: {SHADOWS['lg']};
    border-color: {COLORS['primary_light']};
}}

/* Feature Card Styling */
.feature-card {{
    background: {COLORS['surface']};
    border-radius: {RADIUS['lg']};
    padding: 1.5rem;
    border: 1px solid {COLORS['border']};
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}}

.feature-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['primary_light']});
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease;
}}

.feature-card:hover::before {{
    transform: scaleX(1);
}}

.feature-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}}

/* Metric Card Enhancement */
.metric-card {{
    background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['slate_50']} 100%);
    border-radius: {RADIUS['lg']};
    padding: 1.5rem;
    border: 1px solid {COLORS['border']};
    transition: all 0.3s ease;
}}

.metric-card:hover {{
    border-color: {COLORS['primary_light']};
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}}

/* Hero Section Enhancement */
.hero-section {{
    background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['slate_50']} 50%, #E0E7FF 100%);
    border-radius: {RADIUS['xl']};
    padding: 3rem;
    position: relative;
    overflow: hidden;
    border: 1px solid {COLORS['border']};
}}

.hero-section::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
    border-radius: 50%;
}}

.hero-section::after {{
    content: '';
    position: absolute;
    bottom: -30%;
    left: 10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(79, 70, 229, 0.08) 0%, transparent 70%);
    border-radius: 50%;
}}

/* Sidebar Enhancement */
.sidebar-nav-item {{
    padding: 0.75rem 1rem;
    border-radius: {RADIUS['md']};
    transition: all 0.2s ease;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}}

.sidebar-nav-item:hover {{
    background: {COLORS['slate_100']};
    transform: translateX(4px);
}}

.sidebar-nav-item.active {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_light']} 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);
}}

/* Enhanced Button Styles */
.btn-primary {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
    color: white;
    border: none;
    border-radius: {RADIUS['md']};
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(30, 58, 138, 0.25);
}}

.btn-primary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(30, 58, 138, 0.35);
}}

.btn-secondary {{
    background: {COLORS['surface']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['md']};
    padding: 0.75rem 1.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.btn-secondary:hover {{
    border-color: {COLORS['primary']};
    color: {COLORS['primary']};
    background: {COLORS['slate_50']};
}}

/* Status Badge Enhancements */
.badge {{
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.75rem;
    border-radius: {RADIUS['full']};
    font-size: 0.75rem;
    font-weight: 600;
}}

.badge-success {{
    background: {COLORS['success_bg']};
    color: {COLORS['success']};
}}

.badge-warning {{
    background: {COLORS['warning_bg']};
    color: {COLORS['warning']};
}}

.badge-danger {{
    background: {COLORS['danger_bg']};
    color: {COLORS['danger']};
}}

.badge-info {{
    background: {COLORS['info_bg']};
    color: {COLORS['info']};
}}

/* Enhanced Input Focus */
.input-focused {{
    border-color: {COLORS['primary']} !important;
    box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.15) !important;
    outline: none;
}}

/* Tab Enhancement */
.tab-item {{
    padding: 0.75rem 1.25rem;
    border-radius: {RADIUS['md']} {RADIUS['md']} 0 0;
    transition: all 0.2s ease;
    cursor: pointer;
}}

.tab-item:hover {{
    background: {COLORS['slate_100']};
}}

.tab-item.active {{
    background: {COLORS['surface']};
    color: {COLORS['primary']};
    font-weight: 600;
    box-shadow: {SHADOWS['sm']};
}}

/* Loading Skeleton */
.skeleton {{
    background: linear-gradient(90deg, 
        {COLORS['slate_200']} 25%, 
        {COLORS['slate_100']} 50%, 
        {COLORS['slate_200']} 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: {RADIUS['md']};
}}

/* Divider Enhancement */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        {COLORS['border']} 50%, 
        transparent 100%);
    margin: 1.5rem 0;
}}

/* Section Title Enhancement */
.section-title {{
    font-size: 1.25rem;
    font-weight: 700;
    color: {COLORS['text_primary']};
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, {COLORS['border']}, transparent);
}}

/* Avatar Circle */
.avatar {{
    width: 40px;
    height: 40px;
    border-radius: {RADIUS['full']};
    background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['primary_light']});
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 1rem;
}}

/* Upload Zone Enhancement */
.upload-zone {{
    border: 2px dashed {COLORS['border']};
    border-radius: {RADIUS['xl']};
    padding: 3rem;
    text-align: center;
    transition: all 0.3s ease;
    background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['slate_50']} 100%);
}}

.upload-zone:hover {{
    border-color: {COLORS['primary']};
    background: linear-gradient(135deg, {COLORS['slate_50']} 0%, #E0E7FF 100%);
}}

.upload-zone.dragover {{
    border-color: {COLORS['primary_light']};
    background: #E0E7FF;
    transform: scale(1.02);
}}

/* Icon Container */
.icon-container {{
    width: 48px;
    height: 48px;
    border-radius: {RADIUS['lg']};
    display: flex;
    align-items: center;
    justify-content: center;
}}

.icon-container-sm {{
    width: 32px;
    height: 32px;
    border-radius: {RADIUS['md']};
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* Progress Ring */
.progress-ring {{
    transform: rotate(-90deg);
}}

.progress-ring-circle {{
    transition: stroke-dashoffset 0.35s;
    transform-origin: 50% 50%;
}}

/* Tooltip Enhancement */
.tooltip {{
    position: relative;
    display: inline-block;
}}

.tooltip .tooltiptext {{
    visibility: hidden;
    background-color: {COLORS['slate_800']};
    color: white;
    text-align: center;
    padding: 0.5rem 0.75rem;
    border-radius: {RADIUS['sm']};
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 0.75rem;
    white-space: nowrap;
}}

.tooltip:hover .tooltiptext {{
    visibility: visible;
    opacity: 1;
}}

/* Chart Container Enhancement */
.chart-container {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['lg']};
    padding: 1.5rem;
    box-shadow: {SHADOWS['card']};
}}

/* Responsive Grid */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}}

/* Paper List Item */
.paper-item {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['lg']};
    padding: 1.25rem;
    transition: all 0.2s ease;
    cursor: pointer;
}}

.paper-item:hover {{
    border-color: {COLORS['primary_light']};
    box-shadow: {SHADOWS['md']};
    transform: translateX(4px);
}}

/* Tag/Badge Row */
.tag-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}}

.tag {{
    background: {COLORS['slate_100']};
    color: {COLORS['slate_600']};
    padding: 0.25rem 0.75rem;
    border-radius: {RADIUS['full']};
    font-size: 0.75rem;
    font-weight: 500;
}}

/* Chart Legend Enhancement */
.chart-legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 1rem;
}}

.legend-item {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: {COLORS['text_secondary']};
}}

.legend-color {{
    width: 12px;
    height: 12px;
    border-radius: 3px;
}}

/* Empty State */
.empty-state {{
    text-align: center;
    padding: 3rem;
    color: {COLORS['text_tertiary']};
}}

.empty-state-icon {{
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}}

/* Search Box Enhancement */
.search-box {{
    position: relative;
}}

.search-box input {{
    padding-left: 2.5rem;
}}

.search-box .search-icon {{
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    color: {COLORS['text_tertiary']};
}}

/* Notification Dot */
.notification-dot {{
    position: absolute;
    top: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    background: {COLORS['danger']};
    border-radius: {RADIUS['full']};
    border: 2px solid {COLORS['surface']};
}}
</style>
"""

def card_html(body: str, border: str = COLORS['primary'], padding: str = SPACING['lg']) -> str:
    """Generate a glass card HTML with clean styling."""
    return f'''<div style="background:{COLORS['surface']};border-radius:{RADIUS['lg']};padding:{padding};box-shadow:{SHADOWS['card']};border:1px solid {COLORS['border']};margin-bottom:1rem;">{body}</div>'''
