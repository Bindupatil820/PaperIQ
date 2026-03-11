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
]

def show():
    page = sidebar(NAV, "#1E3A8A")
    if page == "dashboard": _dashboard()
    elif page == "analyze":  _analyze()
    elif page == "deep":     _deep()
    elif page == "compare":  _compare()
    elif page == "chatbot":  _chatbot()
    elif page == "admin":    _admin()


def _dashboard():
    page_header("Admin Dashboard", "Full platform overview and analytics")
    papers = st.session_state.get("papers", [])

    st.markdown("""
    <div style="background:linear-gradient(135deg,#FFFFFF 0%,#F8FAFC 60%,#EAF2FF 100%);
         border-radius:16px;padding:2.5rem 2.8rem;margin-bottom:1.8rem;
         position:relative;overflow:hidden;border:1px solid #E2E8F0;
         box-shadow:0 4px 6px -1px rgba(0,0,0,0.06),0 2px 4px -1px rgba(0,0,0,0.04);">
      <div style="position:absolute;top:-20px;right:-20px;width:200px;height:200px;
           background:radial-gradient(circle,rgba(30,58,138,.14) 0%,transparent 70%);"></div>
      <div style="position:absolute;bottom:-30px;left:30%;width:180px;height:180px;
           background:radial-gradient(circle,rgba(29,78,216,.10) 0%,transparent 70%);"></div>
      <h1 style="font-family:'Inter',sans-serif;font-size:2rem;color:#0F172A;
           margin:0 0 .6rem;font-weight:800;letter-spacing:-.03em;position:relative;">
        Admin Intelligence Center
      </h1>
      <p style="color:#475569;font-size:.95rem;margin:0 0 1.2rem;
           max-width:540px;line-height:1.65;position:relative;">
        Full platform control: paper management, analytics, plagiarism oversight, and system status.
      </p>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Papers", len(papers))
    with c2:
        patents = sum(1 for p in papers if p.get("metadata", {}).get("is_patent"))
        st.metric("Patents", patents)
    with c3:
        domains = len({p.get("metadata", {}).get("domain", "Unknown") for p in papers})
        st.metric("Domains", domains)
    with c4:
        avg_plag = 0
        if papers:
            vals = [p.get("plagiarism",{}).get("estimated_pct",0) for p in papers]
            avg_plag = round(sum(vals)/len(vals), 1) if vals else 0
        st.metric("Avg Plagiarism", f"{avg_plag}%")
    with c5:
        high_risk = sum(1 for p in papers if p.get("plagiarism",{}).get("level","") == "High")
        st.metric("High Risk", high_risk)

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

    st.markdown("---")
    st.markdown("### System Information")

    try:
        from utils.ollama_engine import is_ollama_running, get_best_model, _available_models
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
            {'Online' if running else 'Offline - Extractive mode active'}
          </span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        try:
            models = _available_models()
        except:
            models = []
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;
             padding:1.2rem 1.4rem;border-left:4px solid #4F46E5;">
          <strong>Available Models</strong><br>
          <span style="font-size:.85rem;color:#64748B;">
            {', '.join(models) if models else 'None pulled yet'}
          </span>
        </div>
        """, unsafe_allow_html=True)

