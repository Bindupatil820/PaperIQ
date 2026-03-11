"""
PaperIQ Pro - User Page
Simple user interface with light theme.
"""
import streamlit as st
import re
from pages.components import (
    sidebar, page_header, upload_widget, paper_selector,
    render_sections, paper_metrics, keyword_chart, section_pie,
    overall_summary_card, chatbot, comparison_widget,
    paper_banner, limitations_advantages_card, plagiarism_card,
    patent_info_card, sentiment_card, research_gaps_card, trends_card,
)

NAV = [
    ("home",     "Home"),
    ("analyze",  "Upload & Analyze"),
    ("papers",   "My Papers"),
    ("chatbot",  "Research Chatbot"),
    ("compare",  "Compare Papers"),
    ("notes",    "Notes"),
]

def show():
    page = sidebar(NAV, "#1E3A8A")
    if page == "home":     _home()
    elif page == "analyze":_analyze()
    elif page == "papers": _my_papers()
    elif page == "chatbot":_chatbot()
    elif page == "compare":_compare()
    elif page == "notes":  _notes()


# Home ----------------------------------------------------------------------
def _home():
    page_header("Welcome to PaperIQ Pro", "Understand any research paper or patent in minutes")
    papers = st.session_state.get("papers", [])

    # Hero banner
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
        From PDF to insights in seconds
      </h1>
      <p style="color:#475569;font-size:.95rem;margin:0 0 1.2rem;
           max-width:540px;line-height:1.65;position:relative;">
        Upload any research paper or patent and get AI-powered deep analysis: section summaries,
        limitations, advantages, plagiarism estimate, sentiment, research gaps, and trend detection.
      </p>
      <div style="display:flex;gap:.6rem;flex-wrap:wrap;position:relative;">
        <span style="background:#F1F5F9;border:1px solid #E2E8F0;
             border-radius:20px;padding:.3rem .9rem;font-size:.78rem;font-weight:600;
             color:#475569;">PDF | DOCX | TXT</span>
        <span style="background:#DBEAFE;border:1px solid #93C5FD;
             border-radius:20px;padding:.3rem .9rem;font-size:.78rem;font-weight:600;
             color:#1E3A8A;">AI Powered (Ollama)</span>
        <span style="background:#FEF3C7;border:1px solid #FDE68A;
             border-radius:20px;padding:.3rem .9rem;font-size:.78rem;font-weight:600;
             color:#92400E;">Patent Detection</span>
        <span style="background:#FEF2F2;border:1px solid #FECACA;
             border-radius:20px;padding:.3rem .9rem;font-size:.78rem;font-weight:600;
             color:#DC2626;">Plagiarism Estimate</span>
      </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Papers Analyzed", len(papers))
    with c2: 
        total_words = sum(p.get("metadata", {}).get("word_count", 0) for p in papers)
        st.metric("Total Words", f"{total_words:,}")
    with c3: st.metric("Chat Messages", len(st.session_state.get("chat_history",[])))

    st.markdown("---")
    st.markdown("### What PaperIQ Pro does")

    features = [
        ("Deep Extraction", "#1E3A8A", "Accurately extracts title, authors, sections, references, models, and metadata from any research paper."),
        ("Limitations & Advantages", "#DC2626", "Automatically identifies what the paper can and cannot do - crucial for research evaluation."),
        ("Plagiarism Estimate", "#D97706", "Heuristic analysis of common phrases and repetition. Download a paraphrased version."),
        ("Patent Detection", "#92400E", "Detects if a document is a patent or a research paper and provides guidance accordingly."),
        ("Sentiment Analysis", "#334155", "Analyzes the tone of each section - positive, neutral, or negative - giving insight into confidence level."),
        ("Trend Identification", "#059669", "Detects which current AI/tech research trends (LLMs, Transformers, Federated Learning, etc.) appear in the paper."),
        ("Research Gap Detection", "#0369A1", "Highlights gaps, limitations, and open problems identified by the authors."),
        ("AI Chatbot", "#1D4ED8", "Ask any question about your paper. Powered by Ollama (local LLM) or smart keyword extraction."),
        ("Paper Comparison", "#0F172A", "Side-by-side comparison of two papers including limitations, advantages, and metadata."),
    ]

    for i in range(0, len(features), 3):
        cols = st.columns(3)
        for j, (ttl, color, desc) in enumerate(features[i:i+3]):
            with cols[j]:
                st.markdown(f"""
                <div style="background:#fff;border-radius:16px;padding:1.4rem 1.5rem;
                     border:1px solid #E2E8F0;border-top:4px solid {color};
                     box-shadow:0 4px 12px rgba(0,0,0,0.05);height:100%;margin-bottom:.8rem;
                     transition: all 0.2s ease;">
                  <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem;">
                      <div style="width:32px;height:32px;border-radius:8px;background:{color}15;display:flex;align-items:center;justify-content:center;">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2">
                              <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                      </div>
                      <h4 style="color:{color};margin:0;font-size:.95rem;
                           font-weight:700;font-family:'Poppins',sans-serif;">{ttl}</h4>
                  </div>
                  <p style="color:#64748B;font-size:.83rem;margin:0;line-height:1.6;">{desc}</p>
                </div>""", unsafe_allow_html=True)


# Upload & Analyze ----------------------------------------------------------------------
def _analyze():
    page_header("Upload & Analyze", "Upload a paper or patent and get instant deep analysis")
    paper = upload_widget("user")
    if not paper:
        return

    paper_banner(paper)
    paper_metrics(paper)
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Sections", "Intelligence", "Limitations & Advantages",
        "Plagiarism", "Sentiment", "Trends & Gaps"
    ])

    with tab1:
        render_sections(paper)

    with tab2:
        overall_summary_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            keyword_chart(paper, "analyze_tab_intelligence")
        with col2:
            section_pie(paper, "analyze_tab_intelligence")

    with tab3:
        patent_info_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        limitations_advantages_card(paper)

    with tab4:
        plagiarism_card(paper)

    with tab5:
        sentiment_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            keyword_chart(paper, "analyze_tab_sentiment")
        with col2:
            section_pie(paper, "analyze_tab_sentiment")

    with tab6:
        trends_card(paper)
        st.markdown("<br>", unsafe_allow_html=True)
        research_gaps_card(paper)

    # Full text download
    st.markdown("---")
    text_content = paper.get("text", "")
    if text_content:
        st.download_button(
            "Download Extracted Text (.txt)",
            data=text_content.encode("utf-8"),
            file_name=f"{paper.get('name', 'paper').rsplit('.',1)[0]}_extracted.txt",
            mime="text/plain",
        )


def _show_references(paper):
    """Show references section with clickable links."""
    secs = paper.get("sections", {})
    refs = secs.get("References", secs.get("references", ""))
    
    if isinstance(refs, dict):
        refs = refs.get("content", "")
    
    if refs and isinstance(refs, str) and refs.strip():
        ref_text = refs
        
        # Make URLs clickable (http/https links)
        ref_text = re.sub(
            r'(https?://[^\s<>\)]+)',
            r'<a href="\1" target="_blank" style="color:#1E3A8A;text-decoration:underline;">\1</a>',
            ref_text
        )
        
        # Make DOI links clickable
        ref_text = re.sub(
            r'(10\.\d{4,}/[^\s<>\)]+)',
            r'<a href="https://doi.org/\1" target="_blank" style="color:#1E3A8A;text-decoration:underline;">\1</a>',
            ref_text
        )
        
        # Split into individual references
        ref_lines = re.split(r'\n(?=\[\d+\]|\d+\.)', ref_text)
        
        st.markdown("#### References")
        for i, ref in enumerate(ref_lines[:100], 1):
            if ref.strip():
                st.markdown(f"<div style='margin-bottom:0.75rem;word-wrap:break-word;line-height:1.6;'>{ref}</div>", unsafe_allow_html=True)
        
        if len(ref_lines) > 100:
            st.caption(f"Showing 100 of {len(ref_lines)} references")
    else:
        st.info("No references section found in this paper.")


# My Papers ----------------------------------------------------------------------
def _my_papers():
    page_header("My Papers", "All papers analysed in this session")
    papers = st.session_state.get("papers", [])
    if not papers:
        st.info("No papers yet. Go to **Upload & Analyze** to get started.")
        return

    # Summary
    total_words = sum(p.get("metadata", {}).get("word_count", 0) for p in papers)
    total_refs = sum(p.get("metadata", {}).get("reference_count", 0) for p in papers)
    avg_plag = 0
    if papers:
        vals = [p.get("plagiarism", {}).get("estimated_pct", 0) for p in papers]
        avg_plag = round(sum(vals) / len(vals), 1) if vals else 0
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Papers", len(papers))
    with c2:
        st.metric("Words", f"{total_words:,}")
    with c3:
        st.metric("References", total_refs)
    with c4:
        st.metric("Avg Plag", f"{avg_plag}%")
    with c5:
        patents = sum(1 for p in papers if p.get("metadata", {}).get("is_patent"))
        st.metric("Patents", patents)

    st.markdown("---")
    st.markdown("### Your Papers")

    for idx, p in enumerate(papers):
        m = p.get("metadata", {})
        patent_tag = "Patent" if m.get("is_patent") else "Paper"
        
        # Get extra metadata
        issn = m.get("issn", "")
        ic_value = m.get("ic_value", "")
        impact_factor = m.get("impact_factor", "")
        
        # Build title with extra info
        title = m.get("title", "Unknown")
        extra_info = []
        if issn:
            extra_info.append(f"ISSN: {issn}")
        if ic_value:
            extra_info.append(f"IC Value: {ic_value}")
        if impact_factor:
            extra_info.append(f"SJ Impact Factor: {impact_factor}")
        
        if extra_info:
            title = f"{title} ({'; '.join(extra_info)})"
        
        with st.expander(f"{patent_tag} - {title[:70]}...", expanded=False):
            paper_banner(p)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**Domain:** {m.get('domain', 'Unknown')}")
                st.write(f"**Type:** {m.get('research_type', 'Unknown')}")
                st.write(f"**Year:** {m.get('year', 'N/A')}")
            with c2:
                st.write(f"**Words:** {m.get('word_count', 0):,}")
                st.write(f"**Sections:** {m.get('section_count', 0)}")
                st.write(f"**References:** {m.get('reference_count', 0)}")
            with c3:
                plag = p.get("plagiarism", {})
                st.write(f"**Plagiarism:** {plag.get('estimated_pct', 'N/A')}% ({plag.get('level','N/A')})")
                st.write(f"**Sentiment:** {p.get('sentiment',{}).get('_overall',{}).get('label','N/A')}")
                st.write(f"**Models:** {len(p.get('models_methods', []))}")

            # Tabs with References
            tabs = st.tabs(["Summary", "Limitations & Advantages", "Trends", "References"])
            with tabs[0]:
                overall_summary_card(p)
            with tabs[1]:
                limitations_advantages_card(p)
            with tabs[2]:
                trends_card(p)
            with tabs[3]:
                _show_references(p)


# Chatbot ----------------------------------------------------------------------
def _chatbot():
    page_header("Research Chatbot", "AI-powered Q&A - ask anything about your paper")
    paper = paper_selector()
    if paper:
        chatbot(paper)


# Compare ----------------------------------------------------------------------
def _compare():
    page_header("Compare Papers", "AI-powered side-by-side paper comparison with Lim & Adv")
    comparison_widget()


# Notes ----------------------------------------------------------------------
def _notes():
    page_header("Notes & Reading List", "Your personal notes and reading list")
    papers = st.session_state.get("papers", [])
    
    # Initialize notes and reading list in session state if not exists
    if "paper_notes" not in st.session_state:
        st.session_state.paper_notes = {}
    if "reading_list" not in st.session_state:
        st.session_state.reading_list = []
    
    # Create tabs for Notes and Reading List
    tab1, tab2 = st.tabs(["📝 Paper Notes", "📚 Reading List"])
    
    with tab1:
        st.markdown("### Per-Paper Notes")
        st.markdown("Add personal notes to any paper in your session:")
        
        if not papers:
            st.info("No papers available. Upload papers to add notes.")
        else:
            # Select paper to add note
            paper_options = {p.get("name", f"Paper {i}"): i for i, p in enumerate(papers)}
            selected_paper_name = st.selectbox("Select Paper", list(paper_options.keys()), key="notes_paper_select")
            selected_paper = papers[paper_options[selected_paper_name]]
            
            # Get current note
            current_note = st.session_state.paper_notes.get(selected_paper_name, "")
            
            # Note text area
            st.markdown("#### Your Note")
            new_note = st.text_area(
                "Write your notes here:",
                value=current_note,
                height=150,
                placeholder="Add your thoughts, observations, or reminders about this paper...",
                key="note_textarea"
            )
            
            # Save/Clear/Export buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Note", use_container_width=True):
                    st.session_state.paper_notes[selected_paper_name] = new_note
                    st.success(f"Note saved for {selected_paper_name}!")
            with col2:
                if st.button("🗑️ Clear Note", use_container_width=True):
                    st.session_state.paper_notes[selected_paper_name] = ""
                    st.success("Note cleared!")
                    st.rerun()
            with col3:
                if new_note:
                    # Export note as text file
                    note_content = f"""
Paper: {selected_paper.get('metadata', {}).get('title', selected_paper_name)}
================================================================================

NOTE:
{new_note}

---
Exported from PaperIQ Pro
"""
                    st.download_button(
                        "📥 Export Note",
                        data=note_content,
                        file_name=f"note_{selected_paper_name.replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            # Show current note if exists
            if new_note:
                st.markdown("#### Preview")
                st.info(new_note)
    
    with tab2:
        st.markdown("### Reading List")
        st.markdown("Bookmark papers for later reading:")
        
        if not papers:
            st.info("No papers available. Upload papers to add to reading list.")
        else:
            # Add to reading list
            st.markdown("#### Add to Reading List")
            paper_options_rl = {p.get("name", f"Paper {i}"): i for i, p in enumerate(papers)}
            selected_for_rl = st.selectbox(
                "Select Paper to Bookmark", 
                list(paper_options_rl.keys()),
                key="rl_paper_select"
            )
            
            if st.button("➕ Add to Reading List", use_container_width=True):
                if selected_for_rl not in st.session_state.reading_list:
                    st.session_state.reading_list.append(selected_for_rl)
                    st.success(f"Added '{selected_for_rl}' to reading list!")
                else:
                    st.warning("This paper is already in your reading list!")
            
            st.markdown("---")
            
            # Show reading list
            st.markdown("#### Your Reading List")
            reading_list = st.session_state.reading_list
            
            if not reading_list:
                st.info("Your reading list is empty. Add papers above!")
            else:
                # Display reading list with quality scores
                for idx, rl_paper_name in enumerate(reading_list):
                    # Find the paper data
                    rl_paper = None
                    for p in papers:
                        if p.get("name") == rl_paper_name:
                            rl_paper = p
                            break
                    
                    if rl_paper:
                        m = rl_paper.get("metadata", {})
                        plag = rl_paper.get("plagiarism", {})
                        
                        # Calculate simple quality score based on available metrics
                        quality_factors = []
                        score = 0
                        
                        # Plagiarism check (lower is better)
                        plag_pct = plag.get("estimated_pct", 0)
                        if plag_pct < 10:
                            score += 25
                            quality_factors.append("Low plagiarism")
                        elif plag_pct < 30:
                            score += 10
                            quality_factors.append("Moderate plagiarism")
                        
                        # Word count (longer papers generally more comprehensive)
                        word_count = m.get("word_count", 0)
                        if word_count > 5000:
                            score += 25
                            quality_factors.append("Comprehensive")
                        elif word_count > 2000:
                            score += 15
                            quality_factors.append("Medium length")
                        
                        # References
                        ref_count = m.get("reference_count", 0)
                        if ref_count > 30:
                            score += 25
                            quality_factors.append("Well-referenced")
                        elif ref_count > 10:
                            score += 15
                            quality_factors.append("Adequate references")
                        
                        # Sentiment (positive confidence is good)
                        sent = rl_paper.get("sentiment", {}).get("_overall", {})
                        if sent.get("label") == "Positive":
                            score += 25
                            quality_factors.append("Positive tone")
                        
                        # Show paper in reading list
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
                            
                            # Remove from reading list button
                            if st.button(f"🗑️ Remove from Reading List", key=f"remove_rl_{idx}"):
                                st.session_state.reading_list.remove(rl_paper_name)
                                st.success("Removed from reading list!")
                                st.rerun()
                
                # Clear all reading list
                if reading_list:
                    st.markdown("---")
                    if st.button("🗑️ Clear All Reading List", use_container_width=True):
                        st.session_state.reading_list = []
                        st.success("Reading list cleared!")
                        st.rerun()

