"""
PaperIQ Pro - Clean Western-style SaaS UI Components
Modern design with glass cards, clean typography, and tabbed section analysis.
"""
import re
import html
import io
import hashlib
from collections import Counter
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from utils.extractor import (
    extract_text, clean_text, identify_sections, analyze_sections,
    extract_metadata, extract_keywords, extract_models,
    extract_limitations, extract_advantages,
    estimate_plagiarism, generate_paraphrased_excerpt,
    analyze_sentiment, detect_research_gaps, identify_trends,
    calculate_paper_quality, calculate_similarity,
    recommend_journals_conferences, analyze_citation_impact,
    suggest_future_directions, analyze_topic_trends,
    semantic_search, generate_project_ideas,
)
from utils.ollama_engine import (
    summarize_paper, answer_question, compare_papers, is_ollama_running,
    get_best_model, extract_limits_advantages_ai,
)
from utils.styles import CSS, sec_color, card_html, COLORS, SPACING, RADIUS, SHADOWS

ANALYSIS_VERSION = "2026-03-03-v3"


def _sanitize_text(value: str, max_len: int | None = None) -> str:
    """Clean text - remove HTML and encoding issues for proper display."""
    if not value:
        return "N/A"
    
    s = str(value)
    # Decode HTML entities
    s = html.unescape(s)
    # Remove ALL HTML tags
    s = re.sub(r"(?is)<[^>]+>", " ", s)
    # Remove style/class attributes
    s = re.sub(r"(?i)\b(style|class|href|target)\s*=\s*(\".*?\"|'.*?'|\S+)", " ", s)
    # Fix common encoding issues
    replacements = {
        "Ã‚Â·": " | ", "Ã¢â‚¬Â¢": "- ", "Ã¢â‚¬": "-", "Ã¢â‚¬": "-",
        "Ã¢â‚¬Ëœ": "'", "Ã¢â‚¬â„¢": "'", "Ã¢â‚¬Å“": '"', "Ã¢â‚¬": '"', "Ã¢â‚¬Â¦": "...",
        "\u00a0": " ", "\ufeff": "",
    }
    for bad, good in replacements.items():
        s = s.replace(bad, good)
    # Clean whitespace
    s = re.sub(r"\s+", " ", s).strip(" -|,;:")
    
    if not s:
        return "N/A"
    if max_len and len(s) > max_len:
        s = s[: max_len - 3].rstrip() + "..."
    return s


def _clean_for_display(text: str) -> str:
    """Fully sanitize text for safe display - removes all HTML."""
    if not text:
        return ""
    # Complete HTML removal
    text = html.unescape(text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    # Replace all types of whitespace (including newlines) with single space
    text = re.sub(r"\s+", " ", text)
    # Ensure proper spacing after punctuation
    text = re.sub(r"([.!?])\s*", r"\1 ", text)
    # Remove multiple spaces that may result from the above
    text = re.sub(r" +", " ", text)
    return text.strip()


def _clean_multiline_for_display(text: str) -> str:
    """Sanitize while preserving line breaks for section/full-text display."""
    if not text:
        return ""
    text = html.unescape(str(text))
    text = re.sub(r"(?is)<[^>]+>", "", text)
    # Replace all whitespace with single space
    text = re.sub(r"\s+", " ", text)
    # Ensure proper spacing after punctuation
    text = re.sub(r"([.!?])\s*", r"\1 ", text)
    # Remove multiple spaces
    text = re.sub(r" +", " ", text)
    return text.strip()


def _to_points(value: str, max_items: int = 5) -> list[str]:
    """Convert free text or bullet text into clean point list."""
    cleaned = _clean_multiline_for_display(value)
    if not cleaned:
        return []

    points = []
    for line in cleaned.split("\n"):
        ln = line.strip()
        if not ln:
            continue
        ln = re.sub(r"^[-*•\d\.\)\s]+", "", ln).strip()
        if ln:
            points.append(ln)

    # If text is paragraph-like, split into sentences for points.
    if len(points) <= 1:
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        points = [s.strip(" -") for s in sentences if 25 <= len(s.strip()) <= 240]

    uniq = []
    seen = set()
    for p in points:
        key = re.sub(r"[^a-z0-9]+", "", p.lower())[:120]
        if key and key not in seen:
            uniq.append(p)
            seen.add(key)
    return uniq[:max_items]


def _section_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("content", ""))
    return ""


def _build_quick_summary(text: str, sections: dict) -> str:
    """Fast summary used during upload to avoid long AI latency."""
    candidates = [
        _section_text(sections.get("Abstract")),
        _section_text(sections.get("Introduction")),
        _section_text(sections.get("Methodology")),
        _section_text(sections.get("Results")),
        _section_text(sections.get("Conclusion")),
    ]
    merged = " ".join([c for c in candidates if c]).strip()
    if not merged:
        merged = text[:10000]

    merged = re.sub(r"\s+", " ", merged)
    sents = re.split(r"(?<=[.!?])\s+", merged)
    sents = [s.strip() for s in sents if 30 <= len(s.strip()) <= 220]
    if not sents:
        return merged[:1200]
    return " ".join(sents[:5])[:1400]


def _analyze_uploaded_file(uploaded_file, save_to_library: bool = False):
    """Analyze uploaded file once and optionally add to session library."""
    if not uploaded_file:
        return None

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()

    cache = st.session_state.setdefault("paper_cache", {})
    papers = st.session_state.setdefault("papers", [])

    cached_paper = cache.get(file_hash)
    if cached_paper and cached_paper.get("analysis_version") == ANALYSIS_VERSION:
        if save_to_library and not any(p.get("fingerprint") == file_hash for p in papers):
            papers.append(cached_paper)
        return cached_paper

    raw_text = extract_text(io.BytesIO(file_bytes), uploaded_file.name)
    text = clean_text(raw_text)
    secs = identify_sections(text)
    section_analysis = analyze_sections(secs)
    meta = extract_metadata(text, secs)
    # Ensure title/authors are always present for UI.
    if not meta.get("title") or str(meta.get("title")).strip().lower() in {"n/a", "untitled"}:
        base_name = uploaded_file.name.rsplit(".", 1)[0]
        meta["title"] = re.sub(r"[_\-]+", " ", base_name).strip().title() or uploaded_file.name
    if not meta.get("authors") or str(meta.get("authors")).strip().lower() in {"n/a", "unknown"}:
        meta["authors"] = "Authors not detected"
    kws = extract_keywords(text)
    mods = extract_models(text)
    lims = extract_limitations(text, secs)
    advs = extract_advantages(text, secs)
    plag = estimate_plagiarism(text)
    sent = analyze_sentiment(secs)
    gaps = detect_research_gaps(text, secs)
    trends = identify_trends(text)
    ai_summary = _build_quick_summary(text, secs)

    quality = calculate_paper_quality(text, secs, meta)
    recs = recommend_journals_conferences({"metadata": meta, "quality_score": quality})
    impact = analyze_citation_impact({"metadata": meta, "sections": secs, "full_text": text})
    future = suggest_future_directions({"research_gaps": gaps, "limitations": lims, "trends": trends, "metadata": meta})
    projects = generate_project_ideas(
        {
            "metadata": meta,
            "models_methods": mods,
            "keywords": kws,
            "limitations": lims,
            "research_gaps": gaps,
        }
    )

    paper = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "name": uploaded_file.name,
        "text": text,
        "sections": secs,
        "section_analysis": section_analysis,
        "metadata": meta,
        "keywords": kws,
        "models": mods,
        "models_methods": mods,
        "limitations": lims,
        "advantages": advs,
        "plagiarism": plag,
        "sentiment": sent,
        "research_gaps": gaps,
        "trends": trends,
        "quality_score": quality,
        "journal_recommendations": recs,
        "citation_impact": impact,
        "future_directions": future,
        "project_ideas": projects,
        "ai_summary": ai_summary,
        "fingerprint": file_hash,
        "analysis_version": ANALYSIS_VERSION,
    }

    cache[file_hash] = paper
    if save_to_library and not any(p.get("fingerprint") == file_hash for p in papers):
        papers.append(paper)
    return paper


# ============================================================================
# SIDEBAR & NAVIGATION
# ============================================================================

def _logout_session():
    """Clear auth/session state and return to login screen."""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = "User"
    st.session_state.nav = None
    st.session_state.nav_index = {}
    st.session_state.current_paper = None
    st.session_state.papers = []
    st.session_state.paper_cache = {}
    st.session_state.chat_history = []
    for key in ["_keyword_chart_counter", "_section_pie_counter"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def sidebar(nav_items, accent_color="#1E3A8A"):
    """Clean modern sidebar with navy-blue styling and navigation."""
    if "_global_style_loaded" not in st.session_state:
        st.markdown(CSS, unsafe_allow_html=True)
        st.session_state["_global_style_loaded"] = True

    with st.sidebar:
        # Enhanced branding with logo
        st.markdown(f"""
        <div style="
            text-align:center;padding:1.2rem 0 1.5rem;margin-bottom:0.8rem;
            border-radius:18px;border:1px solid {accent_color}35;
            background:linear-gradient(145deg,{accent_color}15 0%,#FFFFFF 60%,{accent_color}08 100%);
        ">
            <div style="
                width:64px;height:64px;margin:0 auto 0.6rem;
                background:linear-gradient(135deg,{accent_color} 0%,#3B82F6 100%);
                border-radius:16px;
                display:flex;align-items:center;justify-content:center;
                box-shadow:0 8px 24px {accent_color}40;
            ">
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 10C8 8.89543 8.89543 8 10 8H26C27.1046 8 28 8.89543 28 10V26C28 27.1046 27.1046 28 26 28H10C8.89543 28 8 27.1046 8 26V10Z" fill="white" fill-opacity="0.95"/>
                    <path d="M12 14H24M12 18H20M12 22H22" stroke="#1E3A8A" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="24" cy="22" r="4" fill="#3B82F6"/>
                    <path d="M22.5 22L23.5 23L25.5 21" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h1 style="font-size:1.35rem;font-weight:800;margin:0;color:#0F172A;letter-spacing:-0.02em;">
                PaperIQ Pro
            </h1>
            <p style="color:#64748B;font-size:0.75rem;margin:0.3rem 0 0;font-weight:500;">
                Research Intelligence
            </p>
        </div>
        <hr style="border-color:{accent_color}22;margin:0.8rem 0 1rem;">
        """, unsafe_allow_html=True)

        if st.session_state.get("logged_in"):
            username = _sanitize_text(st.session_state.get("username", "Account"), max_len=24)
            role = _sanitize_text(st.session_state.get("role", "User"), max_len=20)
            st.markdown(f"""
            <div style="
                border:1px solid {accent_color}2E;
                border-radius:12px;
                padding:0.65rem 0.8rem 0.55rem;
                background:linear-gradient(135deg,#FFFFFF 0%,#F8FAFC 100%);
                margin-bottom:0.75rem;
            ">
                <div style="font-size:0.74rem;color:#64748B;margin-bottom:0.1rem;">Signed in as</div>
                <div style="font-size:0.94rem;font-weight:700;color:#0F172A;line-height:1.2;">{username}</div>
                <div style="margin-top:0.35rem;display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;
                    background:{accent_color}15;color:{accent_color};font-size:0.72rem;font-weight:700;">
                    {role}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Logout", key="sidebar_logout_btn", use_container_width=True):
                _logout_session()

        st.session_state["nav"] = st.radio(
            "Navigation",
            [x[1] for x in nav_items],
            label_visibility="collapsed",
            index=list(st.session_state.get("nav_index", {}).keys())[0]
            if "nav_index" in st.session_state and st.session_state.nav_index
            else 0,
        )

        for i, (key, label) in enumerate(nav_items):
            if label == st.session_state.get("nav"):
                st.session_state.nav_index = {i: True}
                return key
        return nav_items[0][0]


# ============================================================================
# PAGE HEADER
# ============================================================================

def page_header(title: str, subtitle: str = ""):
    """Clean page header with enhanced design."""
    st.markdown(f"""
    <div style="margin-bottom:2rem;position:relative;">
        <h1 style="font-size:2rem;font-weight:700;color:{COLORS['text_primary']};margin:0;letter-spacing:-0.02em;position:relative;">
            {title}
            <div style="
                position: absolute;
                bottom: -8px;
                left: 0;
                width: 60px;
                height: 4px;
                background: linear-gradient(90deg, #1E3A8A, #3B82F6);
                border-radius: 2px;
            "></div>
        </h1>
        {f'<p style="color:{COLORS["text_secondary"]};font-size:1rem;margin:0.8rem 0 0;font-weight:400;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# MODERN UPLOAD WIDGET - Drag & Drop Card
# ============================================================================

def upload_widget(user_type=None, accent_color=None):
    """Centered, minimal upload card - LARGER SIZE."""
    accent_color = accent_color or COLORS['primary']
    _, center, _ = st.columns([0.8, 2.0, 0.8])
    with center:
        st.markdown(f"""
        <div style="
            background: linear-gradient(160deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 2px dashed {accent_color}85;
            border-radius: 32px;
            padding: 4rem 2.5rem;
            text-align: center;
            margin: 0 0 1.5rem 0;
            box-shadow: {SHADOWS['md']};
            min-height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        ">
            <div style="
                font-size: 4rem;
                margin-bottom: 1rem;
                opacity: 0.9;
            ">📄</div>
            <h3 style="color:{COLORS['text_primary']};font-size:1.5rem;font-weight:700;margin:0 0 0.5rem;">
                Upload Research Paper
            </h3>
            <p style="color:{COLORS['text_secondary']};font-size:1.05rem;margin:0;max-width:90%;">
                PDF, DOCX, or TXT. Section-wise extraction and structured analysis are generated automatically.
            </p>
            <div style="
                margin-top: 1rem;
                padding: 0.5rem 1rem;
                background: {accent_color}10;
                border-radius: 20px;
                font-size: 0.85rem;
                color: {accent_color};
                font-weight: 500;
            ">
                Drag & drop or click to browse
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload your research paper",
            type=["pdf", "docx", "doc", "txt"],
            label_visibility="collapsed",
            help="Supported formats: PDF, DOCX, TXT",
            key=f"upload_widget_{user_type or 'default'}",
        )
    
    if uploaded:
        with st.spinner("Extracting text, identifying sections, and preparing analysis..."):
            paper = _analyze_uploaded_file(uploaded, save_to_library=True)
            st.session_state.current_paper = paper

        st.success(f"Successfully analyzed: {uploaded.name}")
        return paper
    return None


# ============================================================================
# PAPER SELECTOR
# ============================================================================

def paper_selector():
    """Clean paper selector dropdown with enhanced display."""
    papers = st.session_state.get("papers", [])
    if not papers:
        st.info("📭 No papers uploaded yet. Go to 'Upload Paper' to add one.")
        return None
    
    # If only one paper, show it directly with more info
    if len(papers) == 1:
        p = papers[0]
        meta = p.get("metadata", {})
        title = _sanitize_text(meta.get("title", p.get("name", "Untitled")), max_len=60)
        domain = meta.get("domain", "Unknown")
        is_patent = meta.get("is_patent", False)
        
        # Set colors based on patent status
        badge_bg = "#FEF3C7" if is_patent else "#DBEAFE"
        badge_color = "#92400E" if is_patent else "#1E3A8A"
        badge_text = "📋 PATENT" if is_patent else "📄 PAPER"
        word_count = meta.get("word_count", 0)
        
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#F8FAFC,#FFFFFF);border-radius:16px;padding:1rem 1.25rem;
             border:1px solid #E2E8F0;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
                <span style="font-size:0.7rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;">Selected Paper</span>
                <span style="background:{badge_bg};color:{badge_color};padding:0.15rem 0.5rem;border-radius:12px;font-size:0.65rem;font-weight:700;">
                    {badge_text}
                </span>
            </div>
            <div style="font-weight:700;color:#0F172A;font-size:0.95rem;line-height:1.4;margin-bottom:0.35rem;">{title}</div>
            <div style="display:flex;gap:0.75rem;font-size:0.75rem;color:#64748B;">
                <span>🏷️ {domain}</span>
                <span>•</span>
                <span>📊 {word_count:,} words</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return p
    
    # Multiple papers - show dropdown with better formatting
    names = [p.get("name", "Untitled") for p in papers]
    selected = st.selectbox("Select a paper", names, label_visibility="collapsed")
    
    for p in papers:
        if p.get("name") == selected:
            return p
    return papers[0] if papers else None


# ============================================================================
# PAPER BANNER
# ============================================================================

def paper_banner(paper, accent=COLORS["primary"]):
    """Clean paper info banner with enhanced design."""
    meta = paper.get("metadata", {})
    title = _sanitize_text(meta.get("title", paper.get("name", "Untitled")))
    authors = _sanitize_text(meta.get("authors", "Unknown Authors"))
    if title in {"N/A", "Untitled"}:
        title = _sanitize_text(paper.get("name", "Untitled"))
    if authors in {"N/A", "Unknown Authors"}:
        authors = "Authors not detected"
    
    # Check if it's a patent
    is_patent = meta.get("is_patent", False)
    badge_color = "#92400E" if is_patent else accent
    badge_text = "Patent" if is_patent else "Research Paper"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['surface']} 0%, #F8FAFC 100%);
        border-radius: 20px;
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.5rem;
        border-left: 5px solid {accent};
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -20px;
            right: -20px;
            width: 120px;
            height: 120px;
            background: radial-gradient(circle, {accent}15 0%, transparent 70%);
            border-radius: 50%;
        "></div>
        <div style="
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: {badge_color}15;
            color: {badge_color};
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        ">
            {badge_text}
        </div>
        <h2 style="font-size:1.35rem;font-weight:700;color:{COLORS['text_primary']};margin:0.5rem 0 0.6rem;line-height:1.4;">
            {title}
        </h2>
        <p style="color:{COLORS['text_secondary']};font-size:0.95rem;margin:0;display:flex;align-items:center;gap:0.5rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
            {authors}
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# SECTION RENDERER - Tabbed with Key Insights
# ============================================================================

def render_sections(paper):
    """Render sections in clean tabbed interface with Key Insights."""
    secs = paper.get("section_analysis") or paper.get("sections", {})
    if not secs:
        st.warning("No sections detected in this paper.")
        return
    
    # Get all detected sections and sort by standard order
    section_order = [
        "Abstract", "Introduction", "Background", "Related Work", "Literature Review",
        "Problem Statement", "Methodology", "Methods", "Proposed Method", 
        "System Design", "Architecture", "Implementation",
        "Experiments", "Results", "Discussion", "Conclusion", 
        "Future Work", "References"
    ]
    
    # Build ordered section list - handle both string and dict formats
    ordered_sections = []
    for name in section_order:
        if name in secs:
            data = secs[name]
            # Handle both string (old format) and dict (new format)
            if isinstance(data, str):
                if data.strip():
                    ordered_sections.append((name, {"content": data}))
            elif isinstance(data, dict) and data.get("content"):
                ordered_sections.append((name, data))
    
    # Add any remaining sections not in standard order
    for name, data in secs.items():
        if name not in section_order:
            if isinstance(data, str):
                if data.strip():
                    ordered_sections.append((name, {"content": data}))
            elif isinstance(data, dict) and data.get("content"):
                ordered_sections.append((name, data))
    
    if not ordered_sections:
        st.warning("No section content found.")
        return

    st.caption(f"{len(ordered_sections)} section(s) automatically identified.")

    # Section-wise full text export
    section_text_blob = []
    for sec_name, sec_data in ordered_sections:
        sec_content = _clean_multiline_for_display(sec_data.get("content", ""))
        section_text_blob.append(f"## {sec_name}\n{sec_content}")
    full_sections_text = "\n\n".join(section_text_blob)
    st.download_button(
        "Download Full Text with Section Content (.txt)",
        data=full_sections_text.encode("utf-8"),
        file_name=f"{paper.get('name', 'paper').rsplit('.', 1)[0]}_sectionwise_full_text.txt",
        mime="text/plain",
        key=f"download_sections_{paper.get('id', 'paper')}",
    )
    
    # Create tabs for each section
    tab_names = [f"{name}" for name, _ in ordered_sections]
    tabs = st.tabs(tab_names)
    
    for tab, (name, data) in zip(tabs, ordered_sections):
        with tab:
            _render_section_content(name, data, paper)


def _render_section_content(section_name: str, section_data: dict, paper: dict):
    """Render a single section with its content and Key Insights."""
    # Get the specific section's content only - NOT the whole paper
    content = _clean_multiline_for_display(section_data.get("content", ""))

    # Get summary points from the section data (section-specific only)
    summary_points = _to_points(section_data.get("summary", ""), max_items=3)
    if not summary_points:
        # If no summary, extract from THIS section's content only
        summary_points = _to_points(content, max_items=2)

    # Limit point length
    summary_points = [
        p if len(p) <= 180 else (p[:177].rstrip() + "...")
        for p in summary_points
    ]

    # Create a paragraph summary from the points
    summary_paragraph = " ".join(summary_points[:2]).strip()
    if len(summary_paragraph) > 420:
        summary_paragraph = summary_paragraph[:417].rstrip() + "..."
    
    # Show section name and summarized content as paragraph at top
    st.markdown(f"### {section_name}")
    
    # Show summarized content as paragraph at top
    if summary_paragraph:
        st.markdown(f"<p style='font-size:1rem;line-height:1.7;color:#1E293B;'>{summary_paragraph}</p>", unsafe_allow_html=True)
    else:
        st.info("Summary unavailable for this section.")

    # Show summarized bullet points 
    if summary_points:
        st.markdown("**Important Points:**")
        for p in summary_points:
            st.markdown(f"- {p}")

    # Show section-specific detailed summary (NOT the whole paper)
    with st.expander(f"View More Details", expanded=False):
        # Get the section-specific content for Detailed Summary
        section_specific_content = _clean_multiline_for_display(section_data.get("content", ""))
        
        # For ALL sections, show summarized bullet points (NOT full text)
        # Limit to reasonable length to avoid showing entire section
        detailed_summary = _to_points(section_specific_content, max_items=4)
        
        if detailed_summary:
            st.markdown("**Detailed Summary:**")
            for p in detailed_summary:
                # Limit each point length
                p_limited = p if len(p) <= 200 else (p[:197] + "...")
                st.markdown(f"- {p_limited}")
        else:
            st.info("No detailed summary available for this section.")

    # Key Insights for this section
    _render_section_insights(section_name, section_data, paper)


def _render_section_insights(section_name: str, section_data: dict, paper: dict):
    """Render Key Insights, Highlights, Key Points, Key Themes for a section."""
    content = _clean_multiline_for_display(section_data.get("content", ""))
    highlights = _to_points(section_data.get("highlights", ""), max_items=4)
    key_points = _to_points(section_data.get("key_points", ""), max_items=5)
    takeaways = _to_points(section_data.get("takeaways", ""), max_items=4)
    highlights = [h if len(h) <= 180 else (h[:177].rstrip() + "...") for h in highlights]
    key_points = [k if len(k) <= 180 else (k[:177].rstrip() + "...") for k in key_points]
    takeaways = [t if len(t) <= 180 else (t[:177].rstrip() + "...") for t in takeaways]
    themes = _clean_for_display(section_data.get("themes", ""))

    # Always show meaningful insight blocks per section.
    if not highlights:
        highlights = _to_points(content, max_items=3)
    if not key_points:
        key_points = _to_points(content, max_items=4)
    if not takeaways:
        takeaways = _to_points(content[-1800:], max_items=3)
    if not themes:
        words = re.findall(r"\b[a-zA-Z]{5,}\b", content.lower())
        common = [w for w, _ in Counter(words).most_common(5)]
        themes = ", ".join(common)
    
    # Only show if there's content
    has_insights = any([highlights, key_points, takeaways, themes])
    
    if has_insights:
        with st.expander(f"Key Insights for {section_name}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if highlights:
                    st.markdown("**Highlights**")
                    for item in highlights:
                        st.markdown(f"- {item}")
                
                if key_points:
                    st.markdown("**Key Points**")
                    for item in key_points:
                        st.markdown(f"- {item}")
            
            with col2:
                if takeaways:
                    st.markdown("**Takeaways**")
                    for item in takeaways:
                        st.markdown(f"- {item}")
                
                if themes:
                    st.markdown("**Key Themes**")
                    st.write(themes)


# ============================================================================
# OVERALL SUMMARY CARD
# ============================================================================

def _get_section_content(secs, section_name):
    """Helper to get section content - handles both string and dict formats."""
    # Handle edge cases where secs might not be a dict
    if not secs or not isinstance(secs, dict):
        return ""
    
    if section_name not in secs:
        return ""
    
    data = secs[section_name]
    # Handle both string (old format) and dict (new format)
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        return data.get("content", "")
    return ""


def overall_summary_card(paper):
    """Paper-level summary with sanitized text output only."""
    secs = paper.get("sections", {})
    text = paper.get("text", "")
    st.markdown("### Paper Summary")
    
    ai_summary = _clean_for_display(paper.get("ai_summary", ""))
    if ai_summary:
        st.write(ai_summary)

    # Show abstract if available - handle both string and dict formats
    abstract = _get_section_content(secs, "Abstract")
    if abstract:
        abstract = _clean_for_display(abstract)
        if abstract:
            st.markdown("**Abstract Snapshot**")
            st.write(f"{abstract[:1500]}{'...' if len(abstract) > 1500 else ''}")
    else:
        # Show first 1000 chars of content
        preview = _clean_for_display(text[:1000])
        st.markdown("**Document Snapshot**")
        st.write(preview)

    section_analysis = paper.get("section_analysis", {})
    if section_analysis:
        st.markdown("**Section-wise Summary Overview**")
        shown = 0
        for sec_name, sec_data in section_analysis.items():
            if shown >= 6:
                break
            points = _to_points(sec_data.get("summary", ""), max_items=2)
            if not points:
                continue
            st.markdown(f"**{sec_name}**")
            for p in points:
                st.markdown(f"- {p}")
            shown += 1


# ============================================================================
# PAPER METRICS
# ============================================================================

def paper_metrics(paper):
    """Clean metrics display."""
    meta = paper.get("metadata", {})
    kws = paper.get("keywords", [])
    mods = paper.get("models_methods", []) or paper.get("models", [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        wc = len(paper.get("text", "").split())
        st.metric("Word Count", f"{wc:,}")
    
    with col2:
        st.metric("Keywords", len(kws))
    
    with col3:
        st.metric("Sections", len(paper.get("sections", {})))
    
    with col4:
        st.metric("Methods/Models", len(mods))


# ============================================================================
# KEYWORD CHART
# ============================================================================

def keyword_chart(paper, key_suffix: str = ""):
    """Clean keyword visualization."""
    kws = paper.get("keywords", [])
    if not kws:
        return
    
    words = [k.get("word", "") for k in kws[:15] if k.get("word")]
    scores = [k.get("score", 1) for k in kws[:15] if k.get("word")]
    
    if not words:
        return
    
    fig = px.bar(
        x=scores, y=words, 
        orientation='h',
        labels={'x': 'Relevance Score', 'y': 'Keyword'},
        title="Top Keywords"
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Inter",
        yaxis=dict(autorange='reversed', gridcolor='#F1F5F9'),
        xaxis=dict(gridcolor='#F1F5F9'),
        height=350,
        margin=dict(l=150, r=20, t=40, b=30),
    )
    fig.update_traces(marker_color=COLORS['primary'])
    paper_id = paper.get("id", paper.get("name", "paper"))
    if not key_suffix:
        counter = st.session_state.get("_keyword_chart_counter", 0) + 1
        st.session_state["_keyword_chart_counter"] = counter
        key_suffix = f"auto_{counter}"
    st.plotly_chart(fig, use_container_width=True, key=f"keyword_chart_{paper_id}_{key_suffix}")


# ============================================================================
# SECTION PIE CHART
# ============================================================================

def section_pie(paper, key_suffix: str = ""):
    """Section distribution pie chart."""
    secs = paper.get("sections", {})
    if not secs:
        return
    
    names = []
    sizes = []
    for name, data in secs.items():
        # Handle both string (old format) and dict (new format)
        if isinstance(data, str):
            content = data
        elif isinstance(data, dict):
            content = data.get("content", "")
        else:
            content = ""
        
        if content:
            names.append(name)
            sizes.append(len(content))
    
    if not names:
        return
    
    colors = [sec_color(n) for n in names]
    
    fig = px.pie(
        values=sizes, names=names,
        title="Section Distribution",
        color_discrete_sequence=colors,
    )
    fig.update_layout(
        paper_bgcolor='white',
        font_family="Inter",
        height=350,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    paper_id = paper.get("id", paper.get("name", "paper"))
    if not key_suffix:
        counter = st.session_state.get("_section_pie_counter", 0) + 1
        st.session_state["_section_pie_counter"] = counter
        key_suffix = f"auto_{counter}"
    st.plotly_chart(fig, use_container_width=True, key=f"section_pie_{paper_id}_{key_suffix}")


# ============================================================================
# LIMITATIONS & ADVANTAGES
# ============================================================================

def limitations_advantages_card(paper):
    """Clean limitations and advantages display."""
    lims = paper.get("limitations", [])
    advs = paper.get("advantages", [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: {COLORS['surface']};
            border-radius: {RADIUS['lg']};
            padding: 1.25rem;
            border: 1px solid {COLORS['border']};
            height: 100%;
        ">
            <h5 style="color:{COLORS['danger']};font-size:1rem;font-weight:600;margin:0 0 1rem;">
                Limitations
            </h5>
        </div>
        """, unsafe_allow_html=True)
        
        if lims:
            for lim in lims[:5]:
                st.markdown(f"""
                <div style="background:#FEF2F2;padding:0.75rem 1rem;border-radius:{RADIUS['md']};margin-bottom:0.5rem;border-left:3px solid {COLORS['danger']};">
                    <p style="color:{COLORS['text_primary']};font-size:0.9rem;margin:0;line-height:1.5;">
                        {_clean_for_display(lim)}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No limitations detected.")
    
    with col2:
        st.markdown(f"""
        <div style="
            background: {COLORS['surface']};
            border-radius: {RADIUS['lg']};
            padding: 1.25rem;
            border: 1px solid {COLORS['border']};
            height: 100%;
        ">
            <h5 style="color:{COLORS['success']};font-size:1rem;font-weight:600;margin:0 0 1rem;">
                Advantages
            </h5>
        </div>
        """, unsafe_allow_html=True)
        
        if advs:
            for adv in advs[:5]:
                st.markdown(f"""
                <div style="background:#ECFDF5;padding:0.75rem 1rem;border-radius:{RADIUS['md']};margin-bottom:0.5rem;border-left:3px solid {COLORS['success']};">
                    <p style="color:{COLORS['text_primary']};font-size:0.9rem;margin:0;line-height:1.5;">
                        {_clean_for_display(adv)}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No advantages detected.")


# ============================================================================
# ADDITIONAL CARDS
# ============================================================================

def plagiarism_card(paper):
    """Plagiarism estimation card."""
    plag = paper.get("plagiarism", {})
    score = plag.get("estimated_pct", plag.get("score", 0))
    
    color = COLORS['success'] if score < 20 else COLORS['warning'] if score < 50 else COLORS['danger']
    
    st.markdown(f"""
    <div style="
        background: {COLORS['surface']};
        border-radius: {RADIUS['lg']};
        padding: 1.25rem;
        border: 1px solid {COLORS['border']};
    ">
        <h5 style="color:{COLORS['text_primary']};font-size:1rem;font-weight:600;margin:0 0 1rem;">
            Plagiarism Estimation
        </h5>
        <div style="display:flex;align-items:center;gap:1rem;">
            <div style="
                width:80px;height:80px;border-radius:50%;
                background:conic-gradient({color} {score*3.6}deg, #E5E7EB 0deg);
                display:flex;align-items:center;justify-content:center;
            ">
                <div style="
                    width:60px;height:60px;border-radius:50%;background:{COLORS['surface']};
                    display:flex;align-items:center;justify-content:center;
                ">
                    <span style="font-size:1.1rem;font-weight:700;color:{color};">{score}%</span>
                </div>
            </div>
            <div>
                <p style="color:{COLORS['text_secondary']};font-size:0.9rem;margin:0;">
                    {plag.get("level", plag.get("verdict", "Analyzing..."))}
                </p>
                <p style="color:{COLORS['text_tertiary']};font-size:0.8rem;margin:0.3rem 0 0;">
                    {plag.get("note", "")}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def sentiment_card(paper):
    """Sentiment analysis card."""
    sent = paper.get("sentiment", {})
    overall = sent.get("_overall", sent)
    label = overall.get("label", "Neutral")
    score = overall.get("score", 0.5)
    
    color = COLORS['success'] if label == "Positive" else COLORS['danger'] if label == "Negative" else COLORS['warning']
    
    st.markdown(f"""
    <div style="
        background: {COLORS['surface']};
        border-radius: {RADIUS['lg']};
        padding: 1.25rem;
        border: 1px solid {COLORS['border']};
    ">
        <h5 style="color:{COLORS['text_primary']};font-size:1rem;font-weight:600;margin:0 0 1rem;">
            Sentiment Analysis
        </h5>
        <div style="
            display:inline-block;padding:0.5rem 1rem;
            background:{color}15;color:{color};
            border-radius:{RADIUS['full']};font-weight:600;
        ">
            {label} ({score:.2f})
        </div>
    </div>
    """, unsafe_allow_html=True)


def research_gaps_card(paper):
    """Research gaps card."""
    gaps = paper.get("research_gaps", [])
    st.markdown("#### Research Gaps")

    if gaps:
        for gap in gaps[:4]:
            st.markdown(f"- {_clean_for_display(gap)}")
    else:
        st.info("No clear research gaps identified.")


def trends_card(paper):
    """Trends card."""
    trends = paper.get("trends", [])
    st.markdown("#### Identified Trends")

    if trends:
        cols = st.columns(2)
        for i, t in enumerate(trends[:6]):
            with cols[i % 2]:
                st.markdown(f"- {_clean_for_display(t.get('trend', 'N/A'))}")
    else:
        st.info("No trends identified.")


def patent_info_card(paper):
    """Patent info card - placeholder."""
    st.info("Patent detection feature coming soon.")


# ============================================================================
# NEW FEATURE CARDS
# ============================================================================

def paper_quality_card(paper):
    """Paper quality score card."""
    quality = paper.get("quality_score", {})
    if not quality:
        st.warning("Quality analysis not available.")
        return

    score = quality.get("overall_score", quality.get("score", 0))
    tier = quality.get("tier", "N/A")
    st.markdown("#### Paper Quality Score")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Score", f"{score}/100")
    with c2:
        st.metric("Tier", tier)

    # Strengths & Weaknesses
    strengths = quality.get("strengths", [])
    weaknesses = quality.get("weaknesses", [])
    
    if strengths:
        st.markdown("**Strengths:**")
        for s in strengths[:3]:
            st.markdown(f"- {_clean_for_display(s)}")
    
    if weaknesses:
        st.markdown("**Areas for Improvement:**")
        for w in weaknesses[:3]:
            st.markdown(f"- {_clean_for_display(w)}")


def journal_recommendations_card(paper):
    """Journal recommendations card."""
    recs = paper.get("journal_recommendations", {})
    if not recs:
        st.warning("Journal recommendations not available.")
        return
    
    venues = recs.get("venues", [])
    if not venues:
        combined = recs.get("all_recommendations", [])
        journals = set(recs.get("recommended_journals", []))
        venues = [
            {
                "name": v,
                "tier": recs.get("quality_tier", "Medium"),
                "type": "Journal" if v in journals else "Conference",
            }
            for v in combined
        ]
    
    st.markdown("#### Journal & Conference Recommendations")

    if venues:
        for v in venues[:6]:
            tier = v.get("tier", "Medium")
            name = _clean_for_display(v.get("name", "N/A"))
            vtype = _clean_for_display(v.get("type", ""))
            st.markdown(f"- **{name}** ({vtype} | {tier} Tier)")
    else:
        st.info("No recommendations available.")


def citation_impact_card(paper):
    """Citation impact card."""
    impact = paper.get("citation_impact", {})
    if not impact:
        st.warning("Citation impact analysis not available.")
        return
    
    st.markdown(f"""
    <div style="
        background: {COLORS['surface']};
        border-radius: {RADIUS['lg']};
        padding: 1.5rem;
        border: 1px solid {COLORS['border']};
    ">
        <h4 style="color:{COLORS['text_primary']};font-size:1.1rem;font-weight:700;margin:0 0 1rem;">
            Citation Impact Analysis
        </h4>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;">
            <div style="text-align:center;padding:1rem;background:{COLORS['background']};border-radius:{RADIUS['md']};">
                <p style="font-size:1.5rem;font-weight:700;color:{COLORS['primary']};margin:0;">
                    {impact.get('reference_count', 0)}
                </p>
                <p style="font-size:0.8rem;color:{COLORS['text_tertiary']};margin:0;">References</p>
            </div>
            <div style="text-align:center;padding:1rem;background:{COLORS['background']};border-radius:{RADIUS['md']};">
                <p style="font-size:1.5rem;font-weight:700;color:{COLORS['success']};margin:0;">
                    {impact.get('impact_score', 0)}
                </p>
                <p style="font-size:0.8rem;color:{COLORS['text_tertiary']};margin:0;">Impact Score</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def future_directions_card(paper):
    """Future directions card."""
    future = paper.get("future_directions", {})
    if not future:
        st.warning("Future directions not available.")
        return
    
    directions = future.get("directions", [])
    
    st.markdown("#### Future Research Directions")

    if directions:
        for d in directions[:5]:
            priority = d.get("priority", "Medium")
            direction = _clean_for_display(d.get("suggestion", d.get("direction", "")))
            st.markdown(f"- {direction} ({priority} priority)")
    else:
        st.info("No future directions suggested.")


def project_ideas_card(paper):
    """Project ideas card."""
    projects = paper.get("project_ideas", {})
    if not projects:
        st.warning("Project ideas not available.")
        return
    
    ideas = projects.get("project_ideas", [])
    
    st.markdown("#### Project Ideas")

    if ideas:
        for p in ideas[:4]:
            title = _clean_for_display(p.get("title", "N/A"))
            desc = _clean_for_display(p.get("description", ""))
            difficulty = _clean_for_display(p.get("difficulty", "N/A"))
            timeline = _clean_for_display(p.get("timeline", "N/A"))
            with st.expander(title, expanded=False):
                st.write(desc)
                st.caption(f"Difficulty: {difficulty} | Timeline: {timeline}")
    else:
        st.info("No project ideas generated.")


def semantic_search_widget():
    """Semantic search widget."""
    st.markdown(f"""
    <div style="
        background: {COLORS['surface']};
        border-radius: {RADIUS['lg']};
        padding: 1.5rem;
        border: 1px solid {COLORS['border']};
        margin-bottom: 1.5rem;
    ">
        <h4 style="color:{COLORS['text_primary']};font-size:1.1rem;font-weight:700;margin:0 0 1rem;">
            Semantic Search
        </h4>
        <input type="text" placeholder="Search across all papers..." style="
            width:100%;padding:0.75rem 1rem;border:1px solid {COLORS['border']};
            border-radius:{RADIUS['md']};font-size:1rem;
        ">
    </div>
    """, unsafe_allow_html=True)
    
    query = st.text_input("Search query", label_visibility="collapsed")
    if query and st.button("Search"):
        papers = st.session_state.get("papers", [])
        results = semantic_search(papers, query)
        st.write(f"Found {len(results)} results")
        for r in results:
            st.markdown(f"**{_clean_for_display(r.get('title', 'Untitled'))}**")
            st.caption(f"Score: {r.get('score', 0)} | Domain: {r.get('domain', 'Unknown')}")
            reasons = r.get("reasons", [])
            if reasons:
                st.write(", ".join(reasons))


def topic_trends_analysis_card(papers):
    """Topic trends analysis across papers."""
    if not papers:
        st.info("Upload papers to see trends.")
        return
    
    all_trends = analyze_topic_trends(papers)
    
    st.markdown("#### Topic Trends Analysis")

    if all_trends:
        st.write(all_trends.get("summary", "No trends data."))
    else:
        st.info("Not enough data for trends analysis.")


def similarity_analysis_card(paper1, paper2):
    """Similarity analysis between two papers."""
    similarity = calculate_similarity(paper1, paper2)
    
    score = similarity.get("similarity_score", 0)
    level = similarity.get("level", "N/A")
    color = similarity.get("color", COLORS['text_tertiary'])
    
    st.markdown(f"""
    <div style="
        background: {COLORS['surface']};
        border-radius: {RADIUS['lg']};
        padding: 1.5rem;
        border: 1px solid {COLORS['border']};
    ">
        <h4 style="color:{COLORS['text_primary']};font-size:1.1rem;font-weight:700;margin:0 0 1rem;">
            Semantic Similarity
        </h4>
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <span style="font-size:2rem;font-weight:800;color:{color};">{score}%</span>
            <span style="
                padding:0.4rem 1rem;background:{color}15;color:{color};
                border-radius:{RADIUS['full']};font-weight:600;
            ">
                {level}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# CHATBOT & COMPARISON
# ============================================================================

def _get_direct_answer(question: str, paper: dict) -> str:
    """
    Get a direct answer for a question about a paper.
    Wraps the answer_question function from ollama_engine with error handling.
    """
    if not question or not paper:
        return "Unable to process your question. Please try again."
    
    try:
        # Use the answer_question function from ollama_engine
        answer = answer_question(question, paper)
        
        # Check if answer is valid
        if not answer or len(answer.strip()) < 5:
            return "I couldn't find enough information to answer your question. Please try a different question."
        
        return answer
    except Exception as e:
        # Fallback for any errors - try extractive approach
        try:
            sections = paper.get("sections", {}) or {}
            if not sections:
                return "No sections found in this paper for analysis."
            
            # Simple fallback - extract relevant content
            keywords = question.lower().split()
            best_content = ""
            best_score = 0
            
            for sec_name, sec_data in sections.items():
                content = _section_text(sec_data)
                if not content:
                    continue
                
                # Score by keyword overlap
                content_lower = content.lower()
                score = sum(1 for kw in keywords if kw in content_lower)
                
                if score > best_score:
                    best_score = score
                    best_content = content[:500]
            
            if best_content:
                return f"Based on the paper content: {best_content[:300]}..."
            return "I couldn't find a good answer from the paper content."
        except:
            return "An error occurred while processing your question. Please try again."


def chatbot(paper):
    """Research chatbot interface with improved UI and direct display."""
    # Initialize chat history for this paper
    paper_key = paper.get("id", paper.get("name", "paper"))
    if f"chat_history_{paper_key}" not in st.session_state:
        st.session_state[f"chat_history_{paper_key}"] = []
    
    # Get this paper's chat history
    chat_history = st.session_state[f"chat_history_{paper_key}"]
    
    # Enhanced header with mode indicator
    ollama_live = is_ollama_running()
    
    # Set colors based on mode
    mode_bg = "#ECFDF5" if ollama_live else "#FEF3C7"
    mode_color = "#059669" if ollama_live else "#D97706"
    mode_text = "🟢 Ollama Online" if ollama_live else "🟡 Offline Mode"
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#F8FAFC,#FFFFFF);border-radius:16px;padding:1.25rem 1.5rem;
         border:1px solid #E2E8F0;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <h3 style="margin:0 0 0.25rem 0;font-size:1.25rem;font-weight:700;color:#0F172A;">🤖 Research Assistant</h3>
                <p style="margin:0;font-size:0.8rem;color:#64748B;">Ask questions about this paper</p>
            </div>
            <div style="text-align:right;">
                <span style="background:{mode_bg};color:{mode_color};padding:0.35rem 0.75rem;border-radius:20px;font-size:0.7rem;font-weight:700;">
                    {mode_text}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick question chips
    st.markdown("**💡 Quick Questions:**")
    examples = [
        ("📊", "What is the accuracy?"),
        ("📈", "What are the main results?"),
        ("🔧", "What methodology is used?"),
        ("❓", "What problem does it solve?"),
        ("📁", "What dataset is used?"),
        ("🎯", "What are the limitations?"),
    ]
    
    example_cols = st.columns(3)
    selected_example = None
    for idx, (icon, question) in enumerate(examples):
        with example_cols[idx % 3]:
            if st.button(f"{icon} {question}", key=f"chat_example_{paper_key}_{idx}", use_container_width=True):
                selected_example = question

    st.markdown("---")
    
    # Chat input area
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input(
            "Ask a question about this paper...",
            key=f"chat_input_{paper_key}",
            label_visibility="collapsed",
            placeholder="Type your question here...",
        )
    with col2:
        ask_btn = st.button("Ask 💬", key=f"chat_ask_{paper_key}", use_container_width=True)
    
    # Process the question
    if selected_example:
        with st.spinner("Analyzing..."):
            answer = _get_direct_answer(selected_example, paper)
            chat_history.append({"question": selected_example, "answer": answer})

    if ask_btn and question.strip():
        with st.spinner("Analyzing..."):
            answer = _get_direct_answer(question.strip(), paper)
            chat_history.append({"question": question.strip(), "answer": answer})
    
    # Display chat history in a beautiful format
    st.markdown("### 💬 Conversation")
    
    if not chat_history:
        st.markdown(f"""
        <div style="text-align:center;padding:2rem;color:#94A3B8;">
            <div style="font-size:3rem;margin-bottom:1rem;">💬</div>
            <div style="font-size:1rem;font-weight:500;">No messages yet</div>
            <div style="font-size:0.85rem;">Ask a question or select a quick question above!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show only last 10 messages
        for i, msg in enumerate(chat_history[-10:]):
            # User message
            st.markdown(f"""
            <div style="background:#EFF6FF;border-radius:16px;padding:1rem 1.25rem;margin-bottom:0.75rem;border-left:4px solid #3B82F6;">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;">
                    <span style="background:#3B82F6;color:white;padding:0.15rem 0.5rem;border-radius:12px;font-size:0.65rem;font-weight:700;">YOU</span>
                    <span style="color:#64748B;font-size:0.75rem;">{msg['question']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Bot response
            st.markdown(f"""
            <div style="background:#F8FAFC;border-radius:16px;padding:1rem 1.25rem;margin-bottom:1rem;border-left:4px solid #10B981;">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;">
                    <span style="background:#10B981;color:white;padding:0.15rem 0.5rem;border-radius:12px;font-size:0.65rem;font-weight:700;">BOT</span>
                    <span style="color:#64748B;font-size:0.75rem;">AI Assistant</span>
                </div>
                <div style="color:#0F172A;font-size:0.95rem;line-height:1.6;">{msg['answer']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", key=f"clear_chat_{paper_key}"):
            chat_history.clear()
            st.rerun()


def comparison_widget(papers=None):
    """Compare papers widget."""
    papers = papers or st.session_state.get("papers", [])
    if not papers:
        st.info("Upload at least one paper to start comparisons.")
        return

    # Persist uploaded comparison paper across page/tab switches.
    if "compare_uploaded_paper" not in st.session_state:
        st.session_state["compare_uploaded_paper"] = None
    if "compare_uploaded_name" not in st.session_state:
        st.session_state["compare_uploaded_name"] = ""

    current = st.session_state.get("current_paper")
    current_idx = 0
    if current:
        for idx, p in enumerate(papers):
            if p.get("id") == current.get("id") or p.get("fingerprint") == current.get("fingerprint"):
                current_idx = idx
                break

    (tab_upload,) = st.tabs(["Current vs Uploaded"])
    with tab_upload:
        base_paper = st.selectbox(
            "Current paper",
            papers,
            index=current_idx,
            format_func=lambda x: x.get("name", ""),
            key="compare_upload_base",
        )
        uploaded_other = st.file_uploader(
            "Upload another paper to compare",
            type=["pdf", "docx", "doc", "txt"],
            key="compare_upload_file",
        )

        uploaded_paper = st.session_state.get("compare_uploaded_paper")
        if uploaded_other:
            with st.spinner("Analyzing uploaded comparison paper..."):
                # Save to library so this paper is available to all pages/features.
                uploaded_paper = _analyze_uploaded_file(uploaded_other, save_to_library=True)
            st.session_state["compare_uploaded_paper"] = uploaded_paper
            st.session_state["compare_uploaded_name"] = uploaded_paper.get("name", uploaded_other.name)
            st.success(f"Ready to compare with: {uploaded_paper.get('name', 'Uploaded paper')}")
        elif uploaded_paper:
            st.info(
                f"Using saved comparison paper: {st.session_state.get('compare_uploaded_name', uploaded_paper.get('name', 'Uploaded paper'))}"
            )

        if uploaded_paper:
            c1, c2 = st.columns(2)
            with c1:
                mb = base_paper.get("metadata", {})
                st.caption(f"Current title: {_clean_for_display(mb.get('title', base_paper.get('name', 'N/A')))}")
                st.caption(f"Current authors: {_clean_for_display(mb.get('authors', 'Authors not detected'))}")
            with c2:
                mu = uploaded_paper.get("metadata", {})
                st.caption(f"Uploaded title: {_clean_for_display(mu.get('title', uploaded_paper.get('name', 'N/A')))}")
                st.caption(f"Uploaded authors: {_clean_for_display(mu.get('authors', 'Authors not detected'))}")

            c3, c4 = st.columns(2)
            with c3:
                if st.button("Compare Current vs Uploaded", key="compare_uploaded_btn"):
                    with st.spinner("Comparing papers..."):
                        result = compare_papers(base_paper, uploaded_paper)
                    similarity_analysis_card(base_paper, uploaded_paper)
                    st.markdown("### Detailed Comparison")
                    st.markdown(result)
            with c4:
                if st.button("Clear Uploaded Paper", key="compare_uploaded_clear_btn"):
                    st.session_state["compare_uploaded_paper"] = None
                    st.session_state["compare_uploaded_name"] = ""
                    st.rerun()

            st.caption("This uploaded comparison paper is saved to My Papers.")


def side_by_side_comparison_view(paper1, paper2):
    """
    Display two papers side-by-side in a clean two-column layout.
    Each column shows the complete extracted content of a paper as natural text blocks
    with section headings, without tables, grids, or bordered containers.
    """
    if not paper1 or not paper2:
        st.warning("Both papers must be selected for comparison.")
        return
    
    # Define the standard section order for consistent display
    section_order = [
        "Abstract", "Introduction", "Background", "Related Work", "Literature Review",
        "Problem Statement", "Objectives", "Methodology", "Methods", "Proposed Method",
        "System Design", "Architecture", "Implementation",
        "Experiments", "Experimental Setup", "Results", "Results & Discussion", "Discussion",
        "Conclusion", "Future Work", "Limitations", "Advantages",
        "References", "Appendix"
    ]
    
    def get_ordered_sections(paper_sections):
        """Return sections in consistent order."""
        ordered = []
        # First add sections in standard order that exist
        for name in section_order:
            if name in paper_sections:
                ordered.append((name, paper_sections[name]))
        # Then add any remaining sections not in standard order
        for name, data in paper_sections.items():
            if name not in section_order:
                ordered.append((name, data))
        return ordered
    
    def render_paper_column(paper, column_label):
        """Render a single paper's content in a column."""
        meta = paper.get("metadata", {})
        secs = paper.get("sections", {})
        
        # Paper header
        st.markdown(f"### {column_label}")
        st.markdown("---")
        
        # Metadata Section
        st.markdown("#### Title")
        title = _clean_for_display(meta.get("title", paper.get("name", "Untitled")))
        st.markdown(f"{title}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Domain and Type
        st.markdown("#### Domain")
        domain = _clean_for_display(meta.get("domain", "N/A"))
        st.markdown(f"{domain}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("#### Type")
        ptype = _clean_for_display(meta.get("research_type", "Research Paper"))
        is_patent = meta.get("is_patent", False)
        if is_patent:
            ptype = "Patent"
        st.markdown(f"{ptype}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("#### Year")
        year = _clean_for_display(str(meta.get("year", "N/A")))
        st.markdown(f"{year}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Authors
        st.markdown("#### Authors")
        authors = _clean_for_display(meta.get("authors", "Authors not detected"))
        st.markdown(f"{authors}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Word Count
        st.markdown("#### Word Count")
        wc = meta.get("word_count", 0)
        st.markdown(f"{wc:,}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Reference Count
        st.markdown("#### References")
        ref_count = meta.get("reference_count", 0)
        st.markdown(f"{ref_count}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Keywords
        st.markdown("#### Keywords")
        kws = paper.get("keywords", [])
        if kws:
            kw_list = ", ".join([k.get("word", "") for k in kws[:15] if k.get("word")])
            st.markdown(f"{kw_list}")
        else:
            st.markdown("No keywords extracted")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Models/Methods/Tools
        st.markdown("#### Models/Methods/Tools Used")
        models = paper.get("models_methods", []) or paper.get("models", [])
        if models:
            models_list = ", ".join(models[:20])
            st.markdown(f"{models_list}")
        else:
            st.markdown("No models/methods detected")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Limitations
        st.markdown("#### Limitations")
        lims = paper.get("limitations", [])
        if lims:
            for lim in lims[:5]:
                st.markdown(f"- {_clean_for_display(lim)}")
        else:
            st.markdown("No limitations detected")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Advantages
        st.markdown("#### Advantages")
        advs = paper.get("advantages", [])
        if advs:
            for adv in advs[:5]:
                st.markdown(f"- {_clean_for_display(adv)}")
        else:
            st.markdown("No advantages detected")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # All Sections - Render in natural reading format
        ordered_sections = get_ordered_sections(secs)
        
        for sec_name, sec_data in ordered_sections:
            # Skip references and appendix in main content view to save space
            if sec_name.lower() in ["references", "appendix"]:
                continue
                
            # Get content - handle both string and dict formats
            if isinstance(sec_data, str):
                content = _clean_multiline_for_display(sec_data)
            elif isinstance(sec_data, dict):
                content = _clean_multiline_for_display(sec_data.get("content", ""))
            else:
                content = ""
            
            if not content:
                continue
            
            st.markdown(f"#### {sec_name}")
            st.markdown(f"{content}")
            st.markdown("<br>", unsafe_allow_html=True)
    
    # Create two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        render_paper_column(paper1, "Paper 1")
    
    with col2:
        render_paper_column(paper2, "Paper 2")
