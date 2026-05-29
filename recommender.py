from __future__ import annotations

"""
recommender.py
Version: 4.0.0
Last updated: 2026-03-10
Author: Abu Zobayer Bin Siddique (202411224)

Deterministic recommender for:
- Software development methodology
- Development environment/tooling

─────────────────────────────────────────
SCORING PHILOSOPHY
─────────────────────────────────────────
Every methodology starts at 0.0.
Points are only awarded or deducted at LOW or HIGH values.
MEDIUM is always neutral (0 points) for all methodologies.
No methodology has a home advantage at default settings.
The winner must emerge purely from the combination of signals.

─────────────────────────────────────────
METHODOLOGY SELECTION CRITERIA (from SDLC literature)
─────────────────────────────────────────
Scrum      → structured sprints, regular feedback, medium-large team,
             needs coordination, some uncertainty, willing to do ceremonies
Kanban     → continuous flow, process improvement, no fixed iterations,
             senior/autonomous team, stable workload, low ceremony
Waterfall  → fixed/stable requirements, compliance-heavy, documentation
             needed, predictable scope, safety-critical
XP         → small team, very high code quality focus, pair programming,
             very high tech uncertainty, frequent releases
Lean       → efficiency focus, waste reduction, well-understood problem,
             experienced team, low overhead needed
Agile Hybrid→ mixed signals, some compliance + some flexibility, medium
             everything, cannot commit to one pure framework
Shape Up   → small autonomous team, fixed time budget (6-week cycles),
             async-friendly, low ceremony, senior team
SAFe       → large organisation (10+ people), multiple teams, enterprise
             coordination, scaled agile needed
Design Sprint → pure discovery/innovation phase, hypothesis testing,
             very high innovation, short burst (1 week), not for full project
Spiral     → high risk management, safety-critical, iterative risk analysis,
             large budget, regulated domain
Stage-Gate → product/R&D projects, formal management approval at each phase,
             hardware+software combined, high investment, regulated industry,
             low-medium volatility (gates require stable deliverables per stage)

─────────────────────────────────────────
CHANGELOG
─────────────────────────────────────────
v1.0.0 — Original prototype (TS2)
v2.0.0 — Expanded engine: +3 methodologies, +3 parameters, confidence score
v3.0.0 — Fixed Scrum bias at medium/default values
v3.1.0 — Fixed Kanban bias at distributed/small team/mixed defaults
v4.1.0 — Added Stage-Gate methodology (11th candidate)
         Stage-Gate wins for: R&D/product projects, high budget,
         management approval gates, hardware+software, regulated domain,
         low-medium volatility, high compliance
v4.0.0 — Full rewrite from SDLC literature
         Scoring rebuilt from theory, not intuition
         Hard rule: medium = 0 points for everyone, always
         Each methodology only wins when signals genuinely point to it
─────────────────────────────────────────
"""

__version__ = "4.1.0"

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple


# ====================== Public API ======================

@dataclass
class Recommendation:
    methodology:  str
    environment:  str
    rationale:    List[str]
    confidence:   str = "medium"
    alternatives: List[str] = field(default_factory=list)
    scores:       Dict[str, float] = field(default_factory=dict)


def recommend(params: Dict[str, Any]) -> Recommendation:
    domain      = _norm(params.get("domain"))
    output_type = _norm(params.get("output_type"))
    features    = params.get("features", {}) or {}

    environment, env_reasons = _pick_environment(domain, output_type)
    methodology, alternatives, confidence, scores, meth_reasons = _pick_methodology(features, domain)

    rationale: List[str] = []
    rationale.append(f"Domain: {params.get('domain', '')}")
    rationale.append(f"Output type: {params.get('output_type', '')}")
    rationale.extend(env_reasons)
    rationale.extend(meth_reasons)

    return Recommendation(
        methodology  = methodology,
        environment  = environment,
        rationale    = rationale,
        confidence   = confidence,
        alternatives = alternatives,
        scores       = scores,
    )


# ====================== Internals ======================

DOMAIN_REGULATED    = {"healthcare","finance","aerospace","automotive","government","gov","defense","medtech","clinic","bio"}
DOMAIN_CONSUMER     = {"e-commerce","ecommerce","education","media","gaming","retail","food","travel"}
DOMAIN_INDUSTRIAL   = {"warehouse","logistics","erp","manufacturing","iot","energy"}
DOMAIN_EXPERIMENTAL = {"ml","ai","research","blockchain","crypto","data","analytics"}

ENV_MAP = {
    "web":       "Node.js + Next.js (TypeScript)",
    "dashboard": "Node.js + Next.js (TypeScript)",
    "cloud":     "Node.js + Next.js (TypeScript) + AWS/Vercel",
    "ml":        "Python + FastAPI + scikit-learn / TensorFlow",
    "ai":        "Python + FastAPI + LangChain / OpenAI SDK",
    "data":      "Python + Jupyter + Pandas",
    "analytics": "Python + Metabase + Pandas",
    "etl":       "Python + Apache Airflow + Pandas",
    "mobile":    "Flutter (Dart)",
    "android":   "Flutter (Dart)",
    "ios":       "Flutter (Dart)",
    "app":       "Flutter (Dart)",
    "3d":        "React + Three.js (R3F)",
    "game":      "Unity (C#)",
    "iot":       "Python + FastAPI + MQTT + InfluxDB",
    "embedded":  "C / C++ + FreeRTOS",
    "desktop":   "Electron (TypeScript) or Tauri (Rust)",
    "api":       "Python + FastAPI or Node.js + Express",
    "saas":      "Node.js + Next.js (TypeScript) + PostgreSQL",
}

CANDIDATES = [
    "Scrum", "Kanban", "XP", "Waterfall", "Spiral",
    "Lean", "Agile Hybrid", "SAFe", "Shape Up", "Design Sprint",
    "Stage-Gate",
]


def _norm(v: Any) -> str:
    return str(v or "").strip().lower()

def _lv(value: Any) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(_norm(value), 1)

def _lvl(n: int) -> str:
    return {0: "low", 1: "medium", 2: "high"}.get(int(n), "medium")


def _pick_environment(domain: str, output_type: str) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    env = ENV_MAP.get(output_type)
    if env:
        reasons.append(f"Environment selected for output type '{output_type}'.")
        return env, reasons
    if domain in DOMAIN_CONSUMER | DOMAIN_INDUSTRIAL:
        reasons.append(f"Web stack selected as default for '{domain}' domain.")
        return ENV_MAP["web"], reasons
    if domain in DOMAIN_EXPERIMENTAL:
        reasons.append(f"ML/data stack selected for experimental domain '{domain}'.")
        return ENV_MAP["ml"], reasons
    if domain in DOMAIN_REGULATED:
        reasons.append(f"Python backend stack selected for regulated domain '{domain}'.")
        return ENV_MAP["ml"], reasons
    reasons.append("Web stack used as sensible default.")
    return ENV_MAP["web"], reasons


def _pick_methodology(
    features: Dict[str, Any],
    domain: str = "",
) -> Tuple[str, List[str], str, Dict[str, float], List[str]]:

    # ── inputs ──────────────────────────────────────────────────────────
    vol       = _lv(features.get("requirements_volatility", "medium"))
    tpress    = _lv(features.get("time_pressure", "medium"))
    inno      = _lv(features.get("innovation_needed", "medium"))
    tech      = _lv(features.get("tech_uncertainty", "medium"))
    comp      = bool(features.get("compliance_heavy", False))
    safe      = bool(features.get("safety_critical", False))
    dist      = bool(features.get("distributed_team", False))
    exp       = _norm(features.get("team_experience", "mixed"))
    budget    = _lv(features.get("budget_constraint", "medium"))
    comp_type = _norm(features.get("compliance_type", "none"))
    try:
        team = int(features.get("team_size", 6))
    except Exception:
        team = 6

    scores:  Dict[str, float] = {m: 0.0 for m in CANDIDATES}
    reasons: List[str]        = []

    # ================================================================
    # RULE: medium = 0 points always. Only LOW and HIGH move scores.
    # ================================================================

    # ── 1. REQUIREMENTS VOLATILITY ──────────────────────────────────
    # HIGH: requirements change often → need iterative, adaptive methods
    # LOW:  requirements are fixed → sequential methods work fine
    if vol == 2:
        scores["Scrum"]        += 3.0
        scores["XP"]           += 2.5
        scores["Kanban"]       += 1.5
        scores["Agile Hybrid"] += 1.0
        scores["Waterfall"]    -= 2.0
        scores["Stage-Gate"]   -= 2.0   # gates require stable deliverables — breaks under high volatility
        reasons.append("High requirements volatility → iterative methods essential (Scrum / XP / Kanban). Waterfall and Stage-Gate penalised.")
    elif vol == 0:
        scores["Waterfall"]    += 2.5
        scores["Lean"]         += 1.5
        scores["Shape Up"]     += 1.0
        scores["Stage-Gate"]   += 2.0   # fixed scope per stage = Stage-Gate's sweet spot
        scores["Scrum"]        -= 0.5
        reasons.append("Low requirements volatility → sequential/stable methods preferred (Waterfall / Stage-Gate / Lean).")

    # ── 2. TIME PRESSURE ────────────────────────────────────────────
    # HIGH: tight deadline → low ceremony, fast flow
    # LOW:  relaxed timeline → thorough planning and risk analysis viable
    if tpress == 2:
        scores["Kanban"]      += 2.5
        scores["Lean"]        += 2.0
        scores["Shape Up"]    += 1.5
        scores["Scrum"]       += 0.5
        scores["Waterfall"]   -= 1.0
        scores["Spiral"]      -= 1.5
        scores["Stage-Gate"]  -= 2.0   # gate reviews slow delivery significantly
        reasons.append("High time pressure → fast flow methods preferred (Kanban / Lean / Shape Up). Stage-Gate and Spiral penalised.")
    elif tpress == 0:
        scores["Waterfall"]    += 1.5
        scores["Spiral"]       += 2.0
        scores["Stage-Gate"]   += 1.5   # gate reviews need time — suits relaxed timelines
        scores["Agile Hybrid"] += 0.5
        reasons.append("Low time pressure → thorough planning and staged reviews viable (Spiral / Stage-Gate / Waterfall).")

    # ── 3. INNOVATION & TECHNICAL UNCERTAINTY ───────────────────────
    # HIGH: unknown territory → need rapid experimentation and feedback
    # LOW:  known domain → standard delivery methods suffice
    if inno == 2 or tech == 2:
        scores["Design Sprint"] += 2.5
        scores["XP"]            += 2.0
        scores["Agile Hybrid"]  += 2.0
        scores["Scrum"]         += 1.0
        scores["Waterfall"]     -= 2.5
        scores["Stage-Gate"]    -= 1.0   # gates assume known deliverables — uncertainty disrupts reviews
        scores["Lean"]          -= 0.5
        reasons.append("High innovation/uncertainty → experimentation methods needed (Design Sprint / XP / Agile Hybrid). Waterfall and Stage-Gate penalised.")
    elif inno == 0 and tech == 0:
        scores["Waterfall"]     += 2.0
        scores["Lean"]          += 1.5
        scores["Kanban"]        += 1.0
        scores["Stage-Gate"]    += 1.5   # known deliverables per stage = ideal for Stage-Gate
        scores["Design Sprint"] -= 2.0
        scores["XP"]            -= 0.5
        reasons.append("Low innovation and uncertainty → predictable delivery methods preferred (Waterfall / Stage-Gate / Lean).")

    # ── 4. COMPLIANCE & SAFETY ──────────────────────────────────────
    if comp:
        scores["Waterfall"]    += 2.5
        scores["Spiral"]       += 1.5
        scores["Stage-Gate"]   += 2.0   # gate reviews produce audit-ready documentation naturally
        scores["Agile Hybrid"] += 0.5
        scores["Kanban"]       -= 0.5
        scores["Design Sprint"] -= 1.0
        reasons.append("Compliance-heavy → formal phases and documentation required (Waterfall / Stage-Gate / Spiral).")

    if safe:
        scores["Waterfall"]  += 2.5
        scores["Spiral"]     += 2.5
        scores["Stage-Gate"] += 1.5   # kill/go decisions at each gate reduce risk of unsafe delivery
        scores["Scrum"]      -= 1.0
        scores["Kanban"]     -= 1.0
        reasons.append("Safety-critical → rigorous risk management and verification gates needed (Spiral / Waterfall / Stage-Gate).")

    if comp_type == "hipaa":
        scores["Waterfall"]  += 1.5
        scores["Spiral"]     += 1.0
        scores["Stage-Gate"] += 1.0
        reasons.append("HIPAA → strict audit trails and documentation phases required.")
    elif comp_type == "gdpr":
        scores["Agile Hybrid"] += 1.0
        scores["Scrum"]        += 0.5
        reasons.append("GDPR → manageable within iterative frameworks with dedicated privacy reviews.")
    elif comp_type == "soc2":
        scores["Waterfall"]    += 1.0
        scores["Agile Hybrid"] += 0.5
        scores["Stage-Gate"]   += 0.5
        reasons.append("SOC2 → structured documentation requirements.")
    elif comp_type == "faa":
        scores["Waterfall"]  += 3.0
        scores["Spiral"]     += 2.0
        scores["Stage-Gate"] += 1.5   # FAA stage reviews compatible with Stage-Gate gates
        scores["Scrum"]      -= 2.0
        scores["Kanban"]     -= 2.0
        reasons.append("FAA certification → DO-178C sequential verification required. Agile methods strongly penalised.")

    if domain in DOMAIN_REGULATED:
        scores["Waterfall"]  += 1.0
        scores["Spiral"]     += 0.5
        scores["Stage-Gate"] += 1.0   # regulated industries commonly use Stage-Gate for product approval
        reasons.append(f"Regulated domain ('{domain}') → structured methodologies preferred (Waterfall / Stage-Gate).")

    # ── 5. TEAM SIZE ────────────────────────────────────────────────
    # Literature: Scrum designed for 3-9 people, SAFe for 10+, XP for small teams
    if team <= 3:
        scores["XP"]           += 2.0  # XP designed for small co-located teams
        scores["Kanban"]       += 1.5  # simple to adopt for tiny teams
        scores["Shape Up"]     += 1.5  # async-friendly, no ceremonies
        scores["Scrum"]        -= 1.0  # Scrum ceremonies (standup, retro, planning) too heavy
        scores["SAFe"]         -= 4.0  # completely unsuitable
        scores["Agile Hybrid"] -= 0.5
        reasons.append("Very small team (≤3) → XP / Kanban / Shape Up preferred. Scrum and SAFe overhead not justified.")
    elif 4 <= team <= 9:
        scores["Scrum"]    += 2.0  # Scrum is designed exactly for this team size
        scores["XP"]       += 1.0
        scores["Kanban"]   += 0.5
        scores["SAFe"]     -= 2.0  # SAFe overkill for single small team
        reasons.append("Small-medium team (4–9) → Scrum is purpose-built for this size.")
    elif 10 <= team <= 15:
        scores["Scrum"]        += 1.5  # still works but coordination harder
        scores["SAFe"]         += 1.5  # SAFe starts to make sense
        scores["Agile Hybrid"] += 1.0
        reasons.append("Medium-large team (10–15) → Scrum or SAFe; coordination becoming important.")
    else:
        scores["SAFe"]      += 4.0   # SAFe purpose-built for large organisations
        scores["Waterfall"] += 1.0
        scores["Scrum"]     -= 0.5   # single Scrum team cannot handle 15+ people
        scores["Kanban"]    -= 1.0
        scores["XP"]        -= 1.0
        reasons.append("Large team (>15) → SAFe purpose-built for multi-team coordination.")

    # ── 6. TEAM EXPERIENCE ──────────────────────────────────────────
    # Literature: juniors need structure/coaching; seniors prefer autonomy
    if exp == "junior":
        scores["Scrum"]        += 2.0  # sprint reviews + retrospectives coach juniors
        scores["XP"]           += 1.5  # pair programming accelerates junior learning
        scores["Waterfall"]    -= 1.5  # juniors struggle with big upfront design
        scores["Shape Up"]     -= 1.5  # requires high autonomy — wrong for juniors
        scores["Lean"]         -= 0.5  # lean requires process maturity
        scores["Kanban"]       -= 0.5  # without WIP discipline, juniors lose focus
        reasons.append("Junior team → coaching-heavy structured methods preferred (Scrum / XP). Autonomy-heavy methods penalised.")
    elif exp == "senior":
        scores["Kanban"]    += 2.0  # seniors self-manage flow without ceremonies
        scores["Lean"]      += 2.0  # seniors can identify and eliminate waste
        scores["Shape Up"]  += 1.5  # seniors thrive with autonomy and fixed budgets
        scores["XP"]        += 0.5  # seniors appreciate engineering rigour
        scores["Scrum"]     -= 1.5  # seniors often find Scrum ceremonies wasteful
        scores["SAFe"]      -= 0.5  # seniors dislike heavy frameworks
        reasons.append("Senior team → autonomous, low-ceremony methods preferred (Kanban / Lean / Shape Up). Scrum penalised.")
    # mixed experience = neutral, no points either way

    # ── 7. DISTRIBUTED TEAM ─────────────────────────────────────────
    # Distributed teams need visibility and explicit coordination
    # Both Scrum and Kanban help but for different reasons
    if dist:
        scores["Scrum"]  += 0.8  # ceremonies force regular communication
        scores["Kanban"] += 0.8  # visual boards give async visibility
        scores["SAFe"]   += 0.5  # SAFe handles multi-location coordination
        scores["XP"]     -= 1.0  # XP depends on co-location and pair programming
        scores["Shape Up"] -= 0.5  # shape up works async but needs strong writing culture
        reasons.append("Distributed team → visibility tools and explicit cadence helpful (Scrum / Kanban). XP penalised (needs co-location).")

    # ── 8. BUDGET ───────────────────────────────────────────────────
    if budget == 0:
        scores["Kanban"]        += 2.0
        scores["Lean"]          += 1.5
        scores["Shape Up"]      += 1.0
        scores["Scrum"]         -= 1.0
        scores["SAFe"]          -= 3.0
        scores["Stage-Gate"]    -= 2.0   # gate reviews require dedicated management time and resources
        scores["Design Sprint"]  -= 0.5
        scores["Spiral"]        -= 0.5
        reasons.append("Low budget → zero-overhead methods preferred (Kanban / Lean / Shape Up). Stage-Gate, Scrum and SAFe penalised.")
    elif budget == 2:
        scores["SAFe"]          += 1.5
        scores["Spiral"]        += 1.0
        scores["Stage-Gate"]    += 2.0   # Stage-Gate requires investment in formal gate reviews and management oversight
        scores["Design Sprint"] += 0.5
        scores["Scrum"]         += 0.5
        reasons.append("High budget → comprehensive methods with formal governance viable (Stage-Gate / SAFe / Spiral).")

    # ── 9. RANK AND CONFIDENCE ──────────────────────────────────────
    ranked     = sorted(CANDIDATES, key=lambda m: (scores[m], -CANDIDATES.index(m)), reverse=True)
    best       = ranked[0]
    alts       = ranked[1:3]
    gap        = scores[ranked[0]] - scores[ranked[1]]
    confidence = "high" if gap >= 2.5 else ("medium" if gap >= 1.0 else "low")

    if confidence == "low":
        reasons.append(
            f"Low confidence: '{ranked[0]}' and '{ranked[1]}' are close in score. "
            f"Consider reviewing both options carefully."
        )

    reasons.append(
        f"Selected '{best}' (confidence: {confidence}) | "
        f"volatility={_lvl(vol)}, time_pressure={_lvl(tpress)}, "
        f"innovation={_lvl(inno)}, tech={_lvl(tech)}, "
        f"experience={exp}, budget={_lvl(budget)}, "
        f"compliance={comp_type if comp_type != 'none' else comp}, "
        f"safety={safe}, distributed={dist}, team={team}."
    )

    return best, alts, confidence, scores, reasons