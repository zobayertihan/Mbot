import os
import json
import re
import html
import hashlib
import datetime
import pathlib
from typing import Any, Dict, Tuple

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ====================== ENV VARIABLES ======================
N8N_LLM_WEBHOOK = os.getenv("N8N_LLM_WEBHOOK", "")
N8N_GITHUB_WEBHOOK = os.getenv("N8N_GITHUB_WEBHOOK", "")
N8N_EXPERTS_WEBHOOK = os.getenv("N8N_EXPERTS_WEBHOOK", "")
FEEDBACK_FILE = pathlib.Path("feedback.json")

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Methodology Recommender",
    page_icon="🚀",
    layout="centered"
)

# ====================== CSS ======================
st.markdown(
    """
    <style>
        .chat-wrapper {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 16px;
        }

        .bubble {
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 80%;
            font-size: 0.95rem;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .bubble-user {
            background: #0066ff;
            color: white;
            border-bottom-right-radius: 4px;
            margin-left: auto;
        }

        .bubble-assistant {
            background: #f0f2f6;
            color: #1a1a1a;
            border-bottom-left-radius: 4px;
        }

        .row-user {
            display: flex;
            justify-content: flex-end;
            width: 100%;
        }

        .row-assistant {
            display: flex;
            justify-content: flex-start;
            width: 100%;
            gap: 8px;
            align-items: flex-end;
        }

        .avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
            background: #e8e8e8;
        }

        .sender-label {
            font-size: 0.75rem;
            color: #888;
            margin-bottom: 3px;
        }

        .label-right {
            text-align: right;
        }

        .label-left {
            text-align: left;
            padding-left: 36px;
        }

        .signal-box {
            background: #f0f7ff;
            border-left: 3px solid #0066ff;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 0.9rem;
            color: #333;
            margin-top: 8px;
        }

        .small-muted {
            color: #777;
            font-size: 0.85rem;
        }

        .expert-card {
            background: #fafafa;
            border: 1px solid #e8e8e8;
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }

        .expert-tag {
            display: inline-block;
            background: #e8f0fe;
            color: #1a56db;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 0.78rem;
            margin-right: 4px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ====================== RECOMMENDER IMPORT ======================
try:
    from recommender import recommend
except Exception:
    from collections import namedtuple

    def recommend(params: Dict[str, Any]):
        """
        Fallback recommender if recommender.py is not available.
        Your real recommender.py will override this automatically.
        """
        Rec = namedtuple(
            "Recommendation",
            ["methodology", "environment", "rationale", "confidence", "alternatives", "scores"]
        )

        features = params.get("features", {})
        output_type = (params.get("output_type") or "").lower()
        domain = params.get("domain", "")

        volatility = str(features.get("requirements_volatility", "medium")).lower()
        tech_uncertainty = str(features.get("tech_uncertainty", "medium")).lower()
        compliance_heavy = bool(features.get("compliance_heavy", False))
        safety_critical = bool(features.get("safety_critical", False))
        team_experience = str(features.get("team_experience", "mixed")).lower()

        if safety_critical or compliance_heavy:
            methodology = "Waterfall"
        elif volatility == "high" or tech_uncertainty == "high":
            methodology = "Scrum"
        elif team_experience == "junior":
            methodology = "Kanban"
        else:
            methodology = "Agile Hybrid"

        env_map = {
            "web": "Node.js + Next.js (TypeScript)",
            "mobile": "Flutter (Dart)",
            "ml": "Python + FastAPI + scikit-learn/TensorFlow",
            "data": "Python + Jupyter + Pandas",
            "3d": "React + Three.js (R3F)",
            "game": "Unity (C#)",
            "dashboard": "Node.js + Next.js + Power BI/Metabase",
            "cloud": "Node.js + Next.js + AWS/Vercel",
            "iot": "Python + FastAPI + MQTT",
            "api": "Python + FastAPI",
            "saas": "Node.js + Next.js + PostgreSQL",
            "desktop": "Electron or Tauri",
            "embedded": "C/C++ or Python depending on hardware",
        }

        environment = env_map.get(output_type, "Node.js + Next.js (TypeScript)")

        rationale = [
            f"Domain: {domain}",
            f"Output type: {output_type}",
            f"Volatility: {volatility}",
            f"Technical uncertainty: {tech_uncertainty}",
            f"Compliance-heavy: {compliance_heavy}",
            f"Safety-critical: {safety_critical}",
            f"Team experience: {team_experience}",
        ]

        return Rec(
            methodology=methodology,
            environment=environment,
            rationale=rationale,
            confidence="medium",
            alternatives=["Kanban", "Scrum"],
            scores={}
        )

# ====================== CONSTANTS ======================
RISKY_DOMAINS = {
    "healthcare",
    "finance",
    "aerospace",
    "automotive",
    "government",
    "defense",
    "medtech"
}

# ====================== HELPER FUNCTIONS ======================
def estimate_needed_months(output_type: str, features: Dict[str, Any], domain: str = "") -> Tuple[int, int]:
    base_by_output = {
        "web": 2,
        "dashboard": 2,
        "data": 2,
        "cloud": 3,
        "mobile": 3,
        "ml": 4,
        "3d": 4,
        "game": 5,
        "iot": 3,
        "api": 2,
        "saas": 4,
        "desktop": 3,
        "embedded": 4,
    }

    base = base_by_output.get((output_type or "").lower(), 2)

    def level_value(key: str) -> int:
        return {
            "low": 0,
            "medium": 1,
            "high": 2
        }.get(str(features.get(key, "medium")).lower(), 1)

    team = int(features.get("team_size", 6))
    experience = str(features.get("team_experience", "mixed")).lower()

    if team <= 2:
        team_adj = 1.0
    elif team <= 5:
        team_adj = 0.0
    elif team <= 8:
        team_adj = -0.5
    else:
        team_adj = -1.0

    if experience == "junior":
        exp_adj = 0.5
    elif experience == "senior":
        exp_adj = -0.5
    else:
        exp_adj = 0

    months_float = (
        base
        + level_value("requirements_volatility")
        + level_value("innovation_needed")
        + level_value("tech_uncertainty")
        + (1 if features.get("compliance_heavy") else 0)
        + (2 if features.get("safety_critical") else 0)
        + (0.5 if features.get("distributed_team") else 0)
        + (1 if (domain or "").lower() in RISKY_DOMAINS else 0)
        + team_adj
        + exp_adj
    )

    months_float = max(1.0, months_float)
    low = int(round(max(1.0, months_float * 0.8)))
    high = int(round(months_float * 1.2))

    if high <= low:
        high = low + 1

    return low, high


def llm_chat(messages, max_tokens: int = 320, temperature: float = 0.2) -> str:
    """
    Sends chat messages to your n8n LLM webhook.
    Expected n8n response can be:
    - OpenAI/Groq style: {"choices": [{"message": {"content": "..."}}]}
    - Simple style: {"text": "..."} or {"content": "..."}
    - Array style: [{"text": "..."}]
    """
    if not N8N_LLM_WEBHOOK.strip():
        return "N8N_LLM_WEBHOOK is not set in your .env file."

    import requests

    try:
        response = requests.post(
            N8N_LLM_WEBHOOK,
            json={
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            data = data[0]

        if isinstance(data, dict):
            if data.get("error"):
                return f"{data.get('message', 'LLM error.')}"

            choices = data.get("choices") or []
            if choices:
                return choices[0].get("message", {}).get("content", "") or ""

            return data.get("text") or data.get("content") or data.get("answer") or str(data)

        return str(data)

    except Exception as e:
        return f"LLM request failed: {str(e)}"


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Tries to extract JSON from LLM output.
    """
    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def extract_signals_from_description(description: str) -> Dict[str, Any]:
    """
    Extracts structured signals from the project description using n8n/Groq.
    This is only called when the user clicks the sidebar button.
    """
    if not description.strip():
        return {}

    prompt = f"""
You are a signal extractor for a software project recommender tool.

Read the project description and return ONLY valid JSON.

Allowed values:
- detected_domain: warehouse, e-commerce, healthcare, finance, logistics, education, government, aerospace, automotive, saas, gaming, research, or null
- detected_output_type: web, mobile, ml, data, 3d, game, dashboard, cloud, iot, api, saas, desktop, embedded, or null
- detected_volatility: low, medium, high, or null
- detected_innovation: low, medium, high, or null
- detected_tech_uncertainty: low, medium, high, or null
- detected_experience: junior, mixed, senior, or null
- detected_budget: low, medium, high, or null
- detected_compliance: none, gdpr, hipaa, soc2, financial, aviation, medical, or null
- detected_safety: true, false, or null
- summary: short human-readable summary

Project description:
{description}
"""

    messages = [
        {
            "role": "system",
            "content": "You extract JSON signals from software project descriptions. Return only valid JSON."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    result = llm_chat(messages, max_tokens=300, temperature=0.1)
    return extract_json_from_text(result)


def infer_tech_stack(environment_text: str):
    env = (environment_text or "").lower()
    tech_stack = []

    mapping = {
        "next.js": "next.js",
        "nextjs": "next.js",
        "react": "react",
        "typescript": "typescript",
        "node": "node",
        "python": "python",
        "fastapi": "fastapi",
        "tensorflow": "tensorflow",
        "scikit": "scikit-learn",
        "pandas": "pandas",
        "flutter": "flutter",
        "dart": "dart",
        "three": "three.js",
        "unity": "unity",
        "mqtt": "mqtt",
        "postgresql": "postgresql",
        "postgres": "postgresql",
    }

    for key, value in mapping.items():
        if key in env and value not in tech_stack:
            tech_stack.append(value)

    return tech_stack


def safe_html(text: str) -> str:
    return html.escape(str(text)).replace("\n", "<br>")


# ====================== EXPERT DISCOVERY ======================
# Dev.to tag names verified to exist and have good traffic.
# Rules: lowercase, hyphens allowed, no camelCase, no spaces.
METHODOLOGY_TAGS = {
    "Scrum":         ["scrum", "agile", "project-management"],
    "Kanban":        ["kanban", "agile", "productivity"],
    "Waterfall":     ["project-management", "software-development", "career"],
    "XP":            ["tdd", "agile", "testing"],
    "Lean":          ["lean", "productivity", "devops"],
    "Agile Hybrid":  ["agile", "scrum", "project-management"],
    "SAFe":          ["agile", "leadership", "project-management"],
    "Shape Up":      ["productivity", "project-management", "ux"],
    "Design Sprint": ["ux", "design", "productivity"],
    "Spiral":        ["software-development", "architecture", "devops"],
    "Stage-Gate":    ["product", "project-management", "entrepreneurship"],
}

DOMAIN_TAGS = {
    "healthcare":  "health",
    "finance":     "fintech",
    "e-commerce":  "ecommerce",
    "education":   "education",
    "gaming":      "gamedev",
    "ml":          "machinelearning",
    "ai":          "ai",
    "iot":         "iot",
    "saas":        "saas",
    "data":        "datascience",
    "research":    "opensource",
    "logistics":   "devops",
    "warehouse":   "backend",
    "aerospace":   "career",
    "automotive":  "opensource",
    "government":  "career",
}


def fetch_experts_via_devto(methodology: str, domain: str, tech_stack: str,
                             experience: str, output_type: str) -> list:
    """
    Calls Dev.to public API directly from Python — no n8n, no API key needed.
    Searches multiple tags (methodology + domain + tech) and returns
    deduplicated authors sorted by reactions.
    """
    import requests

    meth_tags  = METHODOLOGY_TAGS.get(methodology, ["agile", "project-management"])
    domain_tag = DOMAIN_TAGS.get(domain, "")
    env_lower  = (tech_stack or "").lower()
    tech_tag   = next(
        (t for t in ["python", "react", "typescript", "flutter", "node", "fastapi", "javascript"]
         if t in env_lower),
        ""
    )

    # Methodology tags go FIRST — ensures most relevant authors appear before generic ones.
    all_tags = list(meth_tags)
    if domain_tag and domain_tag not in all_tags:
        all_tags.append(domain_tag)
    if tech_tag and tech_tag not in all_tags:
        all_tags.append(tech_tag)
    all_tags = all_tags[:5]

    all_articles = []
    for tag in all_tags:
        try:
            resp = requests.get(
                "https://dev.to/api/articles",
                params={"tag": tag, "per_page": 8},
                timeout=10,
            )
            if resp.ok:
                articles = resp.json()
                articles.sort(key=lambda a: a.get("positive_reactions_count", 0), reverse=True)
                for a in articles:
                    a["_matched_tag"] = tag
                all_articles.extend(articles)
        except Exception:
            continue

    if not all_articles:
        return []

    primary_tag = meth_tags[0] if meth_tags else ""
    seen       = set()
    tag_counts = {}
    authors    = []

    for article in all_articles:
        user     = article.get("user", {})
        username = user.get("username", "")
        if not username or username in seen:
            continue
        tag          = article.get("_matched_tag", "")
        max_from_tag = 3 if tag == primary_tag else 1
        if tag_counts.get(tag, 0) >= max_from_tag:
            continue
        seen.add(username)
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        authors.append({
            "name":           user.get("name", username),
            "username":       username,
            "profile_image":  user.get("profile_image_90", ""),
            "latest_article": article.get("title", ""),
            "article_url":    article.get("url", ""),
            "article_tag":    tag or (article.get("tag_list") or [""])[0],
            "reactions":      article.get("positive_reactions_count", 0),
            "reading_time":   article.get("reading_time_minutes", 0),
        })
        if len(authors) >= 5:
            break

    return authors


# ====================== FEEDBACK ======================
def save_feedback_local(rating: str, comment: str, methodology: str, domain: str,
                        output_type: str, confidence: str, params: Dict) -> bool:
    """
    Appends a feedback entry to feedback.json in the project directory.
    Creates the file if it doesn't exist.
    """
    entry = {
        "timestamp":   datetime.datetime.utcnow().isoformat(),
        "rating":      rating,
        "comment":     comment,
        "methodology": methodology,
        "domain":      domain,
        "output_type": output_type,
        "confidence":  confidence,
        "team_size":   params.get("team_size"),
        "experience":  params.get("team_experience"),
        "volatility":  params.get("requirements_volatility"),
        "budget":      params.get("budget_constraint"),
        "compliance":  params.get("compliance_type"),
        "safety":      params.get("safety_critical"),
    }
    try:
        existing = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8")) if FEEDBACK_FILE.exists() else []
        existing.append(entry)
        FEEDBACK_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False


# ====================== SESSION STATE INIT ======================
default_states = {
    "explain_cache": {},
    "github_cache": {},
    "expert_cache": {},
    "devto_cache": {},
    "generated_explanation": None,
    "generated_github": None,
    "generated_expert": None,
    "chat_messages": [],
    "chat_context_key": None,
    "desc_signals": {},
    "desc_signal_key": None,
    "feedback_submitted": [],
}

for key, default in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ====================== SIDEBAR ======================
st.sidebar.title("Project Parameters")

DOMAINS = [
    "warehouse",
    "e-commerce",
    "healthcare",
    "finance",
    "logistics",
    "education",
    "government",
    "aerospace",
    "automotive",
    "saas",
    "gaming",
    "research",
]

OUTPUT_TYPES = [
    "web",
    "mobile",
    "ml",
    "data",
    "3d",
    "game",
    "dashboard",
    "cloud",
    "iot",
    "api",
    "saas",
    "desktop",
    "embedded",
]

st.sidebar.subheader("Project Description")

project_description = st.sidebar.text_area(
    "Describe your project (optional)",
    height=120,
    placeholder=(
        "Example: We are building a fintech app for small businesses. "
        "Team of 4, two are interns. Hard deadline in 3 months for investor demo."
    ),
    help="Optional. Click 'Apply Description Signals' to let AI extract useful signals from this description."
)

description_key = hashlib.sha256(project_description.strip().encode()).hexdigest()

if st.sidebar.button("Apply Description Signals", use_container_width=True):
    if project_description.strip():
        with st.sidebar:
            with st.spinner("Extracting signals..."):
                st.session_state.desc_signals = extract_signals_from_description(project_description)
                st.session_state.desc_signal_key = description_key
    else:
        st.sidebar.warning("Write a project description first.")

if st.sidebar.button("Clear Description Signals", use_container_width=True):
    st.session_state.desc_signals = {}
    st.session_state.desc_signal_key = None
    st.rerun()

signals = st.session_state.desc_signals if st.session_state.desc_signal_key == description_key else {}

st.sidebar.subheader("Project")

default_domain = signals.get("detected_domain") if signals.get("detected_domain") in DOMAINS else "warehouse"
default_output = signals.get("detected_output_type") if signals.get("detected_output_type") in OUTPUT_TYPES else "web"

domain = st.sidebar.selectbox(
    "Project domain",
    DOMAINS,
    index=DOMAINS.index(default_domain),
    help="The industry or field your project belongs to."
)

output_type = st.sidebar.selectbox(
    "Output type",
    OUTPUT_TYPES,
    index=OUTPUT_TYPES.index(default_output),
    help="What kind of software are you building?"
)

st.sidebar.subheader("Team")

team_size = st.sidebar.number_input(
    "Team size",
    min_value=1,
    max_value=100,
    value=6,
    help="Total number of people working on the project."
)

experience_options = ["junior", "mixed", "senior"]
default_experience = signals.get("detected_experience") if signals.get("detected_experience") in experience_options else "mixed"

team_experience = st.sidebar.selectbox(
    "Team experience",
    experience_options,
    index=experience_options.index(default_experience),
    help="junior = mostly inexperienced, mixed = mixed skill levels, senior = experienced team."
)

st.sidebar.subheader("Project Uncertainty")

level_options = ["low", "medium", "high"]

default_volatility = signals.get("detected_volatility") if signals.get("detected_volatility") in level_options else "medium"
default_innovation = signals.get("detected_innovation") if signals.get("detected_innovation") in level_options else "medium"
default_tech_unc = signals.get("detected_tech_uncertainty") if signals.get("detected_tech_uncertainty") in level_options else "medium"
default_budget = signals.get("detected_budget") if signals.get("detected_budget") in level_options else "medium"

req_vol = st.sidebar.selectbox(
    "Requirements volatility",
    level_options,
    index=level_options.index(default_volatility),
    help="How likely the requirements are to change."
)

innovation = st.sidebar.selectbox(
    "Innovation needed",
    level_options,
    index=level_options.index(default_innovation),
    help="How much novelty or experimentation the project needs."
)

tech_unc = st.sidebar.selectbox(
    "Technical uncertainty",
    level_options,
    index=level_options.index(default_tech_unc),
    help="How uncertain the technical solution is."
)

budget_constraint = st.sidebar.selectbox(
    "Budget constraint",
    level_options,
    index=level_options.index(default_budget),
    help="low = little budget, high = strong budget/funding."
)

st.sidebar.subheader("Risk & Compliance")

compliance_options = ["none", "gdpr", "hipaa", "soc2", "financial", "aviation", "medical"]
default_compliance_type = signals.get("detected_compliance") if signals.get("detected_compliance") in compliance_options else "none"

compliance_type = st.sidebar.selectbox(
    "Compliance type",
    compliance_options,
    index=compliance_options.index(default_compliance_type),
    help="Choose the strongest compliance concern."
)

default_compliance_bool = compliance_type != "none"
default_safety_bool = bool(signals.get("detected_safety")) if signals.get("detected_safety") is not None else False

compliance = st.sidebar.checkbox(
    "Compliance-heavy",
    value=default_compliance_bool,
    help="Check this if the project has legal, audit, privacy, or industry regulation constraints."
)

safety = st.sidebar.checkbox(
    "Safety-critical",
    value=default_safety_bool,
    help="Check this if failure can harm people, property, or critical operations."
)

distributed = st.sidebar.checkbox(
    "Distributed team",
    value=True,
    help="Check this if team members work from different locations or time zones."
)

available_months = st.sidebar.number_input(
    "Available time (months)",
    min_value=1,
    max_value=36,
    value=3,
    help="How many months are available before delivery/demo/MVP deadline."
)

# ====================== COMPUTE RECOMMENDATION ======================
est_features = {
    "team_size": team_size,
    "team_experience": team_experience,
    "requirements_volatility": req_vol,
    "innovation_needed": innovation,
    "tech_uncertainty": tech_unc,
    "budget_constraint": budget_constraint,
    "compliance_heavy": compliance,
    "compliance_type": compliance_type,
    "safety_critical": safety,
    "distributed_team": distributed,
}

need_lo, need_hi = estimate_needed_months(output_type, est_features, domain)

ratio = available_months / max(1, need_lo)

if ratio >= 1.25:
    time_pressure = "low"
elif ratio >= 0.9:
    time_pressure = "medium"
else:
    time_pressure = "high"

features_for_recommender = {
    **est_features,
    "time_pressure": time_pressure,
}

rec = recommend({
    "domain": domain,
    "output_type": output_type,
    "features": features_for_recommender,
})

method_text = rec.methodology
env_text = rec.environment
rationale_list = rec.rationale
confidence = getattr(rec, "confidence", "medium")
alternatives = getattr(rec, "alternatives", [])
scores = getattr(rec, "scores", {})

context_block = (
    f"Project description:\n{project_description or 'No free-text description provided.'}\n\n"
    f"Project context:\n"
    f"- Domain: {domain}\n"
    f"- Output type: {output_type}\n"
    f"- Team size: {team_size}\n"
    f"- Team experience: {team_experience}\n"
    f"- Requirements volatility: {req_vol}\n"
    f"- Innovation needed: {innovation}\n"
    f"- Technical uncertainty: {tech_unc}\n"
    f"- Budget constraint: {budget_constraint}\n"
    f"- Compliance heavy: {compliance}\n"
    f"- Compliance type: {compliance_type}\n"
    f"- Safety critical: {safety}\n"
    f"- Distributed team: {distributed}\n"
    f"- Available months: {available_months}\n"
    f"- Estimated needed: {need_lo}–{need_hi} months\n"
    f"- Time pressure: {time_pressure}\n\n"
    f"Recommended methodology: {method_text}\n"
    f"Recommended environment: {env_text}\n"
    f"Confidence: {confidence}\n"
    f"Rationale: {'; '.join(str(r) for r in rationale_list)}\n"
)

_cache_key = hashlib.sha256(
    json.dumps(
        {
            "project_description": project_description,
            "signals": signals,
            "domain": domain,
            "output_type": output_type,
            "team_size": team_size,
            "team_experience": team_experience,
            "req_vol": req_vol,
            "innovation": innovation,
            "tech_unc": tech_unc,
            "budget_constraint": budget_constraint,
            "compliance": compliance,
            "compliance_type": compliance_type,
            "safety": safety,
            "distributed": distributed,
            "available_months": available_months,
            "methodology": method_text,
            "environment": env_text,
            "confidence": confidence,
        },
        sort_keys=True
    ).encode()
).hexdigest()

# Reset chat only when project parameters change
if st.session_state.chat_context_key != _cache_key:
    st.session_state.chat_context_key = _cache_key
    st.session_state.chat_messages = []

# ====================== MAIN UI ======================
st.title("Methodology & Environment Recommender")
st.caption("AI-assisted selection of project methodologies and development environments for novice/startup teams.")

col1, col2 = st.columns(2)

with col1:
    st.success(f"**Recommended Methodology**\n\n### {method_text}")

with col2:
    st.info(f"**Recommended Environment**\n\n{env_text}")

if confidence:
    st.caption(f"Recommendation confidence: **{confidence}**")

if available_months < need_lo:
    st.warning(
        f"**Timeline looks unrealistic.** Estimated **{need_lo}–{need_hi} months** needed, "
        f"but you have **{available_months}**. Consider reducing scope or adding time."
    )
else:
    st.success(
        f"**Timeline looks feasible.** Estimated need: **{need_lo}–{need_hi} months**. "
        f"You have **{available_months}**."
    )

# ====================== SHOW EXTRACTED SIGNALS ======================
if signals and project_description.strip():
    with st.expander("Signals extracted from your project description", expanded=False):
        if signals.get("summary"):
            st.markdown(
                f'<div class="signal-box"><b>AI detected:</b> {html.escape(str(signals["summary"]))}</div>',
                unsafe_allow_html=True
            )

        overrides = []

        if signals.get("detected_domain"):
            overrides.append(f"Domain → **{signals['detected_domain']}**")
        if signals.get("detected_output_type"):
            overrides.append(f"Output type → **{signals['detected_output_type']}**")
        if signals.get("detected_volatility"):
            overrides.append(f"Requirements volatility → **{signals['detected_volatility']}**")
        if signals.get("detected_innovation"):
            overrides.append(f"Innovation level → **{signals['detected_innovation']}**")
        if signals.get("detected_tech_uncertainty"):
            overrides.append(f"Technical uncertainty → **{signals['detected_tech_uncertainty']}**")
        if signals.get("detected_experience"):
            overrides.append(f"Team experience → **{signals['detected_experience']}**")
        if signals.get("detected_budget"):
            overrides.append(f"Budget → **{signals['detected_budget']}**")
        if signals.get("detected_compliance") and signals.get("detected_compliance") != "none":
            overrides.append(f"Compliance type → **{str(signals['detected_compliance']).upper()}**")
        if signals.get("detected_safety") is True:
            overrides.append("Safety-critical → **true**")

        if overrides:
            st.caption("These detected values were used as sidebar defaults:")
            for item in overrides:
                st.markdown(f"- {item}")
        else:
            st.caption("No strong parameter overrides detected.")

# ====================== AI TOOLS BUTTONS ======================
st.divider()
st.subheader("AI Tools")

tool_col1, tool_col2, tool_col3, tool_col4 = st.columns([1, 1, 1, 0.7])

with tool_col1:
    explain_clicked = st.button("AI Explanation", type="primary", use_container_width=True)

with tool_col2:
    github_clicked = st.button("GitHub Projects", use_container_width=True)

with tool_col3:
    expert_clicked = st.button("Find Experts", use_container_width=True)

with tool_col4:
    reset_clicked = st.button("Reset", use_container_width=True)

if reset_clicked:
    st.session_state.explain_cache = {}
    st.session_state.github_cache = {}
    st.session_state.expert_cache = {}
    st.session_state.devto_cache = {}
    st.session_state.generated_explanation = None
    st.session_state.generated_github = None
    st.session_state.generated_expert = None
    st.rerun()

if explain_clicked:
    st.session_state.generated_explanation = _cache_key

if github_clicked:
    st.session_state.generated_github = _cache_key

if expert_clicked:
    st.session_state.generated_expert = _cache_key

# ====================== AI EXPLANATION SECTION ======================
if st.session_state.generated_explanation == _cache_key:
    st.divider()
    st.subheader("AI Explanation")

    if _cache_key not in st.session_state.explain_cache:
        with st.spinner("Generating explanation via n8n/Groq…"):
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a precise SDLC advisor for startup teams and novice engineers. "
                        "Do not contradict the final recommendation. "
                        "Write no more than 150 words. "
                        "If a project description was provided, reference it naturally. "
                        "First explain why the recommended methodology and environment fit. "
                        "Then add the heading 'Alternatives:' and list exactly 2 short bullets using '-'."
                    )
                },
                {
                    "role": "user",
                    "content": context_block + "\nWrite the explanation now."
                }
            ]

            explanation = llm_chat(messages, max_tokens=350, temperature=0.2)

            def needs_continuation(text: str) -> bool:
                if not text:
                    return True

                if "Alternatives:" in text:
                    after = text.split("Alternatives:", 1)[1]
                    bullets = re.findall(r"(?m)^\s*[-•*]\s+\S", after)
                    return len(bullets) < 2

                return False

            if needs_continuation(explanation):
                continuation = llm_chat(
                    [
                        {
                            "role": "system",
                            "content": "Finish the response. Ensure 'Alternatives:' has exactly 2 '-' bullets. Maximum 60 words."
                        },
                        {
                            "role": "user",
                            "content": "Continue. Do not repeat earlier text."
                        }
                    ],
                    max_tokens=120,
                    temperature=0.2
                )

                explanation = (explanation or "") + ("\n" + continuation if continuation else "")

        st.session_state.explain_cache[_cache_key] = explanation or "Could not generate explanation."

    st.markdown(st.session_state.explain_cache[_cache_key])

    # Inline shortcuts below explanation
    # Hide completely when both sections are already triggered
    _github_done = st.session_state.generated_github == _cache_key
    _expert_done = st.session_state.generated_expert == _cache_key
    if not _github_done and not _expert_done:
        _sc1, _sc2 = st.columns(2)
        with _sc1:
            if st.button("Find GitHub Projects", key="github_btn_below_explain", use_container_width=True):
                st.session_state.generated_github = _cache_key
                st.rerun()
        with _sc2:
            if st.button("Find Experts", key="expert_btn_below_explain", use_container_width=True):
                st.session_state.generated_expert = _cache_key
                st.rerun()
    elif _github_done and not _expert_done:
        if st.button("Find Experts", key="expert_btn_below_explain", use_container_width=True):
            st.session_state.generated_expert = _cache_key
            st.rerun()
    elif not _github_done and _expert_done:
        if st.button("Find GitHub Projects", key="github_btn_below_explain", use_container_width=True):
            st.session_state.generated_github = _cache_key
            st.rerun()
    # else: both done, show nothing

# ====================== GITHUB PROJECTS SECTION ======================
if st.session_state.generated_github == _cache_key:
    st.divider()
    st.subheader("Similar GitHub Projects")

    if not N8N_GITHUB_WEBHOOK.strip():
        st.caption("Set N8N_GITHUB_WEBHOOK in your .env file to enable GitHub search.")
    else:
        if _cache_key not in st.session_state.github_cache:
            with st.spinner("Searching GitHub through n8n…"):
                import requests

                tech_stack = infer_tech_stack(env_text)

                payload = {
                    "project_domain": domain,
                    "output_type": output_type,
                    "tech_stack": tech_stack[:2],
                    "methodology": method_text,
                    "project_size": "small" if team_size <= 5 else ("medium" if team_size <= 12 else "large"),
                    "duration_weeks": available_months * 4,
                    "project_description": project_description,
                }

                try:
                    response = requests.post(
                        N8N_GITHUB_WEBHOOK,
                        json=payload,
                        timeout=30
                    )

                    response.raise_for_status()
                    data = response.json()

                    if isinstance(data, list) and data:
                        data = data[0]

                    st.session_state.github_cache[_cache_key] = data.get("repositories", [])

                except Exception as e:
                    st.session_state.github_cache[_cache_key] = []
                    st.error(f"GitHub search failed: {e}")

        repos = st.session_state.github_cache.get(_cache_key, [])

        if repos:
            for index, repo in enumerate(repos[:5], 1):
                name = repo.get("name", "Unnamed repository")
                url = repo.get("url", "")
                stars = repo.get("stars", 0)
                description = repo.get("description", "")
                language = repo.get("language", "")

                if url:
                    st.markdown(f"**{index}. [{name}]({url})** ⭐ {stars}")
                else:
                    st.markdown(f"**{index}. {name}** ⭐ {stars}")

                if description:
                    st.caption(description[:180] + ("..." if len(description) > 180 else ""))

                if language:
                    st.caption(f"🔤 Language: {language}")

                if index < len(repos[:5]):
                    st.divider()
        else:
            st.caption("No similar repositories found. Try changing the project domain or output type.")

        # Show Expert button below GitHub results if not yet triggered
        if st.session_state.generated_expert != _cache_key:
            st.divider()
            if st.button("Find Community Experts", key="expert_btn_below_github", use_container_width=True):
                st.session_state.generated_expert = _cache_key
                st.rerun()


# ====================== EXPERT SUGGESTIONS SECTION ======================
if st.session_state.generated_expert == _cache_key:
    st.divider()
    st.subheader("Find Community Experts")
    st.caption(
        f"Dev.to authors relevant to **{method_text}** · **{domain}** · **{env_text.split()[0]}** — "
        f"searched across methodology, domain, and tech stack tags."
    )

    if _cache_key not in st.session_state.devto_cache:
        with st.spinner("Searching Dev.to for relevant authors…"):
            authors = fetch_experts_via_devto(
                methodology=method_text,
                domain=domain,
                tech_stack=env_text,
                experience=team_experience,
                output_type=output_type,
            )
            st.session_state.devto_cache[_cache_key] = authors

    devto_authors = st.session_state.devto_cache.get(_cache_key)

    if devto_authors:
        st.caption(f"Found **{len(devto_authors)}** author(s) — sorted by most reactions:")
        for author in devto_authors:
            col_img, col_info = st.columns([1, 7])
            with col_img:
                if author.get("profile_image"):
                    st.image(author["profile_image"], width=52)
                else:
                    st.markdown("### 👤")
            with col_info:
                st.markdown(
                    f"**[{author.get('name', author.get('username', ''))}]"
                    f"(https://dev.to/{author.get('username', '')})**"
                    f" &nbsp; `@{author.get('username', '')}`"
                )
                if author.get("latest_article"):
                    tag_badge = f"`#{author.get('article_tag', '')}`" if author.get("article_tag") else ""
                    st.markdown(
                        f"📝 [{author['latest_article']}]({author.get('article_url', '#')}) "
                        f"· ❤️ {author.get('reactions', 0)} "
                        f"· ⏱ {author.get('reading_time', 0)} min read "
                        f"{tag_badge}"
                    )
            st.divider()
    else:
        st.warning("No authors found. Dev.to may be temporarily unavailable — try again in a moment.")

# ====================== FOLLOW-UP CHAT SECTION ======================
st.divider()
st.subheader("Ask Follow-up Questions")
st.caption("This chat is separate from AI Explanation, GitHub Projects, and Expert Search.")

SYSTEM_PROMPT = (
    "You are a helpful software development mentor for startup teams and novice engineers. "
    "Answer questions about the methodology recommendation conversationally. "
    "Be practical, concise, and encouraging. "
    "Keep answers under 100 words unless the user asks for more detail."
)

# Render chat history
if st.session_state.chat_messages:
    chat_html = '<div class="chat-wrapper">'

    for message in st.session_state.chat_messages:
        content = safe_html(message.get("content", ""))

        if message.get("role") == "user":
            chat_html += (
                f'<div class="row-user">'
                f'<div>'
                f'<div class="sender-label label-right">You</div>'
                f'<div class="bubble bubble-user">{content}</div>'
                f'</div>'
                f'</div>'
            )
        else:
            chat_html += (
                f'<div class="row-assistant">'
                f'<div class="avatar">🤖</div>'
                f'<div>'
                f'<div class="sender-label label-left">Mentor</div>'
                f'<div class="bubble bubble-assistant">{content}</div>'
                f'</div>'
                f'</div>'
            )

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
else:
    st.caption("No messages yet — ask your first question below.")

# Enter-to-send form
with st.form("followup_form", clear_on_submit=True):
    question = st.text_input(
        "Your question:",
        placeholder="e.g. Why not Kanban? How should we run sprints with a small team?",
        label_visibility="collapsed"
    )

    submitted = st.form_submit_button(
        "Send",
        use_container_width=True
    )

if submitted and question.strip():
    user_question = question.strip()

    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_question
    })

    llm_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"Project context:\n{context_block}"
        },
        {
            "role": "assistant",
            "content": "Understood. Ready to answer questions about this recommendation."
        },
    ] + st.session_state.chat_messages[-10:]

    with st.spinner("Mentor is typing…"):
        answer = llm_chat(
            llm_messages,
            max_tokens=220,
            temperature=0.3
        )

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": answer or "No response."
    })

    st.rerun()

if st.button("Clear Chat", use_container_width=True):
    st.session_state.chat_messages = []
    st.rerun()

# ====================== FEEDBACK SECTION ======================
st.divider()
st.subheader("Was this recommendation helpful?")

feedback_key      = f"feedback_{_cache_key}"
already_submitted = feedback_key in st.session_state.feedback_submitted

if already_submitted:
    st.success("Thank you for your feedback!")
else:
    col_up, col_down = st.columns(2)
    with col_up:
        helpful_btn = st.button("Yes, this was helpful", use_container_width=True)
    with col_down:
        nothelpful_btn = st.button("No, this didn't fit my project", use_container_width=True)

    feedback_comment = st.text_area(
        "Optional comment (what worked or didn't work?):",
        placeholder="e.g. The methodology was correct but the timeline estimate seemed too long.",
        height=80,
        key=f"comment_{_cache_key}",
    )

    def _send_feedback(rating: str):
        save_feedback_local(
            rating      = rating,
            comment     = feedback_comment.strip(),
            methodology = method_text,
            domain      = domain,
            output_type = output_type,
            confidence  = confidence,
            params      = features_for_recommender,
        )
        st.session_state.feedback_submitted.append(feedback_key)
        st.rerun()

    if helpful_btn:
        _send_feedback("helpful")
    if nothelpful_btn:
        _send_feedback("not_helpful")

# # ====================== DEBUG / CONFIG INFO ======================
# with st.expander(" Webhook Configuration Status", expanded=False):
#     st.write("N8N_LLM_WEBHOOK:", "✅ Set" if N8N_LLM_WEBHOOK else "❌ Missing")
#     st.write("N8N_GITHUB_WEBHOOK:", "✅ Set" if N8N_GITHUB_WEBHOOK else "❌ Missing")
#     st.write("N8N_EXPERTS_WEBHOOK:", "✅ Set" if N8N_EXPERTS_WEBHOOK else "❌ Missing")

#     st.caption("For production n8n workflows, use /webhook/... URLs, not /webhook-test/... URLs.")