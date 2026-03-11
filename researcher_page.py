"""
PaperIQ Pro - Researcher Page
Full research workspace with deep analysis, comparison, and literature mapping.
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
    # New feature components
    paper_quality_card, journal_recommendations_card, citation_impact_card,
    future_directions_card, project_ideas_card, semantic_search_widget,
    topic_trends_analysis_card, similarity_analysis_card,
)
from utils.styles import sec_color

NAV = [
    ("dashboard", "Dashboard"),
    ("analyze",   "Upload Paper"),
    ("deep",      "Deep Analysis"),
    ("compare",   "Compare Papers"),
    ("chatbot",   "Research Chatbot"),
    ("litmap",    "Literature Map"),
    ("quality",   "Quality & Impact"),
    ("semantic",  "Semantic Search"),
    ("notes",     "Notes"),
    ("export",    "Export & Cite"),
]

def show():
    page = sidebar(NAV, "#1E3A8A")
    if page == "dashboard": _dashboard()
    elif page == "analyze":  _analyze()
    elif page == "deep":     _deep()
    elif page == "compare":  _compare()
    elif page == "chatbot":  _chatbot()
    elif page == "litmap":   _litmap()
    elif page == "quality":  _quality()
    elif page == "semantic": _semantic()
    elif page == "notes":    _notes()
    elif page == "export":   _export_cite()


def _dashboard():
    page_header("Researcher Workspace", "Deep analysis, patent detection & literature mapping")
    papers = st.session_state.get("papers", [])

    # Enhanced hero section with indigo theme for researchers
    st.markdown("""
    <div class="hero-section" style="margin-bottom:2rem;">
      <div style="position:relative;z-index:1;">
        <h1 style="font-family:'Poppins',sans-serif;font-size:2rem;color:#0F172A;
             margin:0 0 .6rem;font-weight:800;letter-spacing:-.02em;">
          🔬 Research Intelligence Hub
        </h1>
        <p style="color:#475569;font-size:1rem;margin:0;line-height:1.7;">
          Deep-dive analysis, methodology extraction, limitation/advantage detection,
          patent identification, cross-paper comparison and literature landscape mapping.
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced metrics with gradient cards and icons
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#EEF2FF;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Papers</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#4F46E5,#6366F1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{len(papers)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
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
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#92400E,#D97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{sum(1 for p in papers if p.get("metadata", {}).get("is_patent", False))}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        unique_models = len({m.get("name", m) for p in papers for m in p.get("models_methods", p.get("models", []))})
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#DCFCE7;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <path d="M3 9h18M9 21V9"></path>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Unique Models</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#059669,#10B981);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{unique_models}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        total_refs = sum(p.get("metadata", {}).get("reference_count", 0) for p in papers)
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;margin-bottom:0.5rem;">
                <div style="width:36px;height:36px;border-radius:10px;background:#DBEAFE;display:flex;align-items:center;justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" stroke-width="2">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                    </svg>
                </div>
                <span style="color:#64748B;font-size:0.75rem;font-weight:600;">Total References</span>
            </div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#1E3A8A,#3B82F6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Poppins',sans-serif;">{total_refs}</div>
        </div>
        """, unsafe_allow_html=True)

    if papers:
        st.markdown("---")
        st.markdown("### Papers Overview")
        rows = []
        for p in papers:
            m = p.get("metadata", {})
            plag = p.get("plagiarism",{})
            rows.append({
                "Title":         m.get("title", "Unknown")[:55]+"..." if len(m.get("title", ""))>55 else m.get("title", "Unknown"),
                "Type":          "Patent" if m.get("is_patent") else "Paper",
                "Domain":        m.get("domain", "Unknown"),
                "Year":          m.get("year", "N/A"),
                "Words":         m.get("word_count", 0),
                "Plagiarism":    f"{plag.get('estimated_pct','N/A')}%",
                "Sentiment":     p.get("sentiment",{}).get("_overall",{}).get("label","N/A"),
                "Models":        ", ".join([m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in (p.get("models_methods", p.get("models", [])))[:3]]) or "N/A",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _analyze():
    page_header("Upload Paper", "Upload and run comprehensive deep analysis")
    paper = upload_widget("researcher", "#4F46E5")
    if not paper:
        return

    paper_banner(paper, "#4F46E5")
    paper_metrics(paper)
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Sections", "Intelligence", "Limitations & Advantages", "Plagiarism", "Trends"
    ])
    with tab1: render_sections(paper)
    with tab2:
        overall_summary_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        patent_info_card(paper)
    with tab3:
        limitations_advantages_card(paper)
    with tab4: plagiarism_card(paper)
    with tab5:
        trends_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        research_gaps_card(paper)


def _deep():
    page_header("Deep Analysis", "Comprehensive paper intelligence")
    paper = paper_selector()
    if not paper:
        return

    paper_banner(paper, "#4F46E5")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Intelligence", "Methodology", "Limitations & Advantages",
        "Plagiarism", "Analytics", "Gaps & Trends"
    ])

    with tab1:
        overall_summary_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        patent_info_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        def _sec_box(name, bg, border):
            secs = paper.get("sections", {})
            if name in secs:
                content = secs[name]
                if isinstance(content, dict):
                    content = content.get("content", "")
                if content:
                    st.markdown(f"**{name}**")
                    st.markdown(f"""
                    <div style="background:{bg};border-radius:10px;padding:.85rem 1rem;
                         border-left:3px solid {border};font-size:.87rem;
                         line-height:1.7;white-space:pre-line;color:#0F172A;margin-bottom:.7rem;">
                      {content[:500]}{'...' if len(content) > 500 else ''}
                    </div>""", unsafe_allow_html=True)

        with col1:
            for n in ["Abstract","Introduction","Background","Problem Statement"]:
                _sec_box(n, "#EFF6FF", "#2563EB")
        with col2:
            for n in ["Conclusion","Future Work","Limitations"]:
                _sec_box(n, "#F0FDF4", "#059669")

    with tab2:
        secs = paper.get("sections", {})
        method_name = next(
            (k for k in ["Methodology","Methods","Proposed Method","Proposed Approach","Framework"]
             if k in secs), None
        )
        if method_name:
            method_content = secs.get(method_name, "")
            if isinstance(method_content, dict):
                method_content = method_content.get("content", "")
            
            if method_content:
                st.markdown("#### Methodology Content")
                st.markdown(f"""
                <div style="background:#FFFBEB;border-radius:10px;padding:1rem 1.2rem;
                     border-left:4px solid #D97706;font-size:.9rem;
                     line-height:1.8;white-space:pre-line;color:#0F172A;margin-bottom:1rem;">
                  {method_content[:1000]}{'...' if len(method_content) > 1000 else ''}
                </div>""", unsafe_allow_html=True)
            with st.expander("Full methodology text"):
                st.write(method_content)
        else:
            st.info("Methodology section not explicitly found - check the Sections tab.")

        models = paper.get("models_methods", [])
        if models:
            st.markdown("#### Detected Models, Algorithms & Tools")
            # Handle both string and dict formats for models
            def get_model_name(m):
                if isinstance(m, dict):
                    return m.get("name", str(m))
                return str(m)
            
            badges = "".join(
                f'<span style="background:#EEF2FF;color:#4338CA;border-radius:20px;'
                f'padding:.25rem .8rem;font-size:.8rem;font-weight:700;'
                f'margin:.18rem;display:inline-block;font-family:monospace;">{get_model_name(m)}</span>'
                for m in models
            )
            st.markdown(badges, unsafe_allow_html=True)

    with tab3:
        limitations_advantages_card(paper)

    with tab4:
        plagiarism_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        sentiment_card(paper)

    with tab5:
        col1, col2 = st.columns(2)
        with col1: section_pie(paper, "researcher_deep_analytics")
        with col2: keyword_chart(paper, "researcher_deep_analytics")

    with tab6:
        trends_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        research_gaps_card(paper)


def _compare():
    page_header("Compare Papers", "Side-by-side AI comparison with Lim & Adv analysis")
    comparison_widget()


def _chatbot():
    page_header("Research Chatbot", "AI-powered Q&A about your paper")
    paper = paper_selector()
    if paper:
        chatbot(paper)


def _litmap():
    page_header("Literature Map", "Visual landscape of your uploaded papers")
    papers = st.session_state.get("papers", [])
    if len(papers) < 2:
        st.info("Upload at least **2 papers** to see the literature map.")
        return

    rows = []
    for p in papers:
        m = p.get("metadata", {})
        plag = p.get("plagiarism", {})
        rows.append({
            "Paper":     m.get("title", "Unknown")[:45]+"...",
            "Type":      "Patent" if m.get("is_patent") else "Research Paper",
            "Domain":    m.get("domain", "Unknown"),
            "ResType":   m.get("research_type", "Unknown"),
            "Year":      int(m.get("year", 2023)) if str(m.get("year", "")).isdigit() else 2023,
            "Words":     m.get("word_count", 0),
            "Sections":  m.get("section_count", 0),
            "Refs":      m.get("reference_count", 0),
            "Plagiarism":plag.get("estimated_pct", 0),
        })
    df = pd.DataFrame(rows)

    fig = px.scatter(
        df, x="Words", y="Sections",
        size="Refs", color="Domain",
        symbol="Type",
        hover_name="Paper", size_max=48,
        hover_data={"Year": True, "ResType": True, "Plagiarism": True},
        color_discrete_sequence=["#2563EB","#DC2626","#059669","#D97706","#4F46E5","#0369A1"],
    )
    fig.update_layout(
        title="Paper Landscape - Word Count vs Sections (size = References)",
        plot_bgcolor='white', paper_bgcolor='white',
        height=420, font=dict(family='Inter'),
        xaxis=dict(title="Word Count",gridcolor='#F1F5F9'),
        yaxis=dict(title="Sections",gridcolor='#F1F5F9'),
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        dc = df["Domain"].value_counts()
        fig2 = go.Figure(go.Bar(
            x=dc.index.tolist(), y=dc.values.tolist(),
            marker=dict(color='#4F46E5', opacity=.85),
            text=dc.values.tolist(), textposition='outside',
        ))
        fig2.update_layout(
            title="Domain Distribution", plot_bgcolor='white', paper_bgcolor='white',
            height=260, font=dict(family='Inter'), margin=dict(t=40,b=20),
            yaxis=dict(title="Count",gridcolor='#F1F5F9'),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        tc = df["Type"].value_counts()
        fig3 = go.Figure(go.Pie(
            labels=tc.index.tolist(), values=tc.values.tolist(),
            hole=0.5,
            marker=dict(colors=["#2563EB","#D97706"],line=dict(color='#fff',width=2)),
        ))
        fig3.update_layout(
            title="Papers vs Patents", paper_bgcolor='white',
            height=260, font=dict(family='Inter'), margin=dict(t=40,b=10,l=0,r=0),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Trends heatmap across papers
    all_trends = {}
    for p in papers:
        for t in p.get("trends", []):
            name = t.get("trend", "Unknown")
            all_trends[name] = all_trends.get(name, 0) + 1

    if all_trends:
        st.markdown("### Trends Across All Papers")
        sorted_trends = sorted(all_trends.items(), key=lambda x: x[1], reverse=True)
        fig4 = go.Figure(go.Bar(
            x=[v for _,v in sorted_trends],
            y=[k for k,_ in sorted_trends],
            orientation='h',
            marker=dict(color=[v for _,v in sorted_trends],
                       colorscale=[[0,"#BFDBFE"],[1,"#1D4ED8"]],showscale=False),
            text=[v for _,v in sorted_trends], textposition='outside',
        ))
        fig4.update_layout(
            title="Trend Frequency Across Papers",
            plot_bgcolor='white', paper_bgcolor='white',
            height=350, font=dict(family='Inter'),
            yaxis=dict(autorange='reversed',gridcolor='#F1F5F9'),
            xaxis=dict(gridcolor='#F1F5F9'),
            margin=dict(l=10,r=60,t=40,b=20),
        )
        st.plotly_chart(fig4, use_container_width=True)


def _quality():
    page_header("Quality & Impact", "Paper quality scoring, recommendations & impact analysis")
    paper = paper_selector()
    if not paper:
        return

    paper_banner(paper, "#4F46E5")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Quality Score", "Journals & Conferences", "Citation Impact",
        "Future Directions", "Project Ideas"
    ])

    with tab1:
        paper_quality_card(paper)

    with tab2:
        journal_recommendations_card(paper)

    with tab3:
        citation_impact_card(paper)

    with tab4:
        future_directions_card(paper)

    with tab5:
        project_ideas_card(paper)


def _semantic():
    page_header("Semantic Search & Trends", "Intelligent search and topic analysis")
    
    tab1, tab2 = st.tabs(["Semantic Search", "Topic Trends"])
    
    with tab1:
        semantic_search_widget()
    
    with tab2:
        papers = st.session_state.get("papers", [])
        topic_trends_analysis_card(papers)


def _notes():
    page_header("Notes", "Your personal research notes and reading list")
    papers = st.session_state.get("papers", [])
    
    # Initialize notes and reading list in session state if not exists
    if "researcher_notes" not in st.session_state:
        st.session_state.researcher_notes = {}
    if "researcher_reading_list" not in st.session_state:
        st.session_state.researcher_reading_list = []
    
    # Create tabs for Notes and Reading List
    tab1, tab2 = st.tabs(["📝 Paper Notes", "📚 Reading List"])
    
    with tab1:
        st.markdown("### Per-Paper Research Notes")
        st.markdown("Add detailed research notes to any paper:")
        
        if not papers:
            st.info("No papers available. Upload papers to add notes.")
        else:
            paper_options = {p.get("name", f"Paper {i}"): i for i, p in enumerate(papers)}
            selected_paper_name = st.selectbox("Select Paper", list(paper_options.keys()), key="res_notes_paper_select")
            selected_paper = papers[paper_options[selected_paper_name]]
            
            current_note = st.session_state.researcher_notes.get(selected_paper_name, "")
            
            st.markdown("#### Your Research Note")
            new_note = st.text_area(
                "Write your research notes here:",
                value=current_note,
                height=180,
                placeholder="Add research observations, methodology notes, research questions, etc...",
                key="res_note_textarea"
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Note", use_container_width=True, key="res_save_note"):
                    st.session_state.researcher_notes[selected_paper_name] = new_note
                    st.success(f"Note saved for {selected_paper_name}!")
            with col2:
                if st.button("🗑️ Clear Note", use_container_width=True, key="res_clear_note"):
                    st.session_state.researcher_notes[selected_paper_name] = ""
                    st.success("Note cleared!")
                    st.rerun()
            with col3:
                if new_note:
                    note_content = f"""
Paper: {selected_paper.get('metadata', {}).get('title', selected_paper_name)}
================================================================================

RESEARCH NOTE:
{new_note}

---
Exported from PaperIQ Pro - Researcher Dashboard
"""
                    st.download_button(
                        "📥 Export Note",
                        data=note_content,
                        file_name=f"research_note_{selected_paper_name.replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="res_export_note"
                    )
            
            if new_note:
                st.markdown("#### Preview")
                st.info(new_note)
    
    with tab2:
        st.markdown("### Research Reading List")
        st.markdown("Bookmark papers for your research:")
        
        if not papers:
            st.info("No papers available. Upload papers to add to reading list.")
        else:
            st.markdown("#### Add to Reading List")
            paper_options_rl = {p.get("name", f"Paper {i}"): i for i, p in enumerate(papers)}
            selected_for_rl = st.selectbox(
                "Select Paper to Bookmark", 
                list(paper_options_rl.keys()),
                key="res_rl_paper_select"
            )
            
            if st.button("➕ Add to Reading List", use_container_width=True, key="res_add_rl"):
                if selected_for_rl not in st.session_state.researcher_reading_list:
                    st.session_state.researcher_reading_list.append(selected_for_rl)
                    st.success(f"Added '{selected_for_rl}' to reading list!")
                else:
                    st.warning("This paper is already in your reading list!")
            
            st.markdown("---")
            
            st.markdown("#### Your Reading List")
            reading_list = st.session_state.researcher_reading_list
            
            if not reading_list:
                st.info("Your reading list is empty. Add papers above!")
            else:
                for idx, rl_paper_name in enumerate(reading_list):
                    rl_paper = None
                    for p in papers:
                        if p.get("name") == rl_paper_name:
                            rl_paper = p
                            break
                    
                    if rl_paper:
                        m = rl_paper.get("metadata", {})
                        plag = rl_paper.get("plagiarism", {})
                        
                        quality_factors = []
                        score = 0
                        
                        plag_pct = plag.get("estimated_pct", 0)
                        if plag_pct < 10:
                            score += 25
                            quality_factors.append("Low plagiarism")
                        elif plag_pct < 30:
                            score += 10
                            quality_factors.append("Moderate plagiarism")
                        
                        word_count = m.get("word_count", 0)
                        if word_count > 5000:
                            score += 25
                            quality_factors.append("Comprehensive")
                        elif word_count > 2000:
                            score += 15
                            quality_factors.append("Medium length")
                        
                        ref_count = m.get("reference_count", 0)
                        if ref_count > 30:
                            score += 25
                            quality_factors.append("Well-referenced")
                        elif ref_count > 10:
                            score += 15
                            quality_factors.append("Adequate references")
                        
                        sent = rl_paper.get("sentiment", {}).get("_overall", {})
                        if sent.get("label") == "Positive":
                            score += 25
                            quality_factors.append("Positive tone")
                        
                        with st.expander(f"📄 {m.get('title', rl_paper_name)[:60]}... (Score: {score}/100)", expanded=False):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"**Domain:** {m.get('domain', 'N/A')}")
                                st.markdown(f"**Year:** {m.get('year', 'N/A')}")
                                st.markdown(f"**Words:** {m.get('word_count', 0):,}")
                            with col2:
                                st.markdown(f"**References:** {m.get('reference_count', 0)}")
                                st.markdown(f"**Plagiarism:** {plag.get('estimated_pct', 'N/A')}%")
                                st.markdown(f"**Sentiment:** {sent.get('label', 'N/A')}")
                            with col3:
                                st.markdown(f"**Quality Score:** {score}/100")
                                if quality_factors:
                                    st.markdown("**Factors:**")
                                    for f in quality_factors:
                                        st.markdown(f"  • {f}")
                            
                            if st.button(f"🗑️ Remove from Reading List", key=f"res_remove_rl_{idx}"):
                                st.session_state.researcher_reading_list.remove(rl_paper_name)
                                st.success("Removed from reading list!")
                                st.rerun()
                
                if reading_list:
                    st.markdown("---")
                    if st.button("🗑️ Clear All Reading List", use_container_width=True, key="res_clear_rl"):
                        st.session_state.researcher_reading_list = []
                        st.success("Reading list cleared!")
                        st.rerun()


def _export_cite():
    page_header("Export & Cite", "Generate citations and export analysis reports")
    papers = st.session_state.get("papers", [])
    
    if not papers:
        st.info("No papers available. Upload papers to generate citations and reports.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📚 Citation Generator")
        st.markdown("Generate citations in various formats:")
        
        # Select paper for citation
        paper_options = {p.get("name", f"Paper {i}"): i for i, p in enumerate(papers)}
        selected_paper_name = st.selectbox(
            "Select Paper for Citation", 
            list(paper_options.keys()),
            key="citation_paper_select"
        )
        selected_paper = papers[paper_options[selected_paper_name]]
        m = selected_paper.get("metadata", {})
        
        # Citation format selection
        citation_format = st.selectbox(
            "Citation Format",
            ["APA", "MLA", "Chicago", "BibTeX"],
            key="citation_format"
        )
        
        # Generate citation
        title = m.get("title", "Unknown Title")
        authors = m.get("authors", "Unknown Authors")
        year = m.get("year", "N/A")
        journal = m.get("journal", "")
        doi = m.get("doi", "")
        
        if citation_format == "APA":
            citation = f"{authors} ({year}). {title}. "
            if journal:
                citation += f"{journal}. "
            if doi:
                citation += f"https://doi.org/{doi}"
        elif citation_format == "MLA":
            citation = f"{authors}. \"{title}.\" "
            if journal:
                citation += f"{journal}, "
            citation += f"{year}."
        elif citation_format == "Chicago":
            citation = f"{authors}. \"{title}.\" "
            if journal:
                citation += f"{journal} "
            citation += f"({year})."
        else:  # BibTeX
            first_author = authors.split(",")[0].split("&")[0].strip().split()[-1] if authors else "Unknown"
            citation = f"@article{{{first_author}{year},\n  author = {{{authors}}},\n  title = {{{title}}},\n  year = {{{year}}},\n"
            if journal:
                citation += f"  journal = {{{journal}}},\n"
            if doi:
                citation += f"  doi = {{{doi}}},\n"
            citation += "}"
        
        st.markdown("#### Generated Citation")
        st.code(citation, language="text")
        
        # Copy citation button
        st.download_button(
            "📥 Download Citation",
            data=citation,
            file_name=f"citation_{selected_paper_name.replace(' ', '_')}.txt",
            mime="text/plain",
            key="download_citation"
        )
    
    with col2:
        st.markdown("### 📄 Export Analysis Report")
        st.markdown("Download comprehensive analysis reports:")
        
        # Select paper for report
        report_paper_name = st.selectbox(
            "Select Paper for Report", 
            list(paper_options.keys()),
            key="report_paper_select"
        )
        report_paper = papers[paper_options[report_paper_name]]
        rm = report_paper.get("metadata", {})
        plag = report_paper.get("plagiarism", {})
        sent = report_paper.get("sentiment", {})
        
        # Generate report
        report = f"""
================================================================================
                      PAPERIQ PRO - RESEARCH ANALYSIS REPORT
================================================================================

FILE INFORMATION
--------------------------------------------------------------------------------
Filename:     {report_paper.get('name', 'N/A')}
Title:       {rm.get('title', 'N/A')}
Authors:     {rm.get('authors', 'N/A')}
Domain:       {rm.get('domain', 'N/A')}
Year:        {rm.get('year', 'N/A')}
Type:        {'Patent' if rm.get('is_patent') else 'Research Paper'}
Journal:     {rm.get('journal', 'N/A')}
DOI:         {rm.get('doi', 'N/A')}

METRICS
--------------------------------------------------------------------------------
Word Count:  {rm.get('word_count', 0):,}
Sections:    {rm.get('section_count', 'N/A')}
References:  {rm.get('reference_count', 0)}

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
        for model in report_paper.get("models_methods", []):
            report += f"- {model.get('name', model)}\n"
        if not report_paper.get("models_methods", []):
            report += "No models detected\n"
        
        report += """
TRENDS IDENTIFIED
--------------------------------------------------------------------------------
"""
        for trend in report_paper.get("trends", []):
            report += f"- {trend.get('trend', 'Unknown')}\n"
        if not report_paper.get("trends", []):
            report += "No trends identified\n"
        
        report += """
LIMITATIONS
--------------------------------------------------------------------------------
"""
        for lim in report_paper.get("limitations", []):
            report += f"- {lim}\n"
        if not report_paper.get("limitations", []):
            report += "No limitations identified\n"
        
        report += """
ADVANTAGES
--------------------------------------------------------------------------------
"""
        for adv in report_paper.get("advantages", []):
            report += f"- {adv}\n"
        if not report_paper.get("advantages", []):
            report += "No advantages identified\n"
        
        report += """
RESEARCH GAPS
--------------------------------------------------------------------------------
"""
        for gap in report_paper.get("research_gaps", []):
            report += f"- {gap}\n"
        if not report_paper.get("research_gaps", []):
            report += "No research gaps identified\n"
        
        report += """
================================================================================
                  Generated by PaperIQ Pro Researcher Dashboard
================================================================================
"""
        
        st.download_button(
            "📥 Download Full Report",
            data=report,
            file_name=f"analysis_report_{report_paper_name.replace(' ', '_')}.txt",
            mime="text/plain",
            key="download_report"
        )
    
    # Export all papers summary
    st.markdown("---")
    st.markdown("### 📊 Export All Papers Summary")
    
    if st.button("📥 Export All Papers Summary", use_container_width=True):
        all_papers_summary = "PAPERIQ PRO - ALL PAPERS SUMMARY\n"
        all_papers_summary += "=" * 80 + "\n\n"
        
        for i, p in enumerate(papers, 1):
            pm = p.get("metadata", {})
            pplag = p.get("plagiarism", {})
            psent = p.get("sentiment", {})
            
            all_papers_summary += f"PAPER {i}: {pm.get('title', 'Unknown')[:60]}...\n"
            all_papers_summary += f"  Domain: {pm.get('domain', 'N/A')}\n"
            all_papers_summary += f"  Year: {pm.get('year', 'N/A')}\n"
            all_papers_summary += f"  Words: {pm.get('word_count', 0):,}\n"
            all_papers_summary += f"  Plagiarism: {pplag.get('estimated_pct', 'N/A')}%\n"
            all_papers_summary += f"  Sentiment: {psent.get('_overall', {}).get('label', 'N/A')}\n"
            all_papers_summary += f"  Models: {len(p.get('models_methods', []))}\n"
            all_papers_summary += f"  Trends: {len(p.get('trends', []))}\n"
            all_papers_summary += "-" * 40 + "\n\n"
        
        st.download_button(
            "📥 Download All Papers Summary",
            data=all_papers_summary,
            file_name="all_papers_summary.txt",
            mime="text/plain",
            key="download_all_summary"
        )

