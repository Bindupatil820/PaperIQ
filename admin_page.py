"""
PaperIQ Pro - Admin Page
Full platform control with light theme.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pages.components import (
    sidebar, page_header, upload_widget, paper_selector,
    render_sections, paper_metrics, keyword_chart, section_pie,
    overall_summary_card, chatbot, comparison_widget,
    paper_banner, limitations_advantages_card, plagiarism_card,
    patent_info_card, sentiment_card, research_gaps_card, trends_card,
)

NAV = [
    ("dashboard", "Dashboard"),
    ("analyze",   "Upload Paper"),
    ("deep",      "Deep Analysis"),
    ("compare",   "Compare Papers"),
    ("chatbot",   "Research Chatbot"),
    ("admin",     "Admin Controls"),
    ("reports",   "Reports"),
]

def show():
    page = sidebar(NAV, "#1E3A8A")
    if page == "dashboard": _dashboard()
    elif page == "analyze":  _analyze()
    elif page == "deep":     _deep()
    elif page == "compare":  _compare()
    elif page == "chatbot":  _chatbot()
    elif page == "admin":    _admin()
    elif page == "reports":  _reports()


def _dashboard():
    page_header("Admin Dashboard", "Full platform overview and analytics")
    papers = st.session_state.get("papers", [])

    # Enhanced hero section for admin
    st.markdown("""
    <div class="hero-section" style="margin-bottom:2rem;">
      <div style="position:relative;z-index:1;">
        <h1 style="font-family:'Poppins',sans-serif;font-size:2rem;color:#0F172A;
             margin:0 0 .6rem;font-weight:800;letter-spacing:-.02em;">
          ⚙️ Admin Intelligence Center
        </h1>
        <p style="color:#475569;font-size:1rem;margin:0;line-height:1.7;">
          Full platform control: paper management, analytics, plagiarism oversight, and system status.
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced metrics with gradient cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#DBEAFE;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Total Papers</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#1E3A8A,#3B82F6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{len(papers)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        patents = sum(1 for p in papers if p.get("metadata", {}).get("is_patent"))
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#FEF3C7;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92400E" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 6v6l4 2"></path>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Patents</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#92400E,#D97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{patents}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        domains = len({p.get("metadata", {}).get("domain", "Unknown") for p in papers})
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#EEF2FF;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Domains</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#4F46E5,#6366F1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{domains}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        avg_plag = 0
        if papers:
            vals = [p.get("plagiarism",{}).get("estimated_pct",0) for p in papers]
            avg_plag = round(sum(vals)/len(vals), 1) if vals else 0
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#FEF2F2;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2">
                        <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Avg Plagiarism</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#DC2626,#EF4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{avg_plag}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        high_risk = sum(1 for p in papers if p.get("plagiarism",{}).get("level","") == "High")
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#FEE2E2;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">High Risk</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#B91C1C,#DC2626);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{high_risk}</div>
        </div>
        """, unsafe_allow_html=True)

    if papers:
        st.markdown("---")
        st.markdown("### Papers Registry")
        rows = []
        for p in papers:
            m = p.get("metadata", {})
            plag = p.get("plagiarism",{})
            rows.append({
                "Filename":     p.get("name", "Unknown"),
                "Title":        m.get("title", "Unknown")[:48]+"..." if len(m.get("title", ""))>48 else m.get("title", "Unknown"),
                "Doc Type":     "Patent" if m.get("is_patent") else "Research Paper",
                "Domain":       m.get("domain", "Unknown"),
                "Year":         m.get("year", "N/A"),
                "Words":        m.get("word_count", 0),
                "Plagiarism":   f"{plag.get('estimated_pct','N/A')}% ({plag.get('level','N/A')})",
                "Sentiment":    p.get("sentiment",{}).get("_overall",{}).get("label","N/A"),
                "Models":       len(p.get("models_methods", [])),
                "Trends Found": len(p.get("trends",[])),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Analytics charts
        st.markdown("---")
        st.markdown("### Analytics")
        col1, col2, col3 = st.columns(3)

        with col1:
            domain_counts = {}
            for p in papers:
                d = p.get("metadata", {}).get("domain", "Unknown")
                domain_counts[d] = domain_counts.get(d, 0) + 1
            fig = go.Figure(go.Bar(
                x=list(domain_counts.keys()), y=list(domain_counts.values()),
                marker=dict(color='#4F46E5', opacity=.85),
                text=list(domain_counts.values()), textposition='outside',
            ))
            fig.update_layout(
                title="Domains", plot_bgcolor='white', paper_bgcolor='white',
                height=260, font=dict(family='Inter'), margin=dict(t=35,b=20),
                yaxis=dict(gridcolor='#F1F5F9'),
                xaxis=dict(tickangle=-30),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            sentiment_counts = {}
            for p in papers:
                lbl = p.get("sentiment",{}).get("_overall",{}).get("label","Unknown")
                sentiment_counts[lbl] = sentiment_counts.get(lbl, 0) + 1
            colors_map = {"Positive":"#059669","Neutral":"#4F46E5","Negative":"#DC2626"}
            fig2 = go.Figure(go.Pie(
                labels=list(sentiment_counts.keys()),
                values=list(sentiment_counts.values()),
                hole=0.5,
                marker=dict(colors=[colors_map.get(k,"#64748B") for k in sentiment_counts]),
            ))
            fig2.update_layout(
                title="Sentiment Distribution", paper_bgcolor='white',
                height=260, font=dict(family='Inter'), margin=dict(t=35,b=5,l=0,r=0),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            plag_data = {"Low":0,"Moderate":0,"High":0}
            for p in papers:
                lvl = p.get("plagiarism",{}).get("level","Low")
                plag_data[lvl] = plag_data.get(lvl, 0) + 1
            clrs = {"Low":"#059669","Moderate":"#D97706","High":"#DC2626"}
            fig3 = go.Figure(go.Bar(
                x=list(plag_data.keys()),
                y=list(plag_data.values()),
                marker=dict(color=[clrs.get(k,"#64748B") for k in plag_data]),
                text=list(plag_data.values()), textposition='outside',
            ))
            fig3.update_layout(
                title="Plagiarism Risk Levels", plot_bgcolor='white', paper_bgcolor='white',
                height=260, font=dict(family='Inter'), margin=dict(t=35,b=20),
                yaxis=dict(gridcolor='#F1F5F9'),
            )
            st.plotly_chart(fig3, use_container_width=True)


def _analyze():
    page_header("Upload Paper", "Admin deep analysis")
    paper = upload_widget("admin", "#4F46E5")
    if not paper:
        return
    paper_banner(paper, "#4F46E5")
    paper_metrics(paper)
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Sections", "Limitations & Advantages", "Plagiarism", "Sentiment", "Trends"
    ])
    with tab1: render_sections(paper)
    with tab2:
        patent_info_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        limitations_advantages_card(paper)
    with tab3: plagiarism_card(paper)
    with tab4: sentiment_card(paper)
    with tab5:
        trends_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        research_gaps_card(paper)


def _deep():
    page_header("Deep Analysis", "Full admin analysis suite")
    paper = paper_selector()
    if not paper:
        return
    paper_banner(paper, "#4F46E5")
    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Limitations & Advantages", "Plagiarism", "Analytics"])
    with tab1:
        overall_summary_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        patent_info_card(paper)
    with tab2:
        limitations_advantages_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        research_gaps_card(paper)
    with tab3:
        plagiarism_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        sentiment_card(paper)
    with tab4:
        col1, col2 = st.columns(2)
        with col1: section_pie(paper, "admin_deep_analytics")
        with col2: keyword_chart(paper, "admin_deep_analytics")
        trends_card(paper)


def _compare():
    page_header("Compare Papers", "Admin-level paper comparison")
    comparison_widget()


def _chatbot():
    page_header("Research Chatbot", "AI-powered Q&A")
    paper = paper_selector()
    if paper:
        chatbot(paper)


def _admin():
    page_header("Admin Controls", "Session management and system information")
    
    # Create tabs for admin controls
    tab1, tab2, tab3, tab4 = st.tabs(["🗂️ Session Management", "👥 User Registry", "📊 Login History", "🤖 AI Engine"])
    
    with tab1:
        st.markdown("### Session Management")
        papers = st.session_state.get("papers", [])
        st.info(f"**{len(papers)} paper(s)** loaded in current session.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear All Papers", use_container_width=True):
                st.session_state.papers = []
                st.session_state.chat_history = []
                st.success("All papers cleared.")
                st.rerun()
        with col2:
            if st.button("Clear Chat History", use_container_width=True):
                st.session_state.chat_history = []
                st.success("Chat history cleared.")
        
        # Show current session papers
        if papers:
            st.markdown("#### Current Session Papers")
            for idx, p in enumerate(papers):
                m = p.get("metadata", {})
                with st.expander(f"📄 {m.get('title', p.get('name', 'Unknown'))[:50]}..."):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Domain:** {m.get('domain', 'N/A')}")
                        st.markdown(f"**Type:** {'Patent' if m.get('is_patent') else 'Paper'}")
                    with col2:
                        st.markdown(f"**Words:** {m.get('word_count', 0):,}")
                        st.markdown(f"**References:** {m.get('reference_count', 0)}")
                    with col3:
                        plag = p.get("plagiarism", {})
                        st.markdown(f"**Plagiarism:** {plag.get('estimated_pct', 'N/A')}%")
                        st.markdown(f"**Sentiment:** {p.get('sentiment', {}).get('_overall', {}).get('label', 'N/A')}")
                    
                    if st.button(f"Remove Paper", key=f"remove_paper_{idx}"):
                        st.session_state.papers.pop(idx)
                        st.success("Paper removed!")
                        st.rerun()
    
    with tab2:
        st.markdown("### User Registry")
        st.markdown("Registered users on the platform:")
        
        try:
            from utils.auth import get_registered_users
            users = get_registered_users()
            
            if users:
                # Create user table
                user_data = []
                for username, data in users.items():
                    user_data.append({
                        "Username": username,
                        "Role": data.get("role", "User"),
                        "Created": data.get("created", "N/A")
                    })
                st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
                
                # Role distribution chart
                role_counts = {}
                for u, d in users.items():
                    role = d.get("role", "User")
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                if role_counts:
                    fig = go.Figure(go.Pie(
                        labels=list(role_counts.keys()),
                        values=list(role_counts.values()),
                        hole=0.5,
                        marker=dict(colors=["#1E3A8A", "#4F46E5", "#10B981"])
                    ))
                    fig.update_layout(title="Role Distribution", paper_bgcolor='white', height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.markdown("""
                **Note:** To add new users:
                - Researchers can self-register through the signup form
                - Admin accounts are system-managed
                - Passwords are securely hashed using bcrypt
                """)
            else:
                st.info("No registered users found.")
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with tab3:
        st.markdown("### Login History")
        st.markdown("Recent user activity on the platform:")
        
        try:
            from utils.auth import get_login_history
            login_history = get_login_history(limit=30)
            
            if login_history:
                # Create activity table
                activity_data = []
                for entry in login_history:
                    activity_data.append({
                        "Username": entry.get("username", "Unknown"),
                        "Action": "🔵 Login" if entry.get("action") == "login" else "🔴 Logout",
                        "Role": entry.get("role", "N/A"),
                        "Timestamp": entry.get("timestamp", "N/A")
                    })
                st.dataframe(pd.DataFrame(activity_data), use_container_width=True, hide_index=True)
                
                # Activity timeline
                login_count = sum(1 for e in login_history if e.get("action") == "login")
                logout_count = sum(1 for e in login_history if e.get("action") == "logout")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Logins", login_count)
                with col2:
                    st.metric("Total Logouts", logout_count)
            else:
                st.info("No login history recorded yet. Activity will appear here when users log in.")
                
                # Show placeholder message
                st.markdown("""
                **What gets tracked:**
                - Each successful login with username, role, and timestamp
                - Each logout event
                - Last 100 activities are kept for history
                
                **Note:** Login history starts recording once you deploy this update.
                """)
        except Exception as e:
            st.error(f"Error loading login history: {e}")
    
    with tab4:
        st.markdown("### AI Engine Status")
        
        try:
            from utils.ollama_engine import is_ollama_running, _available_models
            running = is_ollama_running()
        except:
            running = False

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;
                 padding:1.2rem 1.4rem;border-left:4px solid {'#059669' if running else '#DC2626'};">
              <strong>AI Engine (Ollama)</strong><br>
              <span style="color:{'#059669' if running else '#DC2626'};font-size:.9rem;">
                {'🟢 Online' if running else '🔴 Offline - Extractive mode active'}
              </span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            try:
                models = _available_models()
            except:
                models = []
            
            if models:
                st.markdown("**Available Models:**")
                badges = " ".join([
                    f'<span style="background:#EEF2FF;color:#4338CA;border-radius:20px;'
                    f'padding:.25rem .8rem;font-size:.75rem;font-weight:700;margin:.2rem;display:inline-block;">{m}</span>'
                    for m in models
                ])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.info("No models pulled yet. Ollama is running but no models are available.")
        
        if not running:
            st.markdown("---")
            st.markdown("""
            ### 🔧 Ollama Setup Instructions
            
            To enable full AI capabilities, install Ollama:
            
            1. **Download Ollama** from https://ollama.com
            2. **Install** the application
            3. **Pull models** using commands like:
               - `ollama pull llama2`
               - `ollama pull mistral`
               - `ollama pull codellama`
            4. **Restart** the PaperIQ Pro app
            
            Once Ollama is installed and running, the AI features will be fully available.
            """)


def _reports():
    page_header("Reports", "Export and analyze session reports")
    papers = st.session_state.get("papers", [])

    # Hero section
    st.markdown("""
    <div class="hero-section" style="margin-bottom:2rem;">
      <div style="position:relative;z-index:1;">
        <h1 style="font-family:'Poppins',sans-serif;font-size:2rem;color:#0F172A;
             margin:0 0 .6rem;font-weight:800;letter-spacing:-.02em;">
          📊 Admin Reports Center
        </h1>
        <p style="color:#475569;font-size:1rem;margin:0;line-height:1.7;">
          Generate and export comprehensive analysis reports for all uploaded papers.
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Session summary
    st.markdown("### Session Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Papers", len(papers))
    with col2:
        total_words = sum(p.get("metadata", {}).get("word_count", 0) for p in papers)
        st.metric("Total Words", f"{total_words:,}")
    with col3:
        patents = sum(1 for p in papers if p.get("metadata", {}).get("is_patent"))
        st.metric("Patents", patents)

    if not papers:
        st.info("No papers uploaded yet. Upload papers to generate reports.")
        return

    st.markdown("---")

    # Topic trends across all papers
    st.markdown("### Topic Trends Across All Papers")
    
    # Collect all trends from all papers
    all_trends = {}
    for p in papers:
        for trend in p.get("trends", []):
            trend_name = trend.get("trend", "Unknown")
            all_trends[trend_name] = all_trends.get(trend_name, 0) + 1
    
    if all_trends:
        # Sort by count and take top 15
        sorted_trends = sorted(all_trends.items(), key=lambda x: x[1], reverse=True)[:15]
        trend_names = [t[0] for t in sorted_trends]
        trend_counts = [t[1] for t in sorted_trends]
        
        fig = go.Figure(go.Bar(
            x=trend_counts,
            y=trend_names,
            orientation='h',
            marker=dict(color='#4F46E5', opacity=0.85),
            text=trend_counts,
            textposition='outside',
        ))
        fig.update_layout(
            title="Top Trends (All Papers)",
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400,
            font=dict(family='Inter'),
            margin=dict(t=35, b=20, l=200, r=20),
            xaxis=dict(gridcolor='#F1F5F9', title="Frequency"),
            yaxis=dict(tickfont=dict(size=11)),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trends data available yet.")

    st.markdown("---")

    # Per-paper export reports
    st.markdown("### Per-Paper Export Reports")
    st.markdown("Download individual analysis reports for each paper:")
    
    # Function to generate report text
    def generate_report(paper):
        m = paper.get("metadata", {})
        plag = paper.get("plagiarism", {})
        sent = paper.get("sentiment", {})
        
        report = f"""
================================================================================
                      PAPERIQ PRO - ANALYSIS REPORT
================================================================================

FILE INFORMATION
--------------------------------------------------------------------------------
Filename:     {paper.get('name', 'N/A')}
Title:       {m.get('title', 'N/A')}
Domain:       {m.get('domain', 'N/A')}
Year:        {m.get('year', 'N/A')}
Type:        {'Patent' if m.get('is_patent') else 'Research Paper'}
Word Count:  {m.get('word_count', 0):,}
Sections:    {m.get('sections_count', 'N/A')}

PLAGIARISM ANALYSIS
--------------------------------------------------------------------------------
Estimated:   {plag.get('estimated_pct', 'N/A')}%
Level:       {plag.get('level', 'N/A')}

SENTIMENT ANALYSIS
--------------------------------------------------------------------------------
Overall:     {sent.get('_overall', {}).get('label', 'N/A')}
Score:       {sent.get('_overall', {}).get('score', 'N/A')}

DETECTED MODELS & METHODS
--------------------------------------------------------------------------------
"""
        for model in paper.get("models_methods", []):
            report += f"- {model.get('name', str(model)) if isinstance(model, dict) else str(model)}\n"
        
        if not paper.get("models_methods", []):
            report += "No models detected\n"
        
        report += """
TRENDS IDENTIFIED
--------------------------------------------------------------------------------
"""
        for trend in paper.get("trends", []):
            report += f"- {trend.get('trend', 'Unknown')}\n"
        
        if not paper.get("trends", []):
            report += "No trends identified\n"
        
        report += """
LIMITATIONS
--------------------------------------------------------------------------------
"""
        for lim in paper.get("limitations", []):
            report += f"- {lim}\n"
        
        if not paper.get("limitations", []):
            report += "No limitations identified\n"
        
        report += """
ADVANTAGES
--------------------------------------------------------------------------------
"""
        for adv in paper.get("advantages", []):
            report += f"- {adv}\n"
        
        if not paper.get("advantages", []):
            report += "No advantages identified\n"
        
        report += """
================================================================================
                     Generated by PaperIQ Pro Admin Dashboard
================================================================================
"""
        return report

    # Create a table of papers with export buttons
    for idx, p in enumerate(papers):
        m = p.get("metadata", {})
        with st.expander(f"📄 {m.get('title', p.get('name', 'Unknown'))[:60]}..."):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Domain:** {m.get('domain', 'N/A')}")
            with col2:
                st.markdown(f"**Year:** {m.get('year', 'N/A')}")
            with col3:
                st.markdown(f"**Words:** {m.get('word_count', 0):,}")
            
            # Generate and provide download button
            report_text = generate_report(p)
            filename = f"report_{p.get('name', f'paper_{idx+1}').replace(' ', '_')}.txt"
            
            st.download_button(
                label=f"📥 Download Report",
                data=report_text,
                file_name=filename,
                mime="text/plain",
                key=f"download_{idx}"
            )

