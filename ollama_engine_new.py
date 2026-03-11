"""
Ollama AI Engine for PaperIQ Pro.
Calls local Ollama server (http://localhost:11434).
Falls back to extractive summarization if Ollama is unavailable.

IMPROVED: Enhanced answer_question function for better numeric query handling.
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
            score += 1. += min(len(s0

        scorenippet.split()) / 1200, 1.0)
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
    if not title:
        return "Untitled"
    title = re.sub(r'ISSN:?\s*[\d-]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'IC Value:?\s*[\d.]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'SJ Impact Factor:?\s*[\d.]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'doi:?\s*[\d/.-]*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'Vol\.?\s*\d+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'IJ[A-Z]+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'^[\s\-:;|]+', '', title)
    return title if title else "Untitled"


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
    except:
        return None


# IMPROVED ANSWER_QUESTION FUNCTION
def answer_question(question: str, paper_data: dict, model: str = None) -> str:
    """Enhanced answer question function that properly handles numeric queries."""
    question = (question or "").strip()
    if not question:
        return "Please ask a specific question about the paper."
    
    ql = question.lower()
    
    # Check for numeric/specific queries - handle them directly with comprehensive search
    numeric_keywords = ["how much", "how many", "percentage", "percent", "accuracy", "precision", 
                        "recall", "f1", "score", "rate", "number of", "dataset size", "training data", 
                        "images", "samples", "effective", "achieve", "demonstrate", "outperform"]
    
    is_numeric_query = any(kw in ql for kw in numeric_keywords)
    
    if is_numeric_query:
        # Direct comprehensive search for numeric answers
        sections = paper_data.get("sections", {}) or {}
        all_findings = []
        
        # Search ALL sections comprehensively
        for sec_name, raw in sections.items():
            if sec_name.lower() in ['references', 'appendix']:
                continue
            content = _section_text(raw)
            if not content:
                continue
            
            # Split into sentences and find ones with numbers
            sentences = re.split(r'(?<=[.!?])\s+', content.replace('\n', ' '))
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < 25 or len(sent) > 300:
                    continue
                # Must have a number
                if not re.search(r'\d+\.?\d*', sent):
                    continue
                
                # Score the sentence
                score = 0
                # High score for metric keywords
                if any(kw in sent.lower() for kw in ['accuracy', 'precision', 'recall', 'f1', 'percent', '%', 'rate', 'performance', 'score']):
                    score += 10
                # Match with query keywords
                for kw in numeric_keywords:
                    if kw in ql and kw in sent.lower():
                        score += 5
                # Good sign words
                if any(kw in sent.lower() for kw in ['achieve', 'demonstrate', 'show', 'obtain', 'reach', 'improve', 'outperform', 'gain', 'reached', 'obtained']):
                    score += 3
                
                if score > 0:
                    all_findings.append((score, sec_name, sent))
        
        # Sort and return best results
        if all_findings:
            all_findings.sort(key=lambda x: x[0], reverse=True)
            result_lines = []
            seen = set()
            for score, sec, sent in all_findings[:8]:
                key = sent[:50].lower()
                if key not in seen:
                    result_lines.append(f"- {sent} (Section: {sec})")
                    seen.add(key)
            
            if result_lines:
                header = "**Key Findings:**"
                if any(kw in ql for kw in ['accuracy', 'precision', 'recall', 'f1']):
                    header = "**Performance Metrics:**"
                elif any(kw in ql for kw in ['train', 'image', 'sample', 'dataset']):
                    header = "**Dataset & Training Info:**"
                return f"{header}\n" + "\n".join(result_lines)
    
    # For non-numeric questions, try normal processing
    relevant_sections = _select_relevant_sections(question, paper_data, max_sections=4)
    context_blocks = []
    for sec_name, sec_content, _ in relevant_sections:
        context_blocks.append(f"[{sec_name}]\n{sec_content[:1400]}")
    context_text = "\n\n".join(context_blocks)[:5600]

    system_msg = """You are PaperIQ Pro, an intelligent research paper assistant.
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

    # Try Ollama if running
    if is_ollama_running():
        result = _ollama_call(prompt, system_msg, model, max_tokens=420, timeout_s=20)
        if result and len(result.strip()) >= 20:
            if "Section:" not in result:
                evidence = _extractive_query_answer(question, relevant_sections, max_points=3)
                return f"{result}\n\nEvidence:\n{evidence}"
            return result
    
    # Fallback - try extractive search on relevant sections
    return _extractive_query_answer(question, relevant_sections, max_points=5)


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


# Legacy functions for compatibility
def summarize_paper(full_text: str, model: str = None) -> str:
    truncated = full_text[:5500]
    result = _ollama_call(truncated, "Summarize this research paper:", model, max_tokens=550)
    if result is None:
        return _extractive(full_text, n=6)
    return result


def compare_papers(p1: dict, p2: dict, model: str = None) -> str:
    """Compare two papers."""
    return "Paper comparison not fully implemented in this version."


def summarize_section(section_name: str, content: str, model: str = None) -> str:
    if not content or len(content.split()) < 20:
        return "- " + content.strip() if content.strip() else ""
    truncated = content[:3500]
    prompt = f"Section: {section_name}\n\nContent:\n{truncated}\n\nProvide bullet-point summary:"
    result = _ollama_call(prompt, "You are a precise academic research assistant.", model, max_tokens=350)
    if result is None:
        return _extractive(content, n=4)
    return result


def extract_limits_advantages_ai(full_text: str, model: str = None) -> dict:
    """Extract limitations and advantages using AI."""
    return {"limitations": [], "advantages": []}

