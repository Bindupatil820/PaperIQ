"""
Enhanced text extraction + smart section detection + new analysis features.
Handles: PDF, DOCX, TXT.
New features:
  - Accurate title & author extraction
  - Limitations & Advantages extraction
  - Patent / Non-patent detection
  - Plagiarism estimation
  - Sentiment analysis (rule-based)
  - Research gap detection
  - Trend identification
"""
import re
import html
import difflib
from collections import Counter

#  Extraction 
def extract_text(file_obj, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    try:
        if ext == "pdf":
            return _pdf(file_obj)
        elif ext in ("docx", "doc"):
            return _docx(file_obj)
        else:
            raw = file_obj.read()
            return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[Error extracting text: {e}]"

def _pdf(f) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)

def _docx(f) -> str:
    import docx
    doc = docx.Document(f)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def _fix_mojibake(text: str) -> str:
    replacements = {
        "Ã‚Â·": " | ",
        "Ã¢â‚¬Â¢": "- ",
        "Ã¢â‚¬â€œ": "-",
        "Ã¢â‚¬â€": "-",
        "Ã¢â‚¬Ëœ": "'",
        "Ã¢â‚¬â„¢": "'",
        "Ã¢â‚¬Å“": '"',
        "Ã¢â‚¬\x9d": '"',
        "Ã¢â‚¬Â¦": "...",
        "Ãƒâ€”": "x",
        "ÃƒÂ©": "e",
        "ÃƒÂ¨": "e",
        "ÃƒÂ¶": "o",
        "ÃƒÂ¼": "u",
        "ÃƒÂ±": "n",
        "\ufeff": "",
        "\u00a0": " ",
    }
    out = text
    for bad, good in replacements.items():
        out = out.replace(bad, good)
    return out


def _fix_run_together_words(text: str) -> str:
    """
    Fix words that are run together without spaces.
    E.g., 'ofthe' -> 'of the', 'theand' -> 'the and'
    """
    if not text:
        return text
    
    # Common patterns where words are concatenated without spaces
    fix_patterns = [
        (r'\btheand\b', 'the and'),
        (r'\bandof\b', 'and of'),
        (r'\bofthe\b', 'of the'),
        (r'\btobe\b', 'to be'),
        (r'\bfromthe\b', 'from the'),
        (r'\bwiththe\b', 'with the'),
        (r'\bforth\b', 'for the'),
        (r'\binthe\b', 'in the'),
        (r'\bforthis\b', 'for this'),
        (r'\bthatis\b', 'that is'),
        (r'\bthisis\b', 'this is'),
        (r'\bitis\b', 'it is'),
        (r'\bwehave\b', 'we have'),
        (r'\bweuse\b', 'we use'),
        (r'\bwealso\b', 'we also'),
        (r'\bourmethod\b', 'our method'),
        (r'\bourapproach\b', 'our approach'),
        (r'\bourresults\b', 'our results'),
        (r'\bourstudy\b', 'our study'),
        (r'\bourpaper\b', 'our paper'),
        (r'\bthispaper\b', 'this paper'),
        (r'\bthisstudy\b', 'this study'),
        (r'\bmethodsand\b', 'methods and'),
        (r'\bresultsand\b', 'results and'),
        (r'\bdataand\b', 'data and'),
        (r'\bmodeland\b', 'model and'),
        (r'\bsystemand\b', 'system and'),
        (r'\bapproachand\b', 'approach and'),
    ]
    
    result = text
    for pattern, replacement in fix_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # General pattern: insert space between lowercase-uppercase
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    result = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', result)
    result = re.sub(r'([.,;:!?])\s*([A-Z])', r'\1 \2', result)
    result = re.sub(r'\.\s+', '. ', result)
    result = re.sub(r',([A-Za-z])', r', \1', result)
    result = re.sub(r' +', ' ', result)
    
    return result


def _strip_html_noise(text: str) -> str:
    # Remove script/style blocks and tags from HTML-like extracted content.
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    # Preserve href targets (useful for DOI links) before dropping tags.
    text = re.sub(r'(?is)<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r" \1 \2 ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    # Remove inline CSS artifacts that leak from badly extracted HTML.
    text = re.sub(r"(?i)\b(style|class|href|target)\s*=\s*(\".*?\"|'.*?'|\S+)", " ", text)
    return text


def _sanitize_metadata_text(value: str, max_len: int = 220) -> str:
    v = _fix_mojibake(_strip_html_noise(value or ""))
    v = re.sub(r"\s+", " ", v).strip(" -|,;:")
    if not v:
        return "N/A"
    if len(v) > max_len:
        v = v[: max_len - 3].rstrip() + "..."
    return v


def clean_text(text: str) -> str:
    text = _fix_mojibake(_strip_html_noise(text or ""))
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', text)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()


#  Section Detection 
ALIASES: dict[str, str] = {
    "abstract":               "Abstract",
    "executive summary":      "Abstract",
    "summary":                "Abstract",
    "abstract and keywords":  "Abstract",
    "introduction":           "Introduction",
    "motivation":             "Introduction",
    "overview":               "Introduction",
    "background":             "Background",
    "preliminaries":          "Background",
    "related work":           "Related Work",
    "prior work":             "Related Work",
    "literature review":      "Literature Review",
    "literature survey":      "Literature Review",
    "state of the art":       "Literature Review",
    "related studies":        "Related Work",
    "previous work":          "Related Work",
    "problem statement":      "Problem Statement",
    "problem formulation":    "Problem Statement",
    "problem definition":     "Problem Statement",
    "research questions":     "Problem Statement",
    "research objectives":    "Objectives",
    "objectives":            "Objectives",
    "aims":                  "Objectives",
    "goals":                 "Objectives",
    "methodology":            "Methodology",
    "methods":                "Methodology",
    "materials and methods":  "Methodology",
    "approach":               "Methodology",
    "proposed method":        "Methodology",
    "proposed approach":      "Methodology",
    "proposed framework":     "Methodology",
    "framework":              "Methodology",
    "model":                  "Methodology",
    "system design":          "System Design",
    "system overview":        "System Design",
    "architecture":           "Architecture",
    "design":                 "System Design",
    "implementation":         "Implementation",
    "experiments":            "Experiments & Results",
    "experimental setup":     "Experiments & Results",
    "experimental results":   "Experiments & Results",
    "experiments and results":"Experiments & Results",
    "results":                "Results",
    "results and discussion": "Results & Discussion",
    "discussion":             "Discussion",
    "evaluation":             "Evaluation",
    "performance evaluation": "Evaluation",
    "analysis":               "Analysis",
    "ablation study":         "Analysis",
    "comparison":             "Comparison",
    "comparative study":      "Comparison",
    "conclusion":             "Conclusion",
    "conclusions":            "Conclusion",
    "concluding remarks":     "Conclusion",
    "summary and conclusion": "Conclusion",
    "future work":            "Future Work",
    "future directions":      "Future Work",
    "limitations":            "Limitations",
    "limitations and future": "Limitations",
    "advantages":             "Advantages",
    "acknowledgements":       "Acknowledgements",
    "acknowledgments":        "Acknowledgements",
    "references":             "References",
    "bibliography":           "References",
    "appendix":               "Appendix",
    "claims":                 "Claims",
    "patent claims":          "Claims",
    "field of invention":     "Field of Invention",
    "background of invention":"Background",
    "brief description":      "Brief Description",
    "detailed description":   "Detailed Description",
    # Additional sections often found in papers
    "datasets":               "Datasets",
    "data collection":        "Data Collection",
    "data description":       "Datasets",
    "data":                   "Datasets",
    "data acquisition":       "Data Collection",
    "experimental data":      "Datasets",
    "hardware":               "Hardware & Software",
    "software":               "Hardware & Software",
    "hardware and software":  "Hardware & Software",
    "experimental environment": "Hardware & Software",
    "preprocessing":          "Data Preprocessing",
    "data preprocessing":     "Data Preprocessing",
    "feature extraction":     "Feature Extraction",
    "features":               "Feature Extraction",
    "feature engineering":    "Feature Extraction",
    "training":               "Training",
    "model training":         "Training",
    "learning":               "Training",
    "training process":       "Training",
    "testing":                "Testing",
    "evaluation":             "Testing",
    "model evaluation":       "Testing",
    "validation":             "Testing",
    "threats to validity":    "Threats to Validity",
    "validity":              "Threats to Validity",
    "ethics":                 "Ethics Statement",
    "ethical considerations": "Ethics Statement",
    "ethical issues":         "Ethics Statement",
    "reproducibility":        "Reproducibility",
    "data availability":     "Data Availability",
    "code availability":      "Code Availability",
}

def identify_sections(text: str) -> dict[str, str]:
    """Return ordered mapping {section_name: content} with robust heading detection."""
    lines = text.split('\n')
    result: dict[str, str] = {}
    cur_name = None
    cur_lines: list[str] = []

    def flush():
        nonlocal cur_name, cur_lines
        if cur_name:
            content = '\n'.join(cur_lines).strip()
            if content:
                if cur_name in result:
                    result[cur_name] += '\n\n' + content
                else:
                    result[cur_name] = content
        cur_lines = []

    for raw_line in lines:
        stripped = raw_line.strip()
        heading, inline_content = _split_inline_heading(stripped)
        if not heading:
            heading = _is_heading(stripped)

        if heading:
            flush()
            cur_name = heading
            if inline_content:
                cur_lines.append(inline_content)
            continue

        cur_lines.append(stripped)

    flush()

    # Keep all explicitly detected sections (even short ones) so UI can show everything.
    result = {k: v for k, v in result.items() if len(v.split()) >= 1}

    if not result:
        result = _heuristic(text)
    else:
        # Augment extraction so key sections are still available when heading detection is partial.
        h = _heuristic(text)
        for k, v in h.items():
            if k == "Full Text":
                continue
            if k not in result and len(v.split()) >= 5:
                result[k] = v

    return result


def _section_text(value) -> str:
    """Normalize section payloads (str or dict with content) to plain text."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("content", ""))
    return ""


def _normalize_heading(line: str) -> str:
    """Normalize heading candidate before alias lookup."""
    stripped = re.sub(
        r'^(\d+(\.\d+)*\.?\s*|[IVXivx]+\.?\s*|[A-Z]\.\s*)',
        '',
        line or "",
    ).strip()
    stripped = re.sub(r'\s+', ' ', stripped)
    return stripped.rstrip('.:-–— ').strip().lower()


def _canonical_section(candidate: str) -> str | None:
    """Map raw heading text to canonical section name."""
    c = _normalize_heading(candidate)
    if not c:
        return None

    if c in ALIASES:
        return ALIASES[c]
    if c.endswith("s") and c[:-1] in ALIASES:
        return ALIASES[c[:-1]]

    # Fuzzy recovery for small heading typos only.
    # Keep strict to avoid matching normal sentences as headings.
    words = c.split()
    if len(words) <= 5:
        for alias, canonical in sorted(ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
            if c == alias:
                return canonical
            if c.startswith(alias + " ") and len(words) <= 4:
                return canonical
            ratio = difflib.SequenceMatcher(None, c, alias).ratio()
            if ratio >= 0.9 and abs(len(c) - len(alias)) <= 3:
                return canonical
    return None


def _split_inline_heading(line: str) -> tuple[str | None, str]:
    """
    Detect one-line heading + content patterns, e.g.:
      "Abstract- This paper ..."
      "1 Introduction: ..."
    """
    if not line or len(line) < 6:
        return None, ""

    stripped = re.sub(
        r'^(\d+(\.\d+)*\.?\s*|[IVXivx]+\.?\s*)',
        '',
        line.strip(),
    )
    lower = stripped.lower()

    # Longest aliases first to avoid "results" matching "results and discussion".
    for alias, canonical in sorted(ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if not lower.startswith(alias):
            continue
        rest = stripped[len(alias):].lstrip()
        if not rest:
            return canonical, ""
        if rest[0] in {":", "-", "–", "—", ".", "?", "|"}:
            return canonical, rest[1:].strip()
    return None, ""


def _is_heading(line: str) -> str | None:
    if not line or len(line) > 85:
        return None

    canonical = _canonical_section(line)
    if canonical:
        return canonical

    if line.isupper() and 3 < len(line) < 60 and re.match(r'^[A-Z\s\d\-&/]+$', line):
        lower2 = _normalize_heading(line)
        canonical = _canonical_section(lower2)
        if canonical:
            return canonical
        return line.title()

    m = re.match(r'^(\d+(\.\d+)*\.?\s+)([A-Z][A-Za-z0-9 &/\-]{2,55})$', line)
    if m:
        candidate = m.group(3).strip()
        canonical = _canonical_section(candidate)
        if canonical:
            return canonical
        if len(m.group(3).split()) <= 6:
            return m.group(3).strip()

    return None


def _extract_section_insights(section_name: str, content: str) -> dict:
    """Extract Highlights, Key Points, Takeaways, and Themes from section content."""
    insights = {
        "highlights": "",
        "key_points": "",
        "takeaways": "",
        "themes": ""
    }
    
    if not content or len(content) < 50:
        return insights

    # Cap section size for speed on large papers.
    working = content[:12000]

    # Clean the content
    clean = re.sub(r'\s+', ' ', working)
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    
    # Extract Highlights - key findings/results sentences
    highlight_patterns = [
        r'(?:we (?:find|show|demonstrate|observe|discover|reveal)|results (?:show|indicate|suggest|demonstrate)|our (?:study|experiment|analysis) (?:reveals|shows|indicates|demonstrates)|findings (?:suggest|show|indicate))[^.!?]{10,150}[.!?]',
        r'(?:significantly|substantially|considerably|markedly) (?:improve|outperform|enhance|reduce|decrease|increase)[^.!?]{10,100}[.!?]',
        r'(?:achieve|attain|reach|obtain) (?:state-of-the-art|best|highest|excellent|good|significant)[^.!?]{10,100}[.!?]',
        r'(?:novel|new|proposed) (?:approach|method|framework|model|technique|algorithm|system)[^.!?]{10,100}[.!?]',
    ]
    
    highlights = []
    for pattern in highlight_patterns:
        for m in re.finditer(pattern, clean, re.IGNORECASE):
            sent = m.group(0).strip()
            if 20 < len(sent) < 200 and sent not in highlights:
                highlights.append(sent)
    
    insights["highlights"] = " ".join(highlights[:3])
    
    # Extract Key Points - important methodology/finding statements
    keypoint_patterns = [
        r'(?:we (?:propose|present|introduce|develop|design|implement|use|employ|adopt)|the (?:proposed|our|this) (?:method|approach|model|framework|system|technique))[^.!?]{10,150}[.!?]',
        r'(?:methodology|approach|model|framework|system|technique) (?:based on|utilizing|employing|using|consists of|includes|involves)[^.!?]{10,120}[.!?]',
        r'(?:first|initially|firstly|to begin|we start) [^.!?]{10,80}[.!?]',
        r'(?:additionally|furthermore|moreover|also|besides) [^.!?]{10,100}[.!?]',
    ]
    
    key_points = []
    for pattern in keypoint_patterns:
        for m in re.finditer(pattern, clean, re.IGNORECASE):
            sent = m.group(0).strip()
            if 20 < len(sent) < 180 and sent not in key_points:
                key_points.append(sent)
    
    insights["key_points"] = " ".join(key_points[:3])
    
    # Extract Takeaways - important conclusions/implications
    takeaway_patterns = [
        r'(?:in conclusion|to conclude|finally|overall|in summary|as a result|therefore|thus|hence|consequently)[^.!?]{10,150}[.!?]',
        r'(?:this (?:study|work|research|paper) (?:shows|demonstrates|reveals|indicates|suggests|provides|offers|presents|contributes))[^.!?]{10,120}[.!?]',
        r'(?:key (?:finding|contribution|insight)|main (?:finding|contribution|insight)|significant (?:finding|contribution))[^.!?]{10,100}[.!?]',
        r'(?:implication|application|potential|future|promise)[^.!?]{10,100}[.!?]',
    ]
    
    takeaways = []
    for pattern in takeaway_patterns:
        for m in re.finditer(pattern, clean, re.IGNORECASE):
            sent = m.group(0).strip()
            if 15 < len(sent) < 160 and sent not in takeaways:
                takeaways.append(sent)
    
    insights["takeaways"] = " ".join(takeaways[:3])
    
    # Extract Themes - topic/keyword based themes from section
    section_lower = section_name.lower()
    theme_indicators = []
    
    # Domain-specific theme keywords
    theme_keywords = {
        "methodology": ["algorithm", "technique", "approach", "method", "procedure", "process", "implementation"],
        "results": ["accuracy", "performance", "efficiency", "speed", "precision", "recall", "f1", "score", "benchmark"],
        "introduction": ["background", "motivation", "problem", "challenge", "objective", "goal", "aim"],
        "conclusion": ["summary", "implication", "future", "limitation", "contribution"],
    }
    
    for theme, keywords in theme_keywords.items():
        if theme in section_lower:
            for kw in keywords:
                if kw in clean.lower():
                    theme_indicators.append(kw)
    
    if theme_indicators:
        insights["themes"] = ", ".join(list(set(theme_indicators))[:6])
    else:
        # Extract top keywords as themes
        words = re.findall(r'\b[a-zA-Z]{4,}\b', clean.lower())
        stop = {"this", "that", "with", "from", "have", "been", "will", "they", "were", "their", "which", "also", "each", "into", "about", "paper", "study", "proposed", "using", "method", "used", "results", "data", "model", "based", "shown", "show", "figure", "table", "section", "approach", "research", "analysis", "system", "work", "however", "therefore", "thus", "such", "through", "these", "those", "between", "where", "when", "both", "more", "most", "some", "other", "than", "then", "there", "after", "before", "since", "while", "although", "because", "first", "second", "third", "given", "found", "make", "made", "well", "even", "just", "very", "high", "large", "small", "different", "various", "several", "many", "number", "present", "existing", "recent", "current", "previous", "general", "specific", "important", "significant", "main", "new", "novel", "effective", "efficient", "improve", "better", "good", "best", "provide", "achieve", "perform", "task", "network", "learning", "training", "test", "performance", "accuracy"}
        freq = Counter(w for w in words if w not in stop)
        top_words = [w for w, c in freq.most_common(5)]
        insights["themes"] = ", ".join(top_words) if top_words else ""
    
    return insights


def _extractive_points(content: str, max_points: int = 5) -> list[str]:
    """Extract top informative sentences as bullet-ready points."""
    if not content:
        return []

    text = re.sub(r'\s+', ' ', content).strip()
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if 18 <= len(s.strip()) <= 240]
    if not sentences:
        return []

    stop = {
        "the", "and", "for", "with", "this", "that", "from", "have", "been", "were",
        "their", "which", "also", "into", "about", "using", "method", "study", "paper",
        "results", "data", "model", "based", "section", "analysis", "system", "these",
        "those", "between", "when", "both", "more", "most", "such", "than", "then",
    }
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    freq = Counter(w for w in words if w not in stop)
    if not freq:
        return sentences[:max_points]

    cue_words = {
        "propose", "present", "introduce", "demonstrate", "show", "results", "improve",
        "outperform", "significant", "novel", "conclusion", "future", "limitation",
    }

    scored = []
    for idx, sent in enumerate(sentences):
        sent_words = re.findall(r'\b[a-z]{4,}\b', sent.lower())
        if not sent_words:
            continue

        # Average term frequency score
        base = sum(freq.get(w, 0) for w in sent_words) / len(sent_words)

        # Promote key scientific claim/summary sentences
        cue_boost = 1.2 if any(c in sent.lower() for c in cue_words) else 1.0

        # Prefer early/mid section evidence while still keeping conclusion candidates
        position_boost = 1.0 + (0.15 if idx < max(2, len(sentences) // 5) else 0.0)

        score = base * cue_boost * position_boost
        scored.append((score, idx, sent))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = sorted(scored[: max_points + 2], key=lambda x: x[1])[:max_points]

    points: list[str] = []
    seen = set()
    for _, _, sent in top:
        key = re.sub(r'[^a-z0-9]+', '', sent.lower())[:120]
        if key and key not in seen:
            points.append(sent)
            seen.add(key)

    return points[:max_points]


def _to_bulleted_text(points: list[str]) -> str:
    return "\n".join(f"- {p.strip()}" for p in points if p and p.strip())


def analyze_sections(sections: dict, section_summarizer=None) -> dict[str, dict]:
    """
    Build enriched section payload with section-wise summaries and insights.
    Returns:
        {
          "Introduction": {
            "content": "...",
            "summary": "...",
            "highlights": "...",
            "key_points": "...",
            "takeaways": "...",
            "themes": "...",
            "word_count": 123
          }
        }
    """
    enriched: dict[str, dict] = {}
    if not isinstance(sections, dict):
        return enriched

    for name, raw in sections.items():
        content = _section_text(raw).strip()
        if not content:
            continue

        insights = _extract_section_insights(name, content)
        scored_points = _extractive_points(content, max_points=5)
        if not scored_points:
            short_sents = re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', content))
            scored_points = [s.strip() for s in short_sents if len(s.strip()) >= 12][:4]
        if not scored_points and content.strip():
            scored_points = [content.strip()[:220]]
        summary = ""
        if callable(section_summarizer):
            try:
                summary = section_summarizer(name, content) or ""
            except Exception:
                summary = ""

        # Fallback to extractive scoring so each section always has meaningful points.
        if not summary and scored_points:
            summary = _to_bulleted_text(scored_points[:4])
        if not insights.get("highlights") and scored_points:
            insights["highlights"] = _to_bulleted_text(scored_points[:3])
        if not insights.get("key_points") and scored_points:
            insights["key_points"] = _to_bulleted_text(scored_points[:4])
        if not insights.get("takeaways") and scored_points:
            insights["takeaways"] = _to_bulleted_text(scored_points[-2:])
        if not insights.get("themes"):
            words = re.findall(r'\b[a-zA-Z]{5,}\b', content.lower())
            common = [w for w, _ in Counter(words).most_common(4)]
            insights["themes"] = ", ".join(common)

        enriched[name] = {
            "content": content,
            "summary": summary,
            "highlights": insights.get("highlights", ""),
            "key_points": insights.get("key_points", ""),
            "takeaways": insights.get("takeaways", ""),
            "themes": insights.get("themes", ""),
            "word_count": len(content.split()),
        }

    return enriched


def _heuristic(text: str) -> dict[str, str]:
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if len(p.strip().split()) > 15]
    if not paras:
        return {"Full Text": text}
    n = len(paras)
    out = {}
    out["Abstract"]     = paras[0]
    if n > 3:
        out["Introduction"] = ' '.join(paras[1: max(2, n//5)])
    if n > 5:
        out["Methodology"]  = ' '.join(paras[n//5: n//2])
        out["Results"]      = ' '.join(paras[n//2: 4*n//5])
    out["Conclusion"]   = paras[-1]
    return out


#  Metadata 
def extract_metadata(text: str, sections: dict) -> dict:
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    #  Better title extraction 
    title = _sanitize_metadata_text(_extract_title(lines, text), max_len=220)

    #  Better author extraction 
    authors = _sanitize_metadata_text(_extract_authors(lines, title), max_len=180)
    if authors != "N/A" and (
        "<" in authors
        or "style=" in authors.lower()
        or "href=" in authors.lower()
    ):
        authors = "N/A"

    year_m = re.search(r'\b(20[0-2]\d|19[89]\d)\b', text[:4000])
    year   = year_m.group(0) if year_m else "N/A"

    doi_m  = re.search(r'\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b', text[:8000])
    doi    = doi_m.group(0).rstrip('.,)') if doi_m else None

    words  = len(re.findall(r'\b\w+\b', text))
    refs   = sections.get("References", "")
    ref_n  = len(re.findall(r'^\[\d+\]|^\d+\.', refs, re.MULTILINE)) if refs else 0

    tl = text.lower()
    domain = _detect_domain(tl)
    rtype  = _detect_type(tl)

    # Patent detection
    is_patent = _detect_patent(text, tl)

    return {
        "title":           title,
        "authors":         authors,
        "year":            year,
        "doi":             doi,
        "word_count":      words,
        "section_count":   len([k for k in sections if k not in ("References","Appendix")]),
        "reference_count": ref_n,
        "domain":          domain,
        "research_type":   rtype,
        "is_patent":       is_patent,
    }


def _extract_title(lines: list[str], text: str) -> str:
    """Extract title robustly from top-of-paper lines."""
    if not lines:
        return "Untitled"

    # Prefer lines before first major heading.
    heading_idx = None
    for i, line in enumerate(lines[:40]):
        ll = line.strip().lower()
        if re.match(r'^(abstract|introduction|summary)\b', ll):
            heading_idx = i
            break
    scope = lines[: heading_idx] if heading_idx and heading_idx > 0 else lines[:20]

    candidates: list[tuple[float, str]] = []
    for idx, line in enumerate(scope):
        l = line.strip()
        ll = l.lower()
        if not l or len(l) < 12 or len(l) > 220:
            continue
        if any(tag in ll for tag in ["<span", "<div", "<a ", "</", "style=", "href="]):
            continue
        if any(kw in ll for kw in [
            "doi:", "http", "journal", "department", "university", "conference",
            "proceedings", "volume", "issue", "page", "email", "e-mail", "@",
            "received", "accepted", "keywords:", "index terms", "copyright",
        ]):
            continue

        words = l.split()
        if len(words) < 3 or len(words) > 22:
            continue

        # Avoid abstract-like long narrative lines.
        if l.endswith(".") and len(words) > 12:
            continue

        comma_penalty = l.count(",") * 0.2
        early_bonus = max(0.0, 1.6 - idx * 0.12)
        length_bonus = 1.0 if 6 <= len(words) <= 16 else 0.4
        caps_ratio = sum(1 for w in words if w[:1].isupper()) / max(len(words), 1)
        caps_bonus = caps_ratio * 0.8

        score = early_bonus + length_bonus + caps_bonus - comma_penalty
        candidates.append((score, l))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        title = candidates[0][1]
        return title[:197] + "..." if len(title) > 200 else title

    return lines[0][:200]

def _extract_authors(lines: list[str], title: str) -> str:
    """Extract author names near the title block."""
    if not lines:
        return "N/A"

    author_pattern = re.compile(
        r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}|[A-Z]\.\s?[A-Z][a-z]+)\b'
    )
    skip_words = {
        "abstract", "doi", "http", "journal", "department", "university",
        "conference", "proceedings", "volume", "introduction", "conclusion",
        "methodology", "results", "keywords", "index", "school", "faculty",
    }

    title_idx = 0
    for i, l in enumerate(lines[:30]):
        if title and title[:35].lower() in l.lower():
            title_idx = i
            break

    scan = []
    for l in lines[title_idx + 1 : title_idx + 8]:
        ll = l.lower().strip()
        if re.match(r'^(abstract|introduction|summary)\b', ll):
            break
        scan.append(l.strip())

    for l in scan:
        if not l or len(l) < 4 or len(l) > 220:
            continue
        ll = l.lower()
        if any(k in ll for k in skip_words):
            continue

        matches = author_pattern.findall(l)
        if len(matches) >= 2 or (len(matches) >= 1 and ("," in l or " and " in ll)):
            return l

    return "N/A"

def _detect_domain(tl: str) -> str:
    for dom, kws in [
        ("NLP / Text Mining",       ["natural language","nlp","bert","transformer","text classification","sentiment","named entity"]),
        ("Machine Learning",        ["machine learning","deep learning","neural network","gradient descent","backpropagation"]),
        ("Computer Vision",         ["image recognition","object detection","computer vision","convolutional","segmentation","yolo"]),
        ("Healthcare / Biomedical", ["clinical","patient","medical","disease","diagnosis","drug","biomedical"]),
        ("Cybersecurity",           ["security","malware","intrusion detection","attack","firewall","cryptography","vulnerability"]),
        ("Data Science / Analytics",["data mining","big data","clustering","feature engineering","analytics","data warehouse"]),
        ("IoT / Embedded Systems",  ["iot","internet of things","embedded","sensor","microcontroller","edge computing"]),
        ("Cloud / Distributed",     ["cloud computing","serverless","microservices","docker","kubernetes","distributed"]),
        ("Robotics / Control",      ["robot","autonomous","control system","pid","servo","actuator"]),
        ("Renewable Energy",        ["solar","wind energy","photovoltaic","battery","energy harvesting","renewable"]),
        ("Materials Science",       ["nanomaterial","polymer","composite","alloy","crystalline","substrate"]),
    ]:
        if any(k in tl for k in kws):
            return dom
    return "General CS"


def _detect_type(tl: str) -> str:
    if any(w in tl for w in ["systematic review","literature survey","we survey","we review"]):
        return "Survey / Review"
    elif any(w in tl for w in ["we propose","novel","we introduce","we present a new"]):
        return "Novel Methodology"
    elif any(w in tl for w in ["case study","real-world deployment","field study"]):
        return "Case Study"
    elif any(w in tl for w in ["theorem","lemma","proof","corollary"]):
        return "Theoretical"
    return "Empirical Study"


def _detect_patent(text: str, tl: str) -> bool:
    patent_signals = [
        "patent no", "patent number", "united states patent",
        "international patent", "patent application",
        "claims:", "claim 1.", "wherein said",
        "field of the invention", "background of the invention",
        "summary of the invention", "brief description of the drawings",
        "detailed description of the preferred",
        "assignee:", "inventor:", "filing date:",
        "patent pending", "all rights reserved patent",
    ]
    score = sum(1 for sig in patent_signals if sig in tl)
    return score >= 2


#  Limitations & Advantages 
def extract_limitations(text: str, sections: dict) -> list[str]:
    """Extract limitations from paper text with improved patterns."""
    limitations = []

    # Search in ALL sections for better coverage
    all_sections = list(sections.keys())
    search_text = ""
    for sec in all_sections:
        if sec.lower() not in ['references', 'appendix']:
            search_text += "\n" + _section_text(sections.get(sec, ""))

    if not search_text:
        search_text = text[:15000]

    # Enhanced sentence-level patterns for limitations
    limit_patterns = [
        r'(?:one|a|the|our|this|main|key|major|notable|primary)?\s*limitation[s]?\s+(?:of|is|are|include|such as|being|observed|noted)[^.!?]{10,200}[.!?]',
        r'(?:we|our|the) (?:did not|could not|were unable to|cannot|do not|have not|has not)[^.!?]{10,150}[.!?]',
        r'(?:shortcoming|drawback|weakness|challenge|constraint|restriction)[s]?[^.!?]{10,150}[.!?]',
        r'(?:not (?:consider|account|address|include|cover|test|evaluat|applied|used))[^.!?]{5,120}[.!?]',
        r'(?:only|solely|exclusively) (?:tested|evaluated|applied|used)[^.!?]{5,100}[.!?]',
        r'(?:small|limited|insufficient) (?:dataset|sample|data|corpus|training|test)[^.!?]{5,100}[.!?]',
        r'(?:lack|absence) of[^.!?]{5,100}[.!?]',
        r'(?:computationally expensive|high computational|resource intensive|expensive)[^.!?]{0,100}[.!?]',
        r'(?:requires|require|need|needed) (?:large|extensive|significant|substantial|more)[^.!?]{5,100}[.!?]',
        r'(?:limited|restrict) (?:to|by|in)[^.!?]{5,80}[.!?]',
    ]

    seen = set()
    for pattern in limit_patterns:
        try:
            for m in re.finditer(pattern, search_text, re.IGNORECASE):
                sent = m.group(0).strip()
                sent = re.sub(r'\s+', ' ', sent)
                key = sent[:60].lower()
                if key not in seen and 15 < len(sent) < 350:
                    limitations.append(sent)
                    seen.add(key)
                if len(limitations) >= 8:
                    break
        except:
            continue
        if len(limitations) >= 8:
            break

    return limitations[:8]


def extract_advantages(text: str, sections: dict) -> list[str]:
    """Extract advantages/contributions from paper text with improved patterns."""
    advantages = []

    # Search in ALL sections
    all_sections = list(sections.keys())
    search_text = ""
    for sec in all_sections:
        if sec.lower() not in ['references', 'appendix']:
            search_text += "\n" + _section_text(sections.get(sec, ""))

    if not search_text:
        search_text = text[:15000]

    # Enhanced patterns for advantages/contributions
    adv_patterns = [
        r'(?:we propose|we present|we introduce|we develop|propose|introduce)[^.!?]{10,200}[.!?]',
        r'(?:novel|innovative|new) (?:approach|method|framework|technique|model|algorithm|system)[^.!?]{5,150}[.!?]',
        r'(?:outperform|outperforms|outperformed|superior|better|improved|significantly better|state-of-the-art|sota)[^.!?]{5,150}[.!?]',
        r'(?:achieve|achieves|achieved|attain|attains) (?:state-of-the-art|best|highest|superior|improved|good|excellent)[^.!?]{5,150}[.!?]',
        r'(?:contribution[s]?|main contribution)[^.!?]{5,150}[.!?]',
        r'(?:advantage[s]?|strength[s]?) (?:of|include|such as|are)[^.!?]{5,150}[.!?]',
        r'(?:effective|efficient|accurate|robust|scalable|lightweight|fast|powerful)[^.!?]{5,150}(?:method|approach|system|model|solution|technique)[^.!?]{0,80}[.!?]',
        r'(?:reduce|reduction|minimize|lower|decrease) (?:error|cost|time|complexity|overhead|latency)[^.!?]{5,100}[.!?]',
        r'(?:improve|improvement|enhance|boost|increase) (?:accuracy|performance|efficiency|speed|robustness)[^.!?]{5,150}[.!?]',
        r'(?:first|pioneering|novel) (?:work|study|paper|approach|method)[^.!?]{5,150}[.!?]',
        r'(?:key|main|major|primary|significant|core) (?:contribution|result|finding|advantage|benefit)[s]?[^.!?]{5,150}[.!?]',
    ]

    seen = set()
    for pattern in adv_patterns:
        try:
            for m in re.finditer(pattern, search_text, re.IGNORECASE):
                sent = m.group(0).strip()
                sent = re.sub(r'\s+', ' ', sent)
                key = sent[:60].lower()
                if key not in seen and 15 < len(sent) < 350:
                    advantages.append(sent)
                    seen.add(key)
                if len(advantages) >= 8:
                    break
        except:
            continue
        if len(advantages) >= 8:
            break

    return advantages[:8]


#  Plagiarism Estimation 
COMMON_ACADEMIC_PHRASES = [
    "in this paper we propose", "in this paper, we present",
    "the results show that", "the experimental results demonstrate",
    "state of the art", "deep learning", "machine learning",
    "convolutional neural network", "the proposed method",
    "in recent years", "with the rapid development",
    "a novel approach", "significantly outperforms",
    "our experimental results", "we evaluate our",
    "the main contributions of this paper",
    "to the best of our knowledge",
    "this paper is organized as follows",
    "the remainder of this paper",
    "as shown in figure", "as shown in table",
    "standard deviation", "mean squared error",
    "baseline model", "benchmark dataset",
    "data augmentation", "transfer learning",
    "in conclusion", "future work will",
]

def estimate_plagiarism(text: str) -> dict:
    """
    Estimate plagiarism based on common academic boilerplate phrases.
    Returns a dict with score and analysis.
    NOTE: This is a heuristic estimate, not a real plagiarism check.
    """
    words = text.split()
    total_words = max(len(words), 1)
    tl = text.lower()

    # Count common boilerplate phrases
    boilerplate_hits = sum(1 for p in COMMON_ACADEMIC_PHRASES if p in tl)
    boilerplate_ratio = min(boilerplate_hits / len(COMMON_ACADEMIC_PHRASES), 1.0)

    # Check for repetitive n-grams (self-plagiarism indicator)
    ngrams = []
    for i in range(len(words) - 4):
        ngram = ' '.join(words[i:i+5]).lower()
        ngrams.append(ngram)
    ngram_counter = Counter(ngrams)
    repeated = sum(v - 1 for v in ngram_counter.values() if v > 1)
    repetition_ratio = min(repeated / max(len(ngrams), 1), 0.3)

    # Estimate: boilerplate is unavoidable in academic writing
    # A "clean" paper still has ~20% boilerplate
    base_score = (boilerplate_ratio * 15) + (repetition_ratio * 100)
    estimated_pct = min(round(base_score, 1), 45)  # cap at 45%

    level = "Low"
    color = "#16a34a"
    if estimated_pct > 30:
        level = "High"
        color = "#dc2626"
    elif estimated_pct > 15:
        level = "Moderate"
        color = "#d97706"

    return {
        "estimated_pct":   estimated_pct,
        "level":           level,
        "color":           color,
        "boilerplate_hits":boilerplate_hits,
        "note": (
            "This is a heuristic estimate based on common academic phrases and repetition. "
            "Use iThenticate, Turnitin, or similar for authoritative results."
        ),
    }


def generate_paraphrased_excerpt(text: str) -> str:
    """Return cleaned version of text with boilerplate reduced."""
    # Replace very common boilerplate openers
    replacements = {
        "in this paper, we propose": "this work presents",
        "in this paper we propose":  "this work presents",
        "in this paper, we present": "the present study introduces",
        "in this paper we present":  "the present study introduces",
        "to the best of our knowledge": "as far as known",
        "the remainder of this paper is organized as follows": "the document is structured as follows",
        "this paper is organized as follows": "this document proceeds as follows",
        "in recent years": "recently",
        "with the rapid development of": "given advances in",
        "the experimental results demonstrate": "experiments confirm",
        "the results show that": "results indicate",
        "as shown in figure": "as illustrated in figure",
        "as shown in table": "as presented in table",
        "future work will": "subsequent work may",
        "in conclusion": "in summary",
        "state of the art": "leading approaches",
        "state-of-the-art": "leading approaches",
    }
    result = text
    for orig, repl in replacements.items():
        result = re.sub(re.escape(orig), repl, result, flags=re.IGNORECASE)
    return result


#  Sentiment Analysis 
POSITIVE_WORDS = {
    "effective", "efficient", "accurate", "robust", "novel", "innovative",
    "superior", "improved", "significant", "outperform", "promising",
    "reliable", "scalable", "lightweight", "fast", "powerful", "strong",
    "excellent", "best", "optimal", "precise", "better", "high", "enhance",
    "successful", "achieve", "advance", "breakthrough", "state-of-the-art",
}
NEGATIVE_WORDS = {
    "limitation", "drawback", "weakness", "difficult", "challenge",
    "constraint", "restricted", "limited", "insufficient", "poor",
    "error", "fail", "slow", "expensive", "complex", "difficult",
    "problematic", "inadequate", "low", "incomplete", "biased",
    "unstable", "unreliable", "ambiguous",
}

def analyze_sentiment(text: str) -> dict:
    """Return sentiment score based on full text."""
    # If text is actually a dict (sections), handle that case
    if isinstance(text, dict):
        # It's sections dict - iterate through it
        results = {}
        all_pos, all_neg = 0, 0
        
        for name, content in text.items():
            if not content or name in ("References", "Appendix"):
                continue
            words = re.findall(r'\b[a-z]+\b', str(content).lower())
            pos = sum(1 for w in words if w in POSITIVE_WORDS)
            neg = sum(1 for w in words if w in NEGATIVE_WORDS)
            total = pos + neg
            if total == 0:
                score = 0.5
                label = "Neutral"
            else:
                score = pos / total
                label = "Positive" if score > 0.6 else ("Negative" if score < 0.4 else "Neutral")
            results[name] = {"pos": pos, "neg": neg, "score": round(score, 2), "label": label}
            all_pos += pos
            all_neg += neg
        
        total = all_pos + all_neg
        overall_score = round(all_pos / total, 2) if total > 0 else 0.5
        overall_label = "Positive" if overall_score > 0.6 else ("Negative" if overall_score < 0.4 else "Neutral")
        results["_overall"] = {
            "pos": all_pos, "neg": all_neg,
            "score": overall_score, "label": overall_label
        }
        return results
    
    # It's plain text - analyze overall sentiment
    if not text:
        return {"_overall": {"pos": 0, "neg": 0, "score": 0.5, "label": "Neutral"}}
    
    words = re.findall(r'\b[a-z]+\b', str(text).lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    
    if total == 0:
        score = 0.5
        label = "Neutral"
    else:
        score = pos / total
        label = "Positive" if score > 0.6 else ("Negative" if score < 0.4 else "Neutral")
    
    return {
        "_overall": {
            "pos": pos, 
            "neg": neg,
            "score": round(score, 2), 
            "label": label
        }
    }


#  Research Gap Detection 
GAP_PATTERNS = [
    r'(?:no|little|limited|few|lack of|insufficient|scarce) (?:work|study|research|attention|focus|investigation)[^.!?]{5,120}[.!?]',
    r'(?:has not been|have not been|remains unexplored|rarely explored|largely unexplored)[^.!?]{5,100}[.!?]',
    r'(?:existing|current|prior|previous) (?:methods|approaches|work|studies|literature) (?:fail|do not|does not|cannot|ignore|neglect|overlook)[^.!?]{5,120}[.!?]',
    r'(?:gap|shortcoming|open problem|open question|open challenge)[^.!?]{5,100}[.!?]',
    r'(?:to our knowledge|to the best of our knowledge)[^.!?]{5,120}[.!?]',
    r'(?:there is a need|need for|need to|requires further|warrants further|calls for further)[^.!?]{5,100}[.!?]',
    r'(?:not yet|yet to be|still unclear|still unknown|still an open)[^.!?]{5,100}[.!?]',
]

def detect_research_gaps(text: str, sections: dict) -> list[str]:
    search_text = ""
    for sec in ["Introduction", "Related Work", "Literature Review",
                "Problem Statement", "Background", "Conclusion", "Future Work"]:
        if sec in sections:
            search_text += "\n" + _section_text(sections[sec])
    if not search_text:
        search_text = text[:6000]

    gaps = []
    seen = set()
    for pattern in GAP_PATTERNS:
        for m in re.finditer(pattern, search_text, re.IGNORECASE):
            # Fix spacing - replace multiple whitespace with single space
            sent = re.sub(r'\s+', ' ', m.group(0).strip())
            # Ensure proper spacing after punctuation
            sent = re.sub(r'([.!?])\s*', r'\1 ', sent)
            # Remove multiple spaces
            sent = re.sub(r' +', ' ', sent)
            key = sent[:50].lower()
            if key not in seen and 20 < len(sent) < 300:
                gaps.append(sent)
                seen.add(key)
        if len(gaps) >= 5:
            break
    return gaps[:5]


#  Trend Identification 
TECH_TRENDS = {
    "Large Language Models": ["llm", "gpt", "chatgpt", "llama", "large language model", "foundation model"],
    "Transformer Architecture": ["transformer", "attention mechanism", "self-attention", "bert", "vit"],
    "Federated Learning": ["federated learning", "federated", "privacy-preserving", "decentralized learning"],
    "Explainable AI (XAI)": ["explainability", "interpretability", "xai", "explainable ai", "shap", "lime"],
    "Edge Computing": ["edge computing", "edge intelligence", "tinyml", "on-device"],
    "Generative AI": ["generative", "diffusion model", "gan", "stable diffusion", "dall-e", "vae"],
    "Graph Neural Networks": ["graph neural", "gnn", "graph convolutional", "knowledge graph"],
    "Few-shot / Zero-shot": ["few-shot", "zero-shot", "meta-learning", "prompt engineering", "in-context"],
    "Multimodal AI": ["multimodal", "vision-language", "vlm", "image-text", "audio-visual"],
    "Reinforcement Learning": ["reinforcement learning", "rl", "reward function", "policy gradient", "q-learning"],
    "AutoML / NAS": ["automl", "neural architecture search", "nas", "hyperparameter"],
    "Quantum Computing": ["quantum", "qubit", "quantum circuit", "quantum machine learning"],
    "Contrastive Learning": ["contrastive learning", "self-supervised", "siamese", "clip"],
    "Green AI": ["energy efficient", "carbon footprint", "green ai", "sustainable ai", "co2"],
}

def identify_trends(text: str) -> list[dict]:
    tl = text.lower()
    detected = []
    for trend, keywords in TECH_TRENDS.items():
        hits = [kw for kw in keywords if kw in tl]
        if hits:
            # Count occurrences
            count = sum(tl.count(kw) for kw in hits)
            # Fix spacing in trend name
            trend_name = re.sub(r'\s+', ' ', trend).strip()
            detected.append({
                "trend":    trend_name if 'trend_name' in locals() else trend,
                "keywords": hits[:3],
                "count":    count,
                "strength": "Strong" if count > 5 else ("Moderate" if count > 2 else "Weak"),
            })
    # Fix spacing in trend names
    for t in detected:
        t["trend"] = re.sub(r'\s+', ' ', t["trend"]).strip()
    
    detected.sort(key=lambda x: x["count"], reverse=True)
    return detected[:8]


#  Keywords 
def extract_keywords(text: str, n: int = 18) -> list[dict]:
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
    stop = {
        "with","that","this","from","have","been","will","they","were","their",
        "which","also","each","into","about","paper","study","proposed","using",
        "method","used","results","data","model","based","shown","show","figure",
        "table","section","approach","research","analysis","system","work",
        "however","therefore","thus","such","through","these","those","between",
        "within","where","when","both","more","most","some","other","than","then",
        "there","after","before","since","while","although","because","first",
        "second","third","given","found","make","made","well","even","just","very",
        "high","large","small","different","various","several","many","number",
        "present","existing","recent","current","proposed","previous","general",
        "specific","important","significant","main","new","novel","effective",
        "efficient","improved","better","good","best","provide","achieve","perform",
        "task","network","learning","training","test","performance","accuracy",
    }
    freq = Counter(w.lower() for w in words if w.lower() not in stop)
    top = freq.most_common(n)
    max_count = top[0][1] if top else 1
    return [{"word": w, "count": c, "score": round(c / max_count, 3)} for w, c in top]


def extract_models(text: str) -> list[str]:
    patterns = [
        r'\b(BERT|GPT-o?|RoBERT?[234]?a|XLNet|T5|LLaMA|LLaMA-?[23]|ChatGPT|Mistral|Phi-?\d*|Gemma|PaLM|Claude|Gemini)\b',
        r'\b(CNN|RNN|LSTM|GRU|Transformer|Multi-?Head Attention|ResNet|VGG|YOLO|EfficientNet|ViT|CLIP|DALL-E|Stable Diffusion)\b',
        r'\b(SVM|KNN|Random Forest|XGBoost|LightGBM|CatBoost|Naive Bayes|Decision Tree|Gradient Boosting|AdaBoost)\b',
        r'\b(k-means|DBSCAN|KMeans|PCA|UMAP|t-SNE|Word2Vec|GloVe|FastText|TF-IDF|BM25)\b',
        r'\b(TensorFlow|PyTorch|Keras|scikit-learn|Hugging Face|spaCy|NLTK|OpenCV|Pandas|NumPy|JAX)\b',
        r'\b(ROUGE|BLEU|METEOR|BERTScore|F1|Accuracy|Precision|Recall|AUC|mAP|NDCG)\b',
    ]
    found = set()
    for p in patterns:
        found.update(re.findall(p, text, re.IGNORECASE))
    return sorted(found)


# ============================================
# NEW FEATURES IMPLEMENTATION
# ============================================

#  Paper Quality Scoring 
def calculate_paper_quality(text: str, sections: dict, metadata: dict) -> dict:
    """
    Calculate comprehensive paper quality score based on multiple factors.
    Returns a dict with overall score and breakdown.
    """
    scores = {}
    
    # 1. Structure Score (0-100)
    section_count = len([s for s in sections.keys() if s.lower() not in ['references', 'appendix']])
    expected_sections = ['abstract', 'introduction', 'methodology', 'results', 'conclusion']
    found_sections = [s.lower() for s in sections.keys()]
    structure_hits = sum(1 for es in expected_sections if any(es in fs for fs in found_sections))
    structure_score = min(100, (structure_hits / len(expected_sections)) * 100)
    if section_count >= 6:
        structure_score = min(100, structure_score + 10)
    scores['structure'] = round(structure_score, 1)
    
    # 2. Depth Score (0-100) - Based on section word counts
    main_sections = ['Introduction', 'Methodology', 'Results', 'Discussion', 'Conclusion']
    total_words = 0
    for sec in main_sections:
        if sec in sections:
            total_words += len(_section_text(sections[sec]).split())
    # Expect at least 3000 words in main sections for high quality
    depth_score = min(100, (total_words / 3000) * 100) if total_words > 0 else 30
    scores['depth'] = round(depth_score, 1)
    
    # 3. Methodology Score (0-100)
    method_keywords = ['experiment', 'evaluation', 'dataset', 'benchmark', 'baseline', 
                      'approach', 'algorithm', 'method', 'framework', 'model', 'training',
                      'testing', 'validation', 'implementation', 'results']
    method_text = ""
    for sec in ['Methodology', 'Methods', 'Implementation', 'Experiments']:
        if sec in sections:
            method_text += _section_text(sections[sec]).lower() + " "
    method_hits = sum(1 for kw in method_keywords if kw in method_text)
    methodology_score = min(100, (method_hits / len(method_keywords)) * 100)
    scores['methodology'] = round(methodology_score, 1)
    
    # 4. Citation Score (0-100)
    ref_count = metadata.get('reference_count', 0)
    if ref_count >= 50:
        citation_score = 100
    elif ref_count >= 30:
        citation_score = 80
    elif ref_count >= 20:
        citation_score = 60
    elif ref_count >= 10:
        citation_score = 40
    else:
        citation_score = 20
    scores['citations'] = citation_score
    
    # 5. Reproducibility Score (0-100)
    repro_keywords = ['code', 'dataset', 'available', 'github', 'repository', 
                     'supplementary', 'material', 'publicly', 'open source']
    repro_text = (text.lower())[:10000]  # Check early sections
    repro_hits = sum(1 for kw in repro_keywords if kw in repro_text)
    reproducibility_score = min(100, repro_hits * 15)
    scores['reproducibility'] = round(reproducibility_score, 1)
    
    # 6. Impact Indicators Score (0-100)
    impact_keywords = ['significant', 'improve', 'outperform', 'state-of-the-art', 
                      'novel', 'innovative', 'breakthrough', 'advance', 'leader']
    impact_text = (text.lower())[:15000]
    impact_hits = sum(1 for kw in impact_keywords if kw in impact_text)
    impact_score = min(100, impact_hits * 12)
    scores['impact'] = round(impact_score, 1)
    
    # Calculate weighted overall score
    weights = {
        'structure': 0.15,
        'depth': 0.20,
        'methodology': 0.25,
        'citations': 0.15,
        'reproducibility': 0.10,
        'impact': 0.15
    }
    overall = sum(scores[k] * weights[k] for k in weights)
    
    # Determine quality tier
    if overall >= 80:
        tier = "Excellent"
        tier_color = "#059669"
    elif overall >= 65:
        tier = "Good"
        tier_color = "#2563EB"
    elif overall >= 50:
        tier = "Average"
        tier_color = "#D97706"
    else:
        tier = "Below Average"
        tier_color = "#DC2626"
    
    return {
        'overall_score': round(overall, 1),
        'tier': tier,
        'tier_color': tier_color,
        'breakdown': scores,
        'strengths': _identify_strengths(scores),
        'weaknesses': _identify_weaknesses(scores)
    }


def _identify_strengths(scores: dict) -> list[str]:
    """Identify key strengths from score breakdown."""
    strengths = []
    if scores.get('structure', 0) >= 70:
        strengths.append("Well-structured with comprehensive sections")
    if scores.get('methodology', 0) >= 70:
        strengths.append("Strong methodological description")
    if scores.get('citations', 0) >= 60:
        strengths.append("Good literature foundation")
    if scores.get('reproducibility', 0) >= 50:
        strengths.append("Reproducibility indicators present")
    if scores.get('impact', 0) >= 60:
        strengths.append("Clear impact/contribution statements")
    return strengths


def _identify_weaknesses(scores: dict) -> list[str]:
    """Identify key weaknesses from score breakdown."""
    weaknesses = []
    if scores.get('structure', 0) < 50:
        weaknesses.append("Missing key sections or incomplete structure")
    if scores.get('depth', 0) < 50:
        weaknesses.append("Limited depth of analysis")
    if scores.get('methodology', 0) < 50:
        weaknesses.append("Methodology could be more detailed")
    if scores.get('citations', 0) < 40:
        weaknesses.append("Limited literature review")
    if scores.get('reproducibility', 0) < 30:
        weaknesses.append("No reproducibility indicators found")
    return weaknesses


#  Semantic Similarity Analysis 
def calculate_similarity(paper1: dict, paper2: dict) -> dict:
    """
    Calculate semantic similarity between two papers.
    Returns similarity score and breakdown.
    """
    # 1. Keyword Overlap
    kw1 = set(k['word'].lower() for k in paper1.get('keywords', [])[:15])
    kw2 = set(k['word'].lower() for k in paper2.get('keywords', [])[:15])
    if kw1 and kw2:
        keyword_jaccard = len(kw1 & kw2) / len(kw1 | kw2)
    else:
        keyword_jaccard = 0
    
    # 2. Domain Match
    domain1 = paper1.get('metadata', {}).get('domain', '')
    domain2 = paper2.get('metadata', {}).get('domain', '')
    domain_match = 1.0 if domain1 == domain2 else 0.0
    
    # 3. Model/Method Overlap
    mods1 = set(m.lower() for m in paper1.get('models_methods', []))
    mods2 = set(m.lower() for m in paper2.get('models_methods', []))
    if mods1 and mods2:
        model_jaccard = len(mods1 & mods2) / len(mods1 | mods2)
    else:
        model_jaccard = 0
    
    # 4. Research Type Match
    rt1 = paper1.get('metadata', {}).get('research_type', '')
    rt2 = paper2.get('metadata', {}).get('research_type', '')
    type_match = 1.0 if rt1 == rt2 else 0.3  # Partial credit for different types
    
    # 5. Word Count Similarity (normalize)
    wc1 = paper1.get('metadata', {}).get('word_count', 0)
    wc2 = paper2.get('metadata', {}).get('word_count', 0)
    if wc1 and wc2:
        wc_ratio = min(wc1, wc2) / max(wc1, wc2)
    else:
        wc_ratio = 0.5
    
    # Weighted overall similarity
    weights = {
        'keyword': 0.30,
        'domain': 0.20,
        'model': 0.25,
        'type': 0.10,
        'length': 0.15
    }
    overall = (
        keyword_jaccard * weights['keyword'] +
        domain_match * weights['domain'] +
        model_jaccard * weights['model'] +
        type_match * weights['type'] +
        wc_ratio * weights['length']
    )
    
    # Determine similarity level
    if overall >= 0.7:
        level = "Highly Similar"
        color = "#059669"
    elif overall >= 0.5:
        level = "Moderately Similar"
        color = "#2563EB"
    elif overall >= 0.3:
        level = "Somewhat Similar"
        color = "#D97706"
    else:
        level = "Dissimilar"
        color = "#64748B"
    
    return {
        'similarity_score': round(overall * 100, 1),
        'level': level,
        'color': color,
        'breakdown': {
            'keyword_overlap': round(keyword_jaccard * 100, 1),
            'domain_match': round(domain_match * 100, 1),
            'model_overlap': round(model_jaccard * 100, 1),
            'type_match': round(type_match * 100, 1),
            'length_similarity': round(wc_ratio * 100, 1)
        }
    }


#  Journal/Conference Recommendations 
JOURNAL_DATABASE = {
    "NLP / Text Mining": {
        "top": ["ACL Anthology", "EMNLP", "NAACL", "COLING", "TACL"],
        "high": ["ACL", "EMNLP", "NAACL", "COLING", "AAAI", "IJCAI"],
        "medium": ["ACL", "NAACL", "EACL", "COLING", "ICML", "ICLR"]
    },
    "Machine Learning": {
        "top": ["ICML", "NeurIPS", "ICLR", "JMLR", "Machine Learning"],
        "high": ["ICML", "NeurIPS", "ICLR", "AAAI", "IJCAI", "AISTATS"],
        "medium": ["ICML", "NeurIPS", "ECAI", "ACML", "UAI", "COLT"]
    },
    "Computer Vision": {
        "top": ["CVPR", "ICCV", "ECCV", "WACV", "PAMI"],
        "high": ["CVPR", "ICCV", "ECCV", "BMVC", "AAAI", "IJCAI"],
        "medium": ["CVPR", "ICCV", "WACV", "ICPR", "CAIP", "ACCV"]
    },
    "Healthcare / Biomedical": {
        "top": ["Nature Medicine", "Lancet", "JAMA", "NEJM", "Cell"],
        "high": ["Nature Medicine", "Nature Methods", "Bioinformatics", "BMC Medical", "JAMIA"],
        "medium": ["BMC Bioinformatics", "Journal of Biomedical", "Health Informatics", "MedIA"]
    },
    "Cybersecurity": {
        "top": ["IEEE S&P", "USENIX Security", "CCS", "NDSS", "ASIACCS"],
        "high": ["IEEE S&P", "USENIX Security", "CCS", "NDSS", "RAID", "ACSAC"],
        "medium": ["SecureComm", "Wisec", "CyberSci", "JCS", "IET Information Security"]
    },
    "Data Science / Analytics": {
        "top": ["KDD", "SIGMOD", "VLDB", "ICDE", "EDBT"],
        "high": ["KDD", "SIGMOD", "VLDB", "ICDE", "SDM", "PAKDD"],
        "medium": ["KDD", "SIGMOD", "VLDB", "DOLAP", "SSDBM", "Data Science"]
    },
    "IoT / Embedded Systems": {
        "top": ["IEEE IoT Journal", "ACM TECS", "Embedded Systems", "RTSS", "DAC"],
        "high": ["IEEE IoT Journal", "ACM TECS", "IEEE TCAD", "IEEE T-ASE", "EMSOFT"],
        "medium": ["IEEE IoT", "Sensors", "JSS", "Microprocessors", "Embedded Computing"]
    },
    "Cloud / Distributed": {
        "top": ["SOSP", "OSDI", "EuroSys", "ATC", "SOCC"],
        "high": ["SOSP", "OSDI", "EuroSys", "USENIX ATC", "Middleware", "ICDCS"],
        "medium": ["EuroSys", "USENIX ATC", "Middleware", "CloudCom", "IC2E", "SERVICES"]
    },
    "Robotics / Control": {
        "top": ["IJRR", "TRO", "ICRA", "IROS", "RSS"],
        "high": ["IJRR", "TRO", "ICRA", "IROS", "Autonomous Robots", "Robotics"],
        "medium": ["ICRA", "IROS", "Robotics", "Autonomous", "IFAC", "Robotica"]
    },
    "Renewable Energy": {
        "top": ["Nature Energy", "Joule", "Energy & Environmental", "Applied Energy", "Renewable Energy"],
        "high": ["Energy", "Applied Energy", "Renewable Energy", "Solar Energy", "Energy Reports"],
        "medium": ["Renewable Energy", "Solar Energy", "Energy Reports", "Sustainability", "Clean Technologies"]
    },
    "Materials Science": {
        "top": ["Nature Materials", "Science", "Advanced Materials", "Nature", "Nature Communications"],
        "high": ["Advanced Materials", "ACS Nano", "Scientific Reports", "Materials Horizons", "Nanoscale"],
        "medium": ["Scientific Reports", "Materials", "Nanomaterials", "Applied Sciences", "Materials Today"]
    },
    "General CS": {
        "top": ["CACM", "Communications of the ACM", "IEEE Computer", "ACM Computing Surveys"],
        "high": ["IEEE Computer", "ACM Computing Surveys", "Information Sciences", "JPDC", "PFG"],
        "medium": ["IEEE Computer", "Computer", "Procedia CS", "IJCS", "ArXiv"]
    }
}


def recommend_journals_conferences(paper: dict) -> dict:
    """
    Recommend suitable journals and conferences based on paper domain and quality.
    """
    domain = paper.get('metadata', {}).get('domain', 'General CS')
    quality = paper.get('quality_score', {}).get('tier', 'Average')
    research_type = paper.get('metadata', {}).get('research_type', 'Empirical Study')
    
    # Get tier recommendations
    if quality == "Excellent":
        tier = "top"
    elif quality == "Good":
        tier = "high"
    else:
        tier = "medium"
    
    # Get recommendations for domain
    domain_recs = JOURNAL_DATABASE.get(domain, JOURNAL_DATABASE["General CS"])
    
    journals = domain_recs.get(tier, domain_recs["medium"])
    conferences = [j for j in journals if any(c in j.upper() for c in ['CONF', 'SYMP', 'SEM', 'PROC', 'ACM', 'IEEE', 'CVPR', 'ICML', 'NeurIPS', 'ICLR', 'ACL'])]
    journal_pubs = [j for j in journals if j not in conferences]
    
    # Add general recommendations if domain specific are limited
    if len(journals) < 3:
        general = JOURNAL_DATABASE["General CS"][tier]
        for g in general:
            if g not in journals:
                journals.append(g)
    
    return {
        'domain': domain,
        'quality_tier': quality,
        'research_type': research_type,
        'recommended_journals': journal_pubs[:5],
        'recommended_conferences': conferences[:5],
        'all_recommendations': journals[:8],
        'tips': _get_publication_tips(domain, quality)
    }


def _get_publication_tips(domain: str, quality: str) -> list[str]:
    """Get publication tips based on domain and quality."""
    tips = []
    
    if quality in ["Excellent", "Good"]:
        tips.append("Consider submitting to top-tier venues first for maximum visibility")
        tips.append("Target high-impact journals for broader audience reach")
    else:
        tips.append("Consider building on this work before targeting top venues")
        tips.append("Medium-tier conferences can provide valuable feedback")
    
    if domain in ["NLP / Text Mining", "Machine Learning"]:
        tips.append("Pre-prints on ArXiv are common in this field before formal submission")
        tips.append("Open-source code publication can strengthen acceptance chances")
    
    elif domain == "Healthcare / Biomedical":
        tips.append("Ensure proper IRB approval and ethical compliance documentation")
        tips.append("Clinical trials registration may be required for certain studies")
    
    elif domain == "Cybersecurity":
        tips.append("Consider responsible disclosure timelines for sensitive findings")
        tips.append("Industry partnerships can strengthen applied research papers")
    
    tips.append("Prepare supplementary materials including code and datasets")
    tips.append("Ensure clear contributions statement in the introduction")
    
    return tips


#  Citation Impact Analysis 
def analyze_citation_impact(paper: dict) -> dict:
    """
    Analyze citation patterns and estimate impact.
    """
    metadata = paper.get('metadata', {})
    sections = paper.get('sections', {})
    text = paper.get('full_text', '')[:20000]
    
    # Reference count analysis
    ref_count = metadata.get('reference_count', 0)
    if ref_count >= 50:
        ref_level = "Extensive"
        ref_color = "#059669"
    elif ref_count >= 30:
        ref_level = "Comprehensive"
        ref_color = "#2563EB"
    elif ref_count >= 15:
        ref_level = "Moderate"
        ref_color = "#D97706"
    else:
        ref_level = "Limited"
        ref_color = "#DC2626"
    
    # Citation quality indicators
    quality_indicators = {
        'recent_citations': 0,
        'seminal_papers': 0,
        'diversity': 0
    }
    
    # Check for recent references (last 5 years)
    recent_years = re.findall(r'\b(201[9-9]|202[0-5])\b', text[:5000])
    quality_indicators['recent_citations'] = len(recent_years)
    
    # Check for seminal papers (frequently cited works)
    seminal_markers = ['1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', 
                      'le Cun', 'Hinton', 'Bengio', 'Silver', 'Vaswani', 'Devlin', 'Mikolov']
    seminal_count = sum(1 for marker in seminal_markers if marker in text[:10000])
    quality_indicators['seminal_papers'] = seminal_count
    
    # Citation diversity (unique venues mentioned)
    venues = set()
    for sec in ['Related Work', 'Literature Review', 'Introduction']:
        if sec in sections:
            conf_matches = re.findall(r'\b(ICML|NeurIPS|ACL|EMNLP|CVPR|ICCV|AAAI|IJCAI|KDD|SIGMOD|VLDB)\b', 
                                      _section_text(sections[sec]), re.IGNORECASE)
            venues.update(conf_matches)
    quality_indicators['diversity'] = len(venues)
    
    # Impact score calculation
    impact_factors = {
        'reference_count': min(ref_count / 50, 1.0) * 30,
        'recent_citations': min(quality_indicators['recent_citations'] / 10, 1.0) * 25,
        'seminal_papers': min(quality_indicators['seminal_papers'] / 5, 1.0) * 25,
        'diversity': min(quality_indicators['diversity'] / 5, 1.0) * 20
    }
    impact_score = sum(impact_factors.values())
    
    if impact_score >= 80:
        impact_level = "High Impact Potential"
        impact_color = "#059669"
    elif impact_score >= 60:
        impact_level = "Moderate Impact Potential"
        impact_color = "#2563EB"
    elif impact_score >= 40:
        impact_level = "Average Impact Potential"
        impact_color = "#D97706"
    else:
        impact_level = "Limited Impact Potential"
        impact_color = "#DC2626"
    
    return {
        'impact_score': round(impact_score, 1),
        'impact_level': impact_level,
        'impact_color': impact_color,
        'reference_count': ref_count,
        'reference_level': ref_level,
        'reference_color': ref_color,
        'quality_indicators': quality_indicators,
        'analysis': _generate_citation_analysis(quality_indicators, ref_count)
    }


def _generate_citation_analysis(indicators: dict, ref_count: int) -> str:
    """Generate textual analysis of citation patterns."""
    analysis_parts = []
    
    if indicators['recent_citations'] >= 8:
        analysis_parts.append("Strong engagement with current literature")
    elif indicators['recent_citations'] >= 4:
        analysis_parts.append("Moderate recent literature coverage")
    else:
        analysis_parts.append("Limited recent references - consider updating")
    
    if indicators['seminal_papers'] >= 3:
        analysis_parts.append("Good foundation with seminal works")
    else:
        analysis_parts.append("Could benefit from more foundational citations")
    
    if indicators['diversity'] >= 4:
        analysis_parts.append("Diverse citation sources across venues")
    else:
        analysis_parts.append("Consider citing broader range of sources")
    
    return "; ".join(analysis_parts)


#  Future Research Directions 
def suggest_future_directions(paper: dict) -> dict:
    """
    Suggest future research directions based on paper analysis.
    """
    gaps = paper.get('research_gaps', [])
    limitations = paper.get('limitations', [])
    trends = paper.get('trends', [])
    metadata = paper.get('metadata', {})
    domain = metadata.get('domain', 'General CS')
    
    directions = []
    
    # 1. Based on identified research gaps
    for gap in gaps[:2]:
        if gap:
            directions.append({
                'category': 'Research Gap',
                'direction': f"Address: {gap[:100]}...",
                'priority': 'High'
            })
    
    # 2. Based on limitations
    for lim in limitations[:2]:
        if lim:
            directions.append({
                'category': 'Limitation Extension',
                'direction': f"Overcome: {lim[:100]}...",
                'priority': 'High'
            })
    
    # 3. Domain-specific future directions
    domain_directions = _get_domain_directions(domain, trends)
    for d in domain_directions[:3]:
        directions.append(d)
    
    # 4. General future suggestions
    directions.extend([
        {
            'category': 'General',
            'direction': "Apply the methodology to new domains or datasets",
            'priority': 'Medium'
        },
        {
            'category': 'General', 
            'direction': "Improve computational efficiency for real-world deployment",
            'priority': 'Medium'
        },
        {
            'category': 'General',
            'direction': "Conduct longitudinal studies to validate long-term effectiveness",
            'priority': 'Low'
        }
    ])
    
    return {
        'directions': directions[:8],
        'domain': domain,
        'trend_based': [t['trend'] for t in trends[:3]]
    }


def _get_domain_directions(domain: str, trends: list) -> list[dict]:
    """Get domain-specific future research directions."""
    
    domain_future = {
        "NLP / Text Mining": [
            "Explore few-shot and zero-shot learning improvements",
            "Investigate multilingual and cross-lingual transfer",
            "Develop better evaluation metrics for generation tasks"
        ],
        "Machine Learning": [
            "Focus on interpretability and explainability",
            "Improve sample efficiency in deep learning",
            "Explore self-supervised and unsupervised learning"
        ],
        "Computer Vision": [
            "Advance video understanding and temporal modeling",
            "Improve robustness to adversarial attacks",
            "Explore 3D scene understanding and reconstruction"
        ],
        "Healthcare / Biomedical": [
            "Ensure fairness and reduce bias in clinical applications",
            "Integrate multi-modal data (imaging, EHR, genomics)",
            "Focus on privacy-preserving machine learning"
        ],
        "Cybersecurity": [
            "Develop robust defenses against emerging threats",
            "Explore automated vulnerability detection",
            "Improve threat intelligence and prediction"
        ],
        "Data Science / Analytics": [
            "Scale methods for massive datasets",
            "Improve interpretability of complex models",
            "Focus on real-time analytics and streaming"
        ],
        "IoT / Embedded Systems": [
            "Optimize for edge deployment and low power",
            "Improve security in resource-constrained devices",
            "Explore federated learning for IoT"
        ],
        "Cloud / Distributed": [
            "Reduce latency in distributed systems",
            "Improve resource allocation and scheduling",
            "Enhance fault tolerance and reliability"
        ],
        "Robotics / Control": [
            "Improve real-world robot learning",
            "Enhance human-robot interaction",
            "Develop safer autonomous systems"
        ],
        "Renewable Energy": [
            "Optimize energy storage and grid integration",
            "Improve forecasting for renewable sources",
            "Develop smart grid technologies"
        ]
    }
    
    directions = domain_future.get(domain, [
        "Explore novel applications of the proposed method",
        "Investigate theoretical foundations",
        "Compare with recent state-of-the-art approaches"
    ])
    
    return [
        {'category': 'Domain Trend', 'direction': d, 'priority': 'Medium'}
        for d in directions
    ]


#  Topic Trend Analysis 
def analyze_topic_trends(papers: list) -> dict:
    """
    Analyze topic trends across multiple papers.
    Returns trend analysis over time.
    """
    if not papers:
        return {'trends': [], 'summary': 'No papers to analyze'}
    
    # Collect all trends and domains
    all_trends = {}
    domain_counts = {}
    year_distribution = {}
    
    for paper in papers:
        # Domain distribution
        domain = paper.get('metadata', {}).get('domain', 'Unknown')
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Year distribution
        year = str(paper.get('metadata', {}).get('year', 'Unknown'))
        year_distribution[year] = year_distribution.get(year, 0) + 1
        
        # Trend analysis
        for trend in paper.get('trends', []):
            trend_name = trend.get('trend', 'Unknown')
            all_trends[trend_name] = all_trends.get(trend_name, 0) + trend.get('count', 1)
    
    # Sort trends by frequency
    sorted_trends = sorted(all_trends.items(), key=lambda x: x[1], reverse=True)
    
    # Identify emerging trends (keywords)
    emerging_keywords = [
        'large language model', 'llm', 'gpt', 'transformer', 'diffusion',
        'federated', 'explainable', 'multimodal', 'few-shot', 'zero-shot'
    ]
    
    emerging = []
    for trend, count in sorted_trends:
        if any(kw in trend.lower() for kw in emerging_keywords):
            emerging.append({'trend': trend, 'count': count})
    
    return {
        'total_papers': len(papers),
        'domain_distribution': dict(sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)),
        'year_distribution': dict(sorted(year_distribution.items())),
        'top_trends': [{'trend': t, 'count': c} for t, c in sorted_trends[:10]],
        'emerging_trends': emerging[:5],
        'summary': _generate_trend_summary(sorted_trends, domain_counts)
    }


def _generate_trend_summary(trends: list, domains: dict) -> str:
    """Generate a textual summary of trends."""
    parts = []
    
    if trends:
        top = trends[0]
        parts.append(f"Leading research area: {top[0]} ({top[1]} mentions)")
    
    if domains:
        top_domain = max(domains.items(), key=lambda x: x[1])
        parts.append(f"Most common domain: {top_domain[0]} ({top_domain[1]} papers)")
    
    if len(trends) >= 3:
        parts.append(f"Research is diversifying into {len(trends)} distinct topics")
    
    return ". ".join(parts) if parts else "Limited trend data available"


#  Semantic Search 
def semantic_search(papers: list, query: str, top_k: int = 5) -> list[dict]:
    """
    Perform semantic search across papers based on query.
    Uses keyword matching + domain filtering + relevance scoring.
    """
    if not papers or not query:
        return []
    
    query_lower = query.lower()
    query_words = set(re.findall(r'\b\w{3,}\b', query_lower))
    
    results = []
    
    for paper in papers:
        score = 0
        reasons = []
        
        # 1. Title match
        title = paper.get('metadata', {}).get('title', '').lower()
        title_matches = sum(1 for w in query_words if w in title)
        if title_matches > 0:
            score += title_matches * 10
            reasons.append(f"Title match ({title_matches})")
        
        # 2. Keyword match
        paper_kws = set(k['word'].lower() for k in paper.get('keywords', [])[:20])
        kw_overlap = len(query_words & paper_kws)
        if kw_overlap > 0:
            score += kw_overlap * 5
            reasons.append(f"Keyword overlap ({kw_overlap})")
        
        # 3. Domain match
        domain = paper.get('metadata', {}).get('domain', '').lower()
        if any(w in domain for w in query_words if len(w) > 4):
            score += 15
            reasons.append("Domain match")
        
        # 4. Section content match
        sections = paper.get('sections', {})
        content_matches = 0
        for sec_name, sec_content in sections.items():
            if sec_name.lower() not in ['references', 'appendix']:
                sec_lower = _section_text(sec_content).lower()[:5000]
                matches = sum(1 for w in query_words if w in sec_lower)
                content_matches += matches
        
        if content_matches > 0:
            score += min(content_matches * 2, 30)
            reasons.append(f"Content matches ({content_matches})")
        
        # 5. Model/method match
        models = set(m.lower() for m in paper.get('models_methods', []))
        model_overlap = len(query_words & models)
        if model_overlap > 0:
            score += model_overlap * 8
            reasons.append(f"Method match ({model_overlap})")
        
        # 6. Quality bonus
        quality = paper.get('quality_score', {}).get('overall_score', 50)
        score += quality * 0.1  # 10% quality boost
        
        if score > 0:
            results.append({
                'paper': paper,
                'score': round(score, 2),
                'reasons': reasons,
                'title': paper.get('metadata', {}).get('title', 'Untitled')[:80],
                'domain': paper.get('metadata', {}).get('domain', 'Unknown')
            })
    
    # Sort by score and return top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]


#  Project Ideas Generation 
def generate_project_ideas(paper: dict) -> dict:
    """
    Convert research paper insights into practical project ideas.
    """
    metadata = paper.get('metadata', {})
    domain = metadata.get('domain', 'General CS')
    research_type = metadata.get('research_type', 'Empirical Study')
    models = paper.get('models_methods', [])
    keywords = paper.get('keywords', [])[:10]
    limitations = paper.get('limitations', [])[:3]
    gaps = paper.get('research_gaps', [])[:2]
    
    project_ideas = []
    
    # 1. Core Implementation Project
    project_ideas.append({
        'title': f"Implementation of {domain} System",
        'description': f"Build a practical system based on the paper's methodology. "
                      f"Focus on implementing the core algorithms using {', '.join(models[:3]) if models else 'standard approaches'}.",
        'difficulty': 'Intermediate',
        'timeline': '3-4 months',
        'skills_needed': ['Programming', 'Algorithm Design', domain]
    })
    
    # 2. Application Project
    project_ideas.append({
        'title': f"Apply {domain} to New Domain",
        'description': f"Adapt the paper's approach to a different application area. "
                      f"Consider domains like healthcare, finance, or education.",
        'difficulty': 'Intermediate to Advanced',
        'timeline': '4-6 months',
        'skills_needed': ['Domain Knowledge', 'Data Processing', 'ML/DL']
    })
    
    # 3. Enhancement Project
    enhancement_kw = keywords[0].get('word', 'method') if keywords else 'method'
    project_ideas.append({
        'title': f"Improve {enhancement_kw.title()} Performance",
        'description': f"Address limitations by improving accuracy, speed, or efficiency. "
                      f"Focus on scalability for real-world deployment.",
        'difficulty': 'Advanced',
        'timeline': '5-6 months',
        'skills_needed': ['Optimization', 'System Design', 'Performance Tuning']
    })
    
    # 4. Comparative Study
    project_ideas.append({
        'title': 'Comparative Analysis with State-of-Art',
        'description': f"Compare the paper's approach with current SOTA methods. "
                      f"Identify strengths and weaknesses across different metrics.",
        'difficulty': 'Intermediate',
        'timeline': '2-3 months',
        'skills_needed': ['Research Skills', 'Benchmarking', 'Data Analysis']
    })
    
    # 5. Extension Project based on gaps
    if gaps:
        gap = gaps[0]
        project_ideas.append({
            'title': 'Research Gap Exploration',
            'description': f"Tackle the identified gap: {gap[:80]}...",
            'difficulty': 'Advanced',
            'timeline': '6+ months',
            'skills_needed': ['Research', 'Innovation', domain]
        })
    
    # 6. Tool/Library Development
    project_ideas.append({
        'title': 'Open Source Tool Development',
        'description': f"Create a reusable library or tool based on the paper's methods. "
                      f"Contribute to the open-source community.",
        'difficulty': 'Intermediate',
        'timeline': '3-5 months',
        'skills_needed': ['Software Engineering', 'Documentation', 'Testing']
    })
    
    return {
        'project_ideas': project_ideas[:6],
        'paper_domain': domain,
        'paper_type': research_type,
        'detected_technologies': models[:8],
        'top_keywords': [k['word'] for k in keywords[:8]],
        'implementation_tips': _get_implementation_tips(domain, models)
    }


def _get_implementation_tips(domain: str, models: list) -> list[str]:
    """Get implementation tips based on domain and models."""
    tips = []
    
    tips.append("Start with the paper's baseline implementation before optimizing")
    tips.append("Use the same datasets for fair comparison, then try new datasets")
    
    if any(m.lower() in ['tensorflow', 'pytorch', 'keras'] for m in models):
        tips.append("Deep learning framework experience recommended")
        tips.append("GPU access will be beneficial for training")
    
    if domain == "Healthcare / Biomedical":
        tips.append("Ensure compliance with health data regulations (HIPAA, GDPR)")
        tips.append("Consider ethical implications of healthcare applications")
    
    if domain == "Cybersecurity":
        tips.append("Follow responsible disclosure practices")
        tips.append("Test thoroughly in controlled environments before deployment")
    
    tips.append("Join relevant communities (GitHub, Discord, forums) for support")
    tips.append("Consider publishing your implementation as open source")
    
    return tips

