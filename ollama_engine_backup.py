"""
Ollama AI Engine for PaperIQ Pro.
Calls local Ollama server (http://localhost:11434).
Falls back to extractive summarization if Ollama is unavailable.
"""
import re
import json
import heapq
import requests
from collections import Counter

OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_CHAT = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2"


def _section_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("content", ""))
    return ""


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "been", "were", "will",
    "their", "which", "also", "into", "about", "paper", "study", "using", "used", "based",
    "section", "results", "method", "methods", "analysis", "system", "data", "model",
    "what", "how", "when", "where", "who", "why", "does", "did", "are", "is", "can",
}


INTENT_SECTION_HINTS = {
    "method": {"Methodology", "Methods", "Proposed Method", "Implementation", "System Design", "Architecture"},
    "approach": {"Methodology", "Methods", "Proposed Method", "Implementation"},
    "result": {"Results", "Results & Discussion", "Experiments & Results", "Evaluation", "Discussion"},
    "finding": {"Results", "Results & Discussion", "Discussion", "Conclusion"},
    "conclusion": {"Conclusion", "Future Work", "Discussion"},
    "limitation": {"Limitations", "Conclusion", "Discussion"},
    "advantage": {"Advantages", "Results", "Conclusion"},
    "future": {"Future Work", "Conclusion", "Discussion"},
    "background": {"Abstract", "Introduction", "Background", "Literature Review", "Related Work"},
    "reference": {"References"},
}


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in STOPWORDS]


def _query_terms(query: str) -> list[str]:
    return _tokenize(query)


def _select_relevant_sections(query: str, paper_data: dict, max_sections: int = 4) -> list[tuple[str, str, float]]:
    sections = paper_data.get("sections", {}) or {}
    terms = set(_query_terms(query))
    if not sections:
        return []

    scored: list[tuple[str, str, float]] = []
    for name, raw in sections.items():
        content = _section_text(raw)
        if not content:
            continue
        snippet = content[:5000]
        tokens = _tokenize(snippet)
        tset = set(tokens)
        overlap = len(terms & tset)
        coverage = overlap / max(len(terms), 1)
        score = overlap * 2.5 + coverage

        lname = name.lower()
        for intent, preferred in INTENT_SECTION_HINTS.items():
            if intent in query.lower() and name in preferred:
                score += 3.0
            if intent in query.lower() and any(p.lower() in lname for p in preferred):
                score += 1.5

        if any(t in lname for t in terms):
            score += 1.0

        score += min(len(snippet.split()) / 1200, 1.0)
        scored.append((name, snippet, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    top = scored[:max_sections]
    if not top:
        fallback = []
        for sec in ["Abstract", "Introduction", "Methodology", "Results", "Conclusion"]:
            if sec in sections:
                fallback.append((sec, _section_text(sections[sec])[:5000], 0.0))
        return fallback[:max_sections]
    return top


def _extractive_query_answer(query: str, section_rows: list[tuple[str, str, float]], max_points: int = 4) -> str:
    terms = set(_query_terms(query))
    candidates: list[tuple[float, str, str]] = []
    for sec_name, content, base_score in section_rows:
        sentences = re.split(r'(?<=[.!?])\s+', content.replace("\n", " "))
        for idx, sent in enumerate(sentences[:120]):
            s = sent.strip()
            if len(s) < 24 or len(s) > 260:
                continue
            stoks = set(_tokenize(s))
            overlap = len(terms & stoks)
            score = base_score + overlap * 2.2
            if overlap == 0 and terms:
                continue
            if idx < 8:
                score += 0.25
            candidates.append((score, sec_name, s))

    if not candidates:
        summary_lines = []
        for sec_name, content, _ in section_rows[:3]:
            compact = re.sub(r"\s+", " ", content).strip()
            if compact:
                summary_lines.append(f"- {compact[:180].rstrip()}... (Section: {sec_name})")
        if summary_lines:
            return "Answer (offline analysis mode):\n" + "\n".join(summary_lines)
        return "I could not find enough evidence in the paper for that question."

    candidates.sort(key=lambda x: x[0], reverse=True)
    chosen = []
    seen = set()
    for _, sec_name, sentence in candidates:
        key = re.sub(r"[^a-z0-9]+", "", sentence.lower())[:120]
        if key in seen:
            continue
        chosen.append((sec_name, sentence))
        seen.add(key)
        if len(chosen) >= max_points:
            break

    lines = [f"- {s} (Section: {sec})" for sec, s in chosen]
    return "Answer (offline analysis mode):\n" + "\n".join(lines)


def _top_terms(text: str, n: int = 8) -> list[str]:
    tokens = _tokenize(text)
    if not tokens:
        return []
    freq = Counter(tokens)
    return [w for w, _ in freq.most_common(n)]


def _clean_title(title: str) -> str:
    """Clean title by removing metadata like ISSN, IC Value, etc."""
    if not title:
        return "Untitled"
    # Remove common metadata artifacts
    title = re.sub(r'ISSN:?\s*[\d-]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'IC Value:?\s*[\d.]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'SJ Impact Factor:?\s*[\d.]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'doi:?\s*[\d/.-]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'Vol\.?\s*\d+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'IJ[A-Z]+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()
    # Remove leading separators
    title = re.sub(r'^[\s\-:;|]+', '', title)
    return title if title else "Untitled"


def _digest_for_compare(paper: dict) -> str:
    """Create a compact digest for paper comparison."""
    meta = paper.get("metadata", {})
    title = _clean_title(meta.get('title', 'Untitled'))[:80]
    authors = meta.get('authors', 'Unknown')[:60]
    domain = meta.get('domain', 'Unknown')
    year = meta.get('year', 'N/A')
    refs = meta.get('reference_count', 0)
    
    # Get key sections (truncated)
    sections = paper.get("sections", {}) or {}
    abstract = ""
    if "Abstract" in sections:
        abstract = re.sub(r"\s+", " ", _section_text(sections["Abstract"])).strip()[:300]
    
    method = ""
    if "Methodology" in sections:
        method = re.sub(r"\s+", " ", _section_text(sections["Methodology"])).strip()[:250]
    
    results = ""
    for sec in ["Results", "Results & Discussion"]:
        if sec in sections:
            results = re.sub(r"\s+", " ", _section_text(sections[sec])).strip()[:250]
            break
    
    conclusion = ""
    if "Conclusion" in sections:
        conclusion = re.sub(r"\s+", " ", _section_text(sections["Conclusion"])).strip()[:200]
    
    # Tools/models
    mods = paper.get("models_methods", []) or paper.get("models", [])
    tools = ", ".join(mods[:5]) if mods else "None"
    
    # Limitations and Advantages
    lims = paper.get("limitations", []) or []
    advs = paper.get("advantages", []) or []
    
    return f"""Title: {title}
Authors: {authors}
Domain: {domain} | Year: {year} | References: {refs}
Tools/Models: {tools}
Abstract: {abstract}
Methodology: {method}
Results: {results}
Conclusion: {conclusion}
Advantages: {'; '.join(advs[:3]) if advs else 'None'}
Limitations: {'; '.join(lims[:3]) if lims else 'None'}"""


def _extract_software_tools(paper: dict) -> list:
    mods = paper.get("models_methods", []) or paper.get("models", [])
    return mods[:10] if mods else []


def _extract_cost_info(paper: dict) -> list:
    text = paper.get("text", "")
    cost_keywords = ["cost", "price", "$", "expense", "budget", "fee", "charge", "pricing", "usd", "dollar"]
    cost_info = []
    for kw in cost_keywords:
        if kw.lower() in text.lower():
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sent in sentences:
                if kw.lower() in sent.lower() and 30 < len(sent) < 200:
                    cost_info.append(sent.strip()[:180])
                    break
            if len(cost_info) >= 2:
                break
    return cost_info


def _extract_abstract_summary(paper: dict) -> str:
    """Extract and summarize abstract - clean version."""
    sections = paper.get("sections", {}) or {}
    abstract = _section_text(sections.get("Abstract", ""))
    if abstract:
        sentences = re.split(r'(?<=[.!?])\s+', abstract)
        # Filter out metadata, URLs, and very short lines
        key_sents = []
        for s in sentences:
            s = s.strip()
            # Skip if starts with metadata indicators or URLs
            if s.startswith(('http', 'www', 'ISSN', 'doi', 'Volum', 'IC ', 'SJ ')):
                continue
            if len(s) > 40:
                key_sents.append(s)
        if key_sents:
            return ". ".join(key_sents[:2]) + "."
    return "Not available"


def _deterministic_compare(p1: dict, p2: dict) -> str:
    """Generate a clean, concise side-by-side comparison."""
    m1, m2 = p1.get("metadata", {}), p2.get("metadata", {})
    s1 = p1.get("sections", {}) or {}
    s2 = p2.get("sections", {}) or {}

    # Clean titles
    title1 = _clean_title(m1.get('title', 'Untitled'))[:60]
    title2 = _clean_title(m2.get('title', 'Untitled'))[:60]
    domain1 = m1.get('domain', 'Unknown')
    domain2 = m2.get('domain', 'Unknown')
    year1 = m1.get('year', 'N/A')
    year2 = m2.get('year', 'N/A')
    ref1 = m1.get('reference_count', 0)
    ref2 = m2.get('reference_count', 0)
    
    # Get abstract summaries
    abstract1 = _extract_abstract_summary(p1)
    abstract2 = _extract_abstract_summary(p2)
    
    # Get methodology
    method1 = _section_text(s1.get("Methodology", s1.get("Methods", "")))[:180]
    method2 = _section_text(s2.get("Methodology", s2.get("Methods", "")))[:180]
    
    # Get results
    results1 = _section_text(s1.get("Results", s1.get("Results & Discussion", "")))[:180]
    results2 = _section_text(s2.get("Results", s2.get("Results & Discussion", "")))[:180]
    
    # Get conclusions
    concl1 = _section_text(s1.get("Conclusion", ""))[:150]
    concl2 = _section_text(s2.get("Conclusion", ""))[:150]
    
    # Get limitations and advantages - clean them
    lim1 = (p1.get("limitations", []) or [])[:3]
    lim2 = (p2.get("limitations", []) or [])[:3]
    adv1 = (p1.get("advantages", []) or [])[:3]
    adv2 = (p2.get("advantages", []) or [])[:3]
    
    # Get tools
    mods1 = _extract_software_tools(p1)
    mods2 = _extract_software_tools(p2)

    out = []
    out.append("## Paper Comparison")
    out.append("")
    
    # Paper Details
    out.append("**Paper 1:**")
    out.append(f"- Title: {title1}")
    out.append(f"- Domain: {domain1} | Year: {year1} | References: {ref1}")
    out.append("")
    out.append("**Paper 2:**")
    out.append(f"- Title: {title2}")
    out.append(f"- Domain: {domain2} | Year: {year2} | References: {ref2}")
    out.append("")
    
    # Abstract Comparison
    out.append("### Abstract")
    out.append(f"**Paper 1:** {abstract1}")
    out.append(f"**Paper 2:** {abstract2}")
    out.append("")
    
    # Methodology Comparison
    out.append("### Methodology")
    out.append(f"**Paper 1:** {method1 if method1 else 'Not available'}")
    out.append(f"**Paper 2:** {method2 if method2 else 'Not available'}")
    out.append("")
    
    # Results Comparison
    out.append("### Results")
    out.append(f"**Paper 1:** {results1 if results1 else 'Not available'}")
    out.append(f"**Paper 2:** {results2 if results2 else 'Not available'}")
    out.append("")
    
    # Conclusion Comparison
    out.append("### Conclusion")
    out.append(f"**Paper 1:** {concl1 if concl1 else 'Not available'}")
    out.append(f"**Paper 2:** {concl2 if concl2 else 'Not available'}")
    out.append("")
    
    # Tools Comparison
    out.append("### Tools & Models")
    tools1 = ", ".join(mods1) if mods1 else "None detected"
    tools2 = ", ".join(mods2) if mods2 else "None detected"
    out.append(f"**Paper 1:** {tools1}")
    out.append(f"**Paper 2:** {tools2}")
    out.append("")
    
    # Advantages
    out.append("### Advantages")
    if adv1:
        for a in adv1:
            out.append(f"- Paper 1: {a}")
    else:
        out.append("- Paper 1: None detected")
    
    if adv2:
        for a in adv2:
            out.append(f"- Paper 2: {a}")
    else:
        out.append("- Paper 2: None detected")
    out.append("")
    
    # Limitations
    out.append("### Limitations")
    if lim1:
        for l in lim1:
            out.append(f"- Paper 1: {l}")
    else:
        out.append("- Paper 1: None detected")
    
    if lim2:
        for l in lim2:
            out.append(f"- Paper 2: {l}")
    else:
        out.append("- Paper 2: None detected")
    
    return "\n".join(out)


def _available_models() -> list[str]:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except:
        pass
    return []


def is_ollama_running() -> bool:
    try:
        r = requests.get("http://localhost:11434/", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_best_model() -> str:
    models = _available_models()
    if not models:
        return DEFAULT_MODEL
    prefer = ["llama3.2","llama3","llama3.1","mistral","phi3","gemma","phi",
              "llama2","mixtral","codellama","neural-chat"]
    for pref in prefer:
        for m in models:
            if pref in m.lower():
                return m
    return models[0]


def _ollama_call(prompt: str, system: str = "", model: str = None,
                 max_tokens: int = 500, timeout_s: int = 25) -> str:
    if model is None:
        model = get_best_model()
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.2, "top_p": 0.9},
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        return None


_SECTION_SYSTEM = """You are a precise academic research assistant.
Summarize the given paper section into 3-5 concise bullet points.
Rules:
- Start each bullet with "- "
- Each bullet = one complete, standalone sentence (max 35 words)
- Focus on the most important claim, finding, or method
- Never copy text verbatim; always paraphrase clearly
- No headings, no preamble, just the bullets"""

def summarize_section(section_name: str, content: str, model: str = None) -> str:
    if not content or len(content.split()) < 20:
        return "- " + content.strip() if content.strip() else ""
    truncated = content[:3500]
    prompt    = f"Section: {section_name}\n\nContent:\n{truncated}\n\nProvide bullet-point summary:"
    result    = _ollama_call(prompt, _SECTION_SYSTEM, model, max_tokens=350)
    if result is None:
        return _extractive(content, n=4)
    return result


_OVERALL_SYSTEM = """You are an expert academic research summarizer.
Given a research paper, produce a structured summary with EXACTLY these four sections:

 Objective
Write 1-2 sentences on what the paper aims to achieve.

 Methodology  
Write 2-3 sentences on the approach, techniques, and tools used.

 Key Findings
List 3 bullet points (use "- " prefix) with the most important results or contributions.

 Significance
Write 1-2 sentences on why this research matters or what it advances.

Be concise. Plain academic language. No filler."""

def summarize_paper(full_text: str, model: str = None) -> str:
    truncated = full_text[:5500]
    result    = _ollama_call(truncated, _OVERALL_SYSTEM, model, max_tokens=550)
    if result is None:
        return _extractive(full_text, n=6)
    return result


_LIMITS_SYSTEM = """You are an expert academic reviewer.
Given a research paper excerpt, extract LIMITATIONS and ADVANTAGES.

Output format:
LIMITATIONS:
 [limitation 1]
 [limitation 2]
 [limitation 3]

ADVANTAGES:
 [advantage 1]
 [advantage 2]
 [advantage 3]

Rules:
- Each point is one clear sentence (max 30 words)
- Base ONLY on what is stated or implied in the paper
- For limitations: focus on scope, data, generalizability, compute requirements
- For advantages: focus on novelty, accuracy gains, efficiency, contributions
- No preamble, just the structured output"""

def extract_limits_advantages_ai(full_text: str, model: str = None) -> dict:
    truncated = full_text[:5000]
    result = _ollama_call(truncated, _LIMITS_SYSTEM, model, max_tokens=450)
    if result is None:
        return None

    limitations = []
    advantages  = []
    mode = None
    for line in result.split('\n'):
        l = line.strip()
        if 'LIMITATION' in l.upper():
            mode = 'lim'
        elif 'ADVANTAGE' in l.upper():
            mode = 'adv'
        elif l.startswith('-') or l.startswith('*') or re.match(r'^\d+[.)]\s+', l):
            point = re.sub(r'^[-*\d.)\s]+', '', l).strip()
            if point:
                if mode == 'lim':
                    limitations.append(point)
                elif mode == 'adv':
                    advantages.append(point)

    return {"limitations": limitations[:6], "advantages": advantages[:6]}


def answer_question(question: str, paper_data: dict, model: str = None) -> str:
    question = (question or "").strip()
    if not question:
        return "Please ask a specific question about the paper."

    relevant_sections = _select_relevant_sections(question, paper_data, max_sections=4)
    context_blocks = []
    for sec_name, sec_content, _ in relevant_sections:
        context_blocks.append(f"[{sec_name}]\n{sec_content[:1400]}")
    context_text = "\n\n".join(context_blocks)[:5600]

    system = """You are PaperIQ Pro, an intelligent research paper assistant.
Answer only from the supplied paper context.
Output format:
1) Direct Answer (2-4 lines)
2) Evidence (3-5 bullets) and each bullet must end with (Section: <name>)
3) If evidence is weak, clearly state uncertainty.
Do not invent facts."""

    title = paper_data.get("metadata", {}).get("title", "Untitled")
    prompt = (
        f"Paper Title: {title}\n\n"
        f"Relevant Context:\n{context_text}\n\n"
        f"User Question: {question}\n\n"
        "Provide the answer in the required format."
    )

    if not is_ollama_running():
        return _fallback_qa(question, paper_data, relevant_sections=relevant_sections)

    result = _ollama_call(prompt, system, model, max_tokens=420, timeout_s=20)
    if result is None or len(result.strip()) < 20:
        return _fallback_qa(question, paper_data, relevant_sections=relevant_sections)

    if "Section:" not in result:
        evidence = _extractive_query_answer(question, relevant_sections, max_points=3)
        return f"{result}\n\nEvidence:\n{evidence}"
    return result


_COMPARE_SYSTEM = """You are an expert research analyst. Compare two research papers professionally.

RULES:
- Be factual and accurate
- Focus on meaningful differences
- Use clear, simple language
- No raw data dumps

OUTPUT:

**Paper 1:** [title]
**Paper 2:** [title]

**Key Difference in Objective:**
- Paper 1: [what it aims to do]
- Paper 2: [what it aims to do]

**Methodology Differences:**
- Paper 1: [approach/method]
- Paper 2: [approach/method]

**Notable Results:**
- Paper 1: [key findings]
- Paper 2: [key findings]

**Advantages:**
- Paper 1: [strengths]
- Paper 2: [strengths]

**Limitations:**
- Paper 1: [weaknesses]
- Paper 2: [weaknesses]

**Verdict:** [Which is better and why in 1-2 sentences]"""

def compare_papers(p1: dict, p2: dict, model: str = None) -> str:
    """Compare two papers and return a clean, summarized output."""
    base = _deterministic_compare(p1, p2)
    if not is_ollama_running():
        return base

    prompt = (
        f"PAPER 1:\n{_digest_for_compare(p1)}\n\n"
        f"PAPER 2:\n{_digest_for_compare(p2)}\n\n"
        "Provide a concise AI-powered comparison following the format."
    )
    result = _ollama_call(prompt, _COMPARE_SYSTEM, model, max_tokens=400, timeout_s=18)
    if result is None or len(result.strip()) < 40:
        return base
    
    # Clean up the AI result - remove any raw data artifacts
    result = re.sub(r'Paper \d+: \+ .+', '', result)
    result = re.sub(r'Paper \d+: - .+', '', result)
    result = re.sub(r'\.{2,}', '.', result)
    result = result.strip()
    
    return result


def _extractive(text: str, n: int = 5) -> str:
    sents = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    sents = [s.strip() for s in sents if 25 < len(s) < 280]
    if len(sents) <= n:
        return '\n'.join(f'- {s}' for s in sents)
    stop = {"with","that","this","from","have","been","will","they","were","their",
            "which","also","into","about","paper","study","using","method","based",
            "shown","these","those","between","when","both","more","most"}
    freq = Counter(w for w in re.findall(r'\b[a-z]{4,}\b', text.lower()) if w not in stop)
    tot  = max(1, sum(freq.values()))
    freq = {w: c/tot for w,c in freq.items()}
    scores = [sum(freq.get(w,0) for w in re.findall(r'\b[a-z]+\b',s.lower()))
              / max(1, len(s.split())) for s in sents]
    top = sorted(heapq.nlargest(n, range(len(scores)), key=lambda i: scores[i]))
    return '\n'.join(f'- {sents[i]}' for i in top)


def _with_section_citations(bullets_text: str, section_name: str) -> str:
    lines = []
    for ln in (bullets_text or "").splitlines():
        line = ln.strip()
        if not line:
            continue
        clean = re.sub(r"^[-*]\s*", "", line)
        lines.append(f"- {clean} (Section: {section_name})")
    return "\n".join(lines)


def _fallback_qa(q: str, data: dict, relevant_sections: list[tuple[str, str, float]] | None = None) -> str:
    ql = q.lower()
    s  = data.get("sections", {}) or {}
    m  = data.get("metadata", {})
    
    # Handle numeric/specific queries (percentages, accuracy, numbers)
    numeric_keywords = ["how much", "how many", "percentage", "percent", "accuracy", "precision", "recall", "f1", "score", "rate", "number of", "dataset size", "training data", "images", "samples", "effective"]
    is_numeric_query = any(kw in ql for kw in numeric_keywords)
    
    if is_numeric_query:
        # Search specifically in Results sections for numeric answers
        results_sections = ["Results", "Results & Discussion", "Experiments", "Experiments & Results", "Evaluation", "Discussion", "Methodology"]
        numeric_findings = []
        
        for sec_name in results_sections:
            if sec_name in s:
                content = _section_text(s[sec_name])
                # Look for sentences with numbers/percentages
                sentences = re.split(r'(?<=[.!?])\s+', content.replace('\n', ' '))
                for sent in sentences:
                    sent = sent.strip()
                    if len(sent) < 30 or len(sent) > 300:
                        continue
                    # Check if sentence contains numbers or percentages
                    if re.search(r'\d+\.?\d*', sent):
                        # Score by relevance to query keywords
                        score = 0
                        if any(kw in sent.lower() for kw in ['accuracy', 'precision', 'recall', 'f1', 'score', 'percent', '%']):
                            score += 5
                        if any(kw in ql for kw in ['accuracy', 'precision', 'recall', 'f1', 'performance', 'effective']):
                            if any(kw in sent.lower() for kw in ['accuracy', 'precision', 'recall', 'f1', 'performance', 'effective']):
                                score += 3
                        if any(kw in ql for kw in ['train', 'dataset', 'image', 'sample', 'data']):
                            if any(kw in sent.lower() for kw in ['train', 'dataset', 'image', 'sample', 'data']):
                                score += 3
                        if score > 0:
                            numeric_findings.append((score, sec_name, sent))
        
        # Sort by score and return top results
        numeric_findings.sort(key=lambda x: x[0], reverse=True)
        if numeric_findings:
            result_lines = []
            for _, sec, sent in numeric_findings[:5]:
                result_lines.append(f"- {sent} (Section: {sec})")
            return "**Numeric Findings from Paper:**\n" + "\n".join(result_lines)
    
    # Basic metadata questions
    if any(w in ql for w in ["title","name","called","about this paper"]):
        return f"**Title:** {m.get('title', 'Not available')}"
    if any(w in ql for w in ["author","who wrote","written by","authors"]):
        return f"**Authors:** {m.get('authors', 'Not available')}"
    if any(w in ql for w in ["year","published","when","date"]):
        return f"**Year:** {m.get('year', 'Not available')}"
    if any(w in ql for w in ["domain","field","area","topic","category"]):
        return f"**Domain:** {m.get('domain', 'Not available')}"
    if any(w in ql for w in ["type","kind","research type"]):
        return f"**Research Type:** {m.get('research_type', 'Not available')}"
    if any(w in ql for w in ["reference","citation","bibliography"]):
        return f"**References:** {m.get('reference_count', 0)}"
    if any(w in ql for w in ["word","length","size"]):
        return f"**Word Count:** {m.get('word_count', 0):,}"
    if any(w in ql for w in ["method","approach","how"]):
        c = _section_text(s.get("Methodology")) or _section_text(s.get("Methods"))
        if not c:
            return "Methodology section not found."
        return "Methodology insights:\n" + _with_section_citations(_extractive(c, 4), "Methodology")
    if any(w in ql for w in ["result","finding","outcome","performance"]):
        c = _section_text(s.get("Results")) or _section_text(s.get("Results & Discussion")) or _section_text(s.get("Experiments & Results"))
        if not c:
            return "Results section not found."
        return "Results insights:\n" + _with_section_citations(_extractive(c, 4), "Results")
    if any(w in ql for w in ["conclusion","conclude","summary"]):
        c = _section_text(s.get("Conclusion"))
        if not c:
            return "Conclusion section not found."
        return "Conclusion insights:\n" + _with_section_citations(_extractive(c, 3), "Conclusion")
    if any(w in ql for w in ["limitation","weakness","drawback"]):
        lims = data.get("limitations", [])
        return ("**Limitations detected:**\n" + "\n".join(f" {l}" for l in lims)
                if lims else "No explicit limitations section found.")
    if any(w in ql for w in ["advantage","contribution","strength","novelty"]):
        advs = data.get("advantages", [])
        return ("**Advantages/Contributions:**\n" + "\n".join(f" {a}" for a in advs)
                if advs else "No explicit advantages section found.")
    if any(w in ql for w in ["model","tool","algorithm","framework","library"]):
        mods = data.get("models_methods", []) or data.get("models", [])
        return "**Detected models/tools:** " + ", ".join(mods) if mods else "None detected."
    
    # Dataset information
    if any(w in ql for w in ["dataset","data","training","test","image","sample","size"]):
        for sec_name in ["Methodology", "Experiments", "Experiments & Results", "Results", "Datasets"]:
            if sec_name in s:
                c = _section_text(s[sec_name])
                sentences = re.split(r'(?<=[.!?])\s+', c.replace('\n', ' '))
                dataset_sents = []
                for sent in sentences:
                    if any(kw in sent.lower() for kw in ['dataset', 'data', 'training', 'test', 'image', 'sample', 'train', 'val', 'experiment', 'size', 'number of']):
                        if 30 < len(sent) < 250:
                            dataset_sents.append(sent.strip())
                if dataset_sents:
                    lines = [f"- {s} (Section: {sec_name})" for s in dataset_sents[:4]]
                    return "**Dataset Information:**\n" + "\n".join(lines)
        return "Dataset information not found in the paper."
    
    ranked = relevant_sections if relevant_sections is not None else _select_relevant_sections(q, data, max_sections=4)
    return _extractive_query_answer(q, ranked, max_points=4)


def _basic_compare(p1: dict, p2: dict) -> str:
    return _deterministic_compare(p1, p2)

