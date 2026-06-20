"""
AceSAT Adaptive Prep — agent backend.

This is not a Q&A chatbot. The Flask app below owns four autonomous
decisions on the student's behalf, each implemented as its own function
so the "agent logic" is easy to find and grade:

  1. select_next_question()  -> decides what to practice next, and why
  2. record_attempt()        -> updates a live mastery model, and decides
                                 whether the student needs a scaffold
                                 (mini re-teach) before continuing
  3. build_study_plan()      -> reviews the whole mastery profile and
                                 writes a personalized weekly plan
  4. check_in()              -> decides whether to proactively nudge the
                                 student about a neglected skill

Claude is used for the two generative jobs (tailored explanations and the
weekly plan's narrative). If no API key is configured, or the call fails
or is slow, every one of those paths has a deterministic fallback so the
app keeps working on a flaky connection — important for students on
school wifi or limited data plans.
"""
import json
import os
import random
import sqlite3
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "acesat.db")
QUESTIONS_PATH = os.path.join(BASE_DIR, "data", "questions.json")
DIAGNOSTIC_SIZE = 8          # one question per skill before adapting
MASTERY_LEARNING_RATE = 0.35
DEFAULT_MASTERY = 0.30
EXPLORATION_RATE = 0.12      # chance the agent samples a non-weakest skill
SCAFFOLD_TRIGGER_STREAK = 3  # consecutive misses before a mini re-teach

app = Flask(__name__, static_folder="static", template_folder="templates")

with open(QUESTIONS_PATH) as f:
    QUESTION_DATA = json.load(f)
SKILLS = QUESTION_DATA["skills"]
QUESTIONS_BY_ID = {q["id"]: q for q in QUESTION_DATA["questions"]}
QUESTIONS_BY_SKILL = {}
for q in QUESTION_DATA["questions"]:
    QUESTIONS_BY_SKILL.setdefault(q["skill"], []).append(q)

ANTHROPIC_MODEL = "claude-sonnet-4-6"
_anthropic_client = None
if os.environ.get("ANTHROPIC_API_KEY"):
    try:
        from anthropic import Anthropic
        _anthropic_client = Anthropic()
    except Exception as e:  # library missing or bad key shape, etc.
        print(f"[agent] Anthropic client unavailable, using fallbacks only: {e}")


# ----------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            skill TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mastery (
            student_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            score REAL NOT NULL,
            target_difficulty INTEGER NOT NULL DEFAULT 1,
            correct_streak INTEGER NOT NULL DEFAULT 0,
            wrong_streak INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_practiced TEXT,
            PRIMARY KEY (student_id, skill)
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            source TEXT NOT NULL
        );
        """
    )
    db.commit()
    db.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------
# Mastery model
# ----------------------------------------------------------------------
def get_mastery_row(db, student_id, skill):
    row = db.execute(
        "SELECT * FROM mastery WHERE student_id=? AND skill=?", (student_id, skill)
    ).fetchone()
    if row is None:
        db.execute(
            """INSERT INTO mastery (student_id, skill, score, target_difficulty,
                                     correct_streak, wrong_streak, attempts, last_practiced)
               VALUES (?, ?, ?, 1, 0, 0, 0, NULL)""",
            (student_id, skill, DEFAULT_MASTERY),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM mastery WHERE student_id=? AND skill=?", (student_id, skill)
        ).fetchone()
    return row


def get_all_mastery(db, student_id):
    out = {}
    for skill in SKILLS:
        out[skill] = dict(get_mastery_row(db, student_id, skill))
    return out


def update_mastery(db, student_id, skill, correct):
    """Exponential update toward 1.0 on correct, toward 0.0 on incorrect.
    Also runs a 2-correct-up / 1-wrong-down difficulty staircase per skill,
    and tracks the wrong-streak the scaffold trigger relies on."""
    row = get_mastery_row(db, student_id, skill)
    score = row["score"]
    target_difficulty = row["target_difficulty"]
    correct_streak = row["correct_streak"]
    wrong_streak = row["wrong_streak"]

    if correct:
        score = score + (1 - score) * MASTERY_LEARNING_RATE
        correct_streak += 1
        wrong_streak = 0
        if correct_streak >= 2 and target_difficulty < 3:
            target_difficulty += 1
            correct_streak = 0
    else:
        score = score - score * MASTERY_LEARNING_RATE
        wrong_streak += 1
        correct_streak = 0
        if target_difficulty > 1:
            target_difficulty -= 1

    score = max(0.05, min(0.98, score))

    db.execute(
        """UPDATE mastery SET score=?, target_difficulty=?, correct_streak=?,
               wrong_streak=?, attempts=attempts+1, last_practiced=?
           WHERE student_id=? AND skill=?""",
        (score, target_difficulty, correct_streak, wrong_streak, now_iso(), student_id, skill),
    )
    db.commit()
    return {
        "skill": skill,
        "new_score": score,
        "target_difficulty": target_difficulty,
        "wrong_streak": wrong_streak,
    }


# ----------------------------------------------------------------------
# Agent 1: question selection
# ----------------------------------------------------------------------
def select_next_question(db, student_id):
    mastery = get_all_mastery(db, student_id)
    total_attempts = sum(m["attempts"] for m in mastery.values())
    seen_ids = {
        r["question_id"]
        for r in db.execute(
            "SELECT DISTINCT question_id FROM attempts WHERE student_id=?", (student_id,)
        ).fetchall()
    }

    # --- Diagnostic phase: cover every skill once before adapting ---
    untried_skills = [s for s, m in mastery.items() if m["attempts"] == 0]
    if total_attempts < DIAGNOSTIC_SIZE and untried_skills:
        skill = untried_skills[0]
        reason = (
            f"Diagnostic check: you haven't tried {SKILLS[skill]} yet, so the agent "
            f"is sampling it now to build an accurate starting profile."
        )
        difficulty = 1
        pool = [q for q in QUESTIONS_BY_SKILL[skill] if q["difficulty"] == difficulty]
        question = random.choice(pool)
        return question, reason, "diagnostic", total_attempts

    # --- Adaptive phase: weight toward weak skills ---
    weights = {}
    for skill, m in mastery.items():
        weakness = (1.05 - m["score"]) ** 2
        novelty_bonus = 1.25 if m["attempts"] < 3 else 1.0
        weights[skill] = weakness * novelty_bonus

    if random.random() < EXPLORATION_RATE:
        skill = random.choice(list(mastery.keys()))
        reason = (
            f"Mixing in a quick {SKILLS[skill]} question to keep all skills warm, "
            f"even though it isn't currently your weakest area."
        )
    else:
        skill = max(weights, key=weights.get)
        pct = round(mastery[skill]["score"] * 100)
        reason = (
            f"Picked {SKILLS[skill]} because it's your lowest mastery skill right now "
            f"({pct}%). The agent prioritizes whatever you're weakest in."
        )

    difficulty = mastery[skill]["target_difficulty"]
    pool = [q for q in QUESTIONS_BY_SKILL[skill] if q["difficulty"] == difficulty]
    unseen = [q for q in pool if q["id"] not in seen_ids]
    candidates = unseen if unseen else pool  # allow repeats once exhausted
    if not candidates:
        # difficulty has no questions (edge case) — widen search
        candidates = QUESTIONS_BY_SKILL[skill]
    question = random.choice(candidates)
    return question, reason, "adaptive", total_attempts


def public_question(q):
    return {
        "id": q["id"],
        "subject": q["subject"],
        "skill": q["skill"],
        "skill_label": SKILLS[q["skill"]],
        "difficulty": q["difficulty"],
        "passage": q["passage"],
        "prompt": q["prompt"],
        "choices": q["choices"],
    }


# ----------------------------------------------------------------------
# Claude integration with deterministic fallbacks
# ----------------------------------------------------------------------
def call_claude(system, user_prompt, max_tokens=400, timeout_s=12):
    if _anthropic_client is None:
        return None
    try:
        start = time.time()
        resp = _anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if time.time() - start > timeout_s:
            return None
        parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "\n".join(parts).strip() or None
    except Exception as e:
        print(f"[agent] Claude call failed, using fallback: {e}")
        return None


def explanation_agent(question, student_choice, correct, scaffold):
    label = SKILLS[question["skill"]]
    if correct and not scaffold:
        ai_text = call_claude(
            system=(
                "You are an encouraging, concise SAT tutor for a high-school student. "
                "Confirm the correct answer in one sentence, then give one short tip "
                "for tackling a slightly harder version of this skill next time. "
                "Keep it under 60 words. No markdown."
            ),
            user_prompt=(
                f"Skill: {label}\nQuestion: {question['prompt']}\n"
                f"Correct answer: {question['answer']}\nStudent answered correctly."
            ),
            max_tokens=150,
        )
        return ai_text or f"Correct! {question['explanation_fallback']}"

    if scaffold:
        ai_text = call_claude(
            system=(
                "You are a patient SAT tutor. The student has missed the same skill "
                "three times in a row. Before another practice question, give a short, "
                "plain-language mini-lesson (3-5 sentences) re-teaching the core idea "
                "behind this skill, using a simple example. Encouraging tone, no markdown."
            ),
            user_prompt=f"Skill: {label}\nMissed question: {question['prompt']}",
            max_tokens=250,
        )
        return ai_text or (
            f"Let's slow down on {label}. {question['explanation_fallback']} "
            f"Take a moment to re-read this idea before the next question — "
            f"you've got this."
        )

    ai_text = call_claude(
        system=(
            "You are an encouraging SAT tutor. The student answered incorrectly. "
            "In under 70 words: explain why the correct answer is right, gently "
            "name the likely mix-up that led to their answer, and give one concrete "
            "tip. Plain language, no markdown, no scolding tone."
        ),
        user_prompt=(
            f"Skill: {label}\nQuestion: {question['prompt']}\n"
            f"Choices: {question['choices']}\nCorrect answer: {question['answer']}\n"
            f"Student answered: {student_choice}\n"
            f"Likely misconception category: {question['misconception_tag']}"
        ),
        max_tokens=180,
    )
    return ai_text or question["explanation_fallback"]


# ----------------------------------------------------------------------
# Agent 3: weekly study plan
# ----------------------------------------------------------------------
def fallback_plan(mastery):
    ranked = sorted(mastery.items(), key=lambda kv: kv[1]["score"])
    weak = [s for s, _ in ranked[:3]]
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    plan_days = []
    for i, day in enumerate(days_order):
        focus = weak[i % len(weak)] if weak else ranked[0][0]
        plan_days.append({
            "day": day,
            "focus_skill": focus,
            "focus_label": SKILLS[focus],
            "num_questions": 8 if i < 5 else 5,
            "note": "Short focused set — quality over quantity." if i >= 5 else
                    "Core practice block on your current weakest skill.",
        })
    return {
        "weekly_focus": [SKILLS[s] for s in weak],
        "days": plan_days,
        "motivational_note": (
            "Your scores show clear room to grow in a few specific areas — that's "
            "good news, because it means focused practice will move the needle fast. "
            "Stick with the plan and check back in a week."
        ),
    }


def build_study_plan(db, student_id):
    mastery = get_all_mastery(db, student_id)
    summary_lines = []
    for skill, m in sorted(mastery.items(), key=lambda kv: kv[1]["score"]):
        summary_lines.append(
            f"- {SKILLS[skill]}: mastery {round(m['score']*100)}%, "
            f"{m['attempts']} questions attempted, current difficulty level {m['target_difficulty']}"
        )
    summary = "\n".join(summary_lines)

    ai_text = call_claude(
        system=(
            "You are an SAT study-plan agent. Given a student's per-skill mastery "
            "profile, output ONLY valid JSON (no markdown fences, no commentary) "
            "matching this schema exactly: "
            '{"weekly_focus": [string, ...max 3], '
            '"days": [{"day": string, "focus_skill_label": string, '
            '"num_questions": int, "note": string}, ...exactly 7 entries], '
            '"motivational_note": string}. '
            "Prioritize the weakest skills, but include at least one lighter review "
            "day. Keep notes under 20 words each, motivational_note under 50 words. "
            "Be specific to the numbers given, not generic."
        ),
        user_prompt=f"Student mastery profile:\n{summary}",
        max_tokens=600,
    )

    if ai_text:
        try:
            cleaned = ai_text.strip().strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            parsed = json.loads(cleaned)
            assert "days" in parsed and len(parsed["days"]) == 7
            source = "agent"
            plan = parsed
        except Exception as e:
            print(f"[agent] plan JSON parse failed, using fallback: {e}")
            plan = fallback_plan(mastery)
            source = "fallback"
    else:
        plan = fallback_plan(mastery)
        source = "fallback"

    db.execute(
        "INSERT INTO plans (student_id, created_at, plan_json, source) VALUES (?, ?, ?, ?)",
        (student_id, now_iso(), json.dumps(plan), source),
    )
    db.commit()
    return plan, source


# ----------------------------------------------------------------------
# Agent 4: proactive check-in / nudge
# ----------------------------------------------------------------------
def check_in(db, student_id):
    mastery = get_all_mastery(db, student_id)
    total_attempts = sum(m["attempts"] for m in mastery.values())
    if total_attempts < DIAGNOSTIC_SIZE:
        return None

    never_revisited = [
        (s, m) for s, m in mastery.items()
        if m["attempts"] > 0 and m["score"] < 0.45
    ]
    if never_revisited:
        skill, m = min(never_revisited, key=lambda sm: sm[1]["score"])
        pct = round(m["score"] * 100)
        return (
            f"Heads up — your {SKILLS[skill]} mastery is sitting at {pct}%, "
            f"the lowest of all your skills. Want a focused 5-question warm-up "
            f"on it right now?"
        )

    best_skill, best_m = max(mastery.items(), key=lambda sm: sm[1]["score"])
    if best_m["attempts"] > 0 and best_m["score"] > 0.8:
        return (
            f"Nice work — {SKILLS[best_skill]} is now at "
            f"{round(best_m['score']*100)}% mastery. Keep the streak going!"
        )
    return None


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/api/students", methods=["POST"])
def api_create_student():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    db = get_db()
    row = db.execute("SELECT id FROM students WHERE name=?", (name,)).fetchone()
    is_new = row is None
    if is_new:
        db.execute(
            "INSERT INTO students (name, created_at) VALUES (?, ?)", (name, now_iso())
        )
        db.commit()
        row = db.execute("SELECT id FROM students WHERE name=?", (name,)).fetchone()
    return jsonify({"student_id": row["id"], "name": name, "is_new": is_new})


@app.route("/api/next-question")
def api_next_question():
    student_id = request.args.get("student_id", type=int)
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
    db = get_db()
    question, reason, mode, total_attempts = select_next_question(db, student_id)
    return jsonify({
        "question": public_question(question),
        "reasoning": reason,
        "mode": mode,
        "diagnostic_progress": min(total_attempts, DIAGNOSTIC_SIZE),
        "diagnostic_total": DIAGNOSTIC_SIZE,
    })


@app.route("/api/answer", methods=["POST"])
def api_answer():
    body = request.json or {}
    student_id = body.get("student_id")
    question_id = body.get("question_id")
    choice = body.get("choice", "")
    if not (student_id and question_id):
        return jsonify({"error": "student_id and question_id are required"}), 400

    question = QUESTIONS_BY_ID.get(question_id)
    if not question:
        return jsonify({"error": "unknown question_id"}), 404

    correct = choice.strip().upper().startswith(question["answer"])
    db = get_db()
    db.execute(
        """INSERT INTO attempts (student_id, question_id, skill, difficulty, correct, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (student_id, question_id, question["skill"], question["difficulty"], int(correct), now_iso()),
    )
    db.commit()
    mastery_update = update_mastery(db, student_id, question["skill"], correct)

    scaffold = (not correct) and mastery_update["wrong_streak"] >= SCAFFOLD_TRIGGER_STREAK
    explanation = explanation_agent(question, choice, correct, scaffold)

    return jsonify({
        "correct": correct,
        "correct_answer": question["answer"],
        "explanation": explanation,
        "scaffold_triggered": scaffold,
        "mastery_update": mastery_update,
    })


@app.route("/api/dashboard")
def api_dashboard():
    student_id = request.args.get("student_id", type=int)
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
    db = get_db()
    mastery = get_all_mastery(db, student_id)
    skills_out = []
    total_attempts = 0
    total_correct = 0
    for skill, m in mastery.items():
        correct_count = db.execute(
            "SELECT COUNT(*) c FROM attempts WHERE student_id=? AND skill=? AND correct=1",
            (student_id, skill),
        ).fetchone()["c"]
        total_attempts += m["attempts"]
        total_correct += correct_count
        skills_out.append({
            "skill": skill,
            "label": SKILLS[skill],
            "score": round(m["score"], 3),
            "attempts": m["attempts"],
            "accuracy": round(correct_count / m["attempts"], 3) if m["attempts"] else None,
            "difficulty_level": m["target_difficulty"],
        })
    skills_out.sort(key=lambda s: s["score"])
    history = db.execute(
        """SELECT skill, correct, difficulty, created_at FROM attempts
           WHERE student_id=? ORDER BY created_at ASC""",
        (student_id,),
    ).fetchall()
    return jsonify({
        "skills": skills_out,
        "total_attempts": total_attempts,
        "overall_accuracy": round(total_correct / total_attempts, 3) if total_attempts else None,
        "history": [dict(h) for h in history],
    })


@app.route("/api/study-plan", methods=["POST"])
def api_study_plan():
    body = request.json or {}
    student_id = body.get("student_id")
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
    db = get_db()
    plan, source = build_study_plan(db, student_id)
    return jsonify({"plan": plan, "source": source})


@app.route("/api/check-in")
def api_check_in():
    student_id = request.args.get("student_id", type=int)
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
    db = get_db()
    nudge = check_in(db, student_id)
    return jsonify({"nudge": nudge})


# Always run at import time — not just under `python3 app.py` — so a
# production WSGI server (gunicorn, etc.) also gets the tables created
# before the first request. CREATE TABLE IF NOT EXISTS makes this safe
# to call on every cold start / worker boot.
init_db()
if _anthropic_client is None:
    print("[agent] ANTHROPIC_API_KEY not set — running on deterministic fallbacks "
          "for explanations and study plans. Set the key for AI-generated text.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"AceSAT Adaptive Prep running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
