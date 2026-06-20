(function () {
  "use strict";

  const state = {
    studentId: null,
    currentQuestion: null,
    answered: false,
  };

  const el = (id) => document.getElementById(id);

  // ---------------- Screen / tab switching ----------------
  function showScreen(name) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("is-active"));
    el(`screen-${name}`).classList.add("is-active");
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.toggle("is-active", b.dataset.screen === name);
    });
    if (name === "progress") loadProgress();
  }

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => showScreen(btn.dataset.screen));
  });

  // ---------------- Login ----------------
  el("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = el("student-name").value.trim();
    if (!name) return;
    const res = await fetch("/api/students", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    const data = await res.json();
    state.studentId = data.student_id;
    el("tabs").hidden = false;
    showScreen("practice");
    loadCheckIn();
    loadNextQuestion();
  });

  // ---------------- Skill colors ----------------
  function fillColorFor(score) {
    if (score >= 0.7) return "var(--teal)";
    if (score >= 0.45) return "var(--amber)";
    return "var(--coral)";
  }

  function renderLadder(container, skills, currentSkill) {
    container.innerHTML = "";
    skills.forEach((s) => {
      const row = document.createElement("div");
      row.className = "ladder-row" + (s.skill === currentSkill ? " is-current" : "");
      const pct = Math.round(s.score * 100);
      row.innerHTML = `
        <div class="ladder-row-head">
          <span>${s.label}</span>
          <span class="pct">${pct}%</span>
        </div>
        <div class="ladder-track">
          <div class="ladder-fill" style="width:${pct}%; background:${fillColorFor(s.score)}"></div>
        </div>`;
      container.appendChild(row);
    });
  }

  async function fetchMastery() {
    const res = await fetch(`/api/dashboard?student_id=${state.studentId}`);
    return res.json();
  }

  // ---------------- Check-in nudge ----------------
  async function loadCheckIn() {
    const res = await fetch(`/api/check-in?student_id=${state.studentId}`);
    const data = await res.json();
    if (data.nudge) {
      el("nudge-text").textContent = data.nudge;
      el("nudge-banner").hidden = false;
    } else {
      el("nudge-banner").hidden = true;
    }
  }
  el("nudge-dismiss").addEventListener("click", () => {
    el("nudge-banner").hidden = true;
  });

  // ---------------- Practice flow ----------------
  async function loadNextQuestion() {
    state.answered = false;
    el("feedback-card").hidden = true;
    el("question-card").style.display = "";

    const res = await fetch(`/api/next-question?student_id=${state.studentId}`);
    const data = await res.json();
    const q = data.question;
    state.currentQuestion = q;

    el("agent-reasoning").textContent = data.reasoning;
    el("diff-badge").textContent = `Level ${q.difficulty}`;
    el("skill-pill").textContent = q.skill_label;

    if (data.mode === "diagnostic") {
      el("diagnostic-progress").hidden = false;
      const pct = Math.round((data.diagnostic_progress / data.diagnostic_total) * 100);
      el("diagnostic-progress-fill").style.width = pct + "%";
      el("diagnostic-progress-label").textContent =
        `${data.diagnostic_progress}/${data.diagnostic_total} diagnostic`;
    } else {
      el("diagnostic-progress").hidden = true;
    }

    if (q.passage) {
      el("passage").hidden = false;
      el("passage").textContent = q.passage;
    } else {
      el("passage").hidden = true;
    }
    el("prompt").textContent = q.prompt;

    const choicesEl = el("choices");
    choicesEl.innerHTML = "";
    q.choices.forEach((choiceText) => {
      const letter = choiceText.trim()[0];
      const btn = document.createElement("button");
      btn.className = "choice-btn";
      btn.textContent = choiceText;
      btn.addEventListener("click", () => submitAnswer(letter, btn));
      choicesEl.appendChild(btn);
    });

    // refresh the sidebar ladder so the highlighted skill matches the new question
    const dash = await fetchMastery();
    renderLadder(el("ladder-bars"), dash.skills, q.skill);
  }

  async function submitAnswer(letter, btnEl) {
    if (state.answered) return;
    state.answered = true;
    document.querySelectorAll(".choice-btn").forEach((b) => (b.disabled = true));

    const res = await fetch("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: state.studentId,
        question_id: state.currentQuestion.id,
        choice: letter,
      }),
    });
    const data = await res.json();

    btnEl.classList.add(data.correct ? "is-correct" : "is-incorrect");
    if (!data.correct) {
      document.querySelectorAll(".choice-btn").forEach((b) => {
        if (b.textContent.trim()[0] === data.correct_answer) b.classList.add("is-correct");
      });
    }

    const statusEl = el("feedback-status");
    if (data.scaffold_triggered) {
      statusEl.textContent = "Let's pause and re-teach this one";
      statusEl.className = "feedback-status scaffold";
    } else if (data.correct) {
      statusEl.textContent = "Correct";
      statusEl.className = "feedback-status correct";
    } else {
      statusEl.textContent = "Not quite";
      statusEl.className = "feedback-status incorrect";
    }
    el("feedback-explanation").textContent = data.explanation;
    el("feedback-card").hidden = false;
    el("feedback-card").scrollIntoView({ behavior: "smooth", block: "nearest" });

    const dash = await fetchMastery();
    renderLadder(el("ladder-bars"), dash.skills, state.currentQuestion.skill);

    loadCheckIn();
  }

  el("next-question-btn").addEventListener("click", loadNextQuestion);

  // ---------------- Progress screen ----------------
  async function loadProgress() {
    const dash = await fetchMastery();
    const statRow = el("stat-row");
    statRow.innerHTML = `
      <div class="stat-box">
        <div class="stat-value">${dash.total_attempts}</div>
        <div class="stat-label">questions answered</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${dash.overall_accuracy != null ? Math.round(dash.overall_accuracy * 100) + "%" : "—"}</div>
        <div class="stat-label">overall accuracy</div>
      </div>`;
    renderLadder(el("progress-ladder"), dash.skills, null);
  }

  // ---------------- Plan screen ----------------
  el("generate-plan-btn").addEventListener("click", async () => {
    el("generate-plan-btn").disabled = true;
    el("generate-plan-btn").textContent = "Thinking through your plan…";
    const res = await fetch("/api/study-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: state.studentId }),
    });
    const data = await res.json();
    el("generate-plan-btn").disabled = false;
    el("generate-plan-btn").textContent = "Regenerate my weekly plan";

    el("plan-source").hidden = false;
    el("plan-source").textContent =
      data.source === "agent"
        ? "Generated live by the AI planning agent"
        : "Generated by the rule-based planner (AI agent unavailable right now)";

    el("plan-motivation").hidden = false;
    el("plan-motivation").textContent = data.plan.motivational_note;

    const daysEl = el("plan-days");
    daysEl.innerHTML = "";
    data.plan.days.forEach((d) => {
      const card = document.createElement("div");
      card.className = "plan-day-card";
      const focusLabel = d.focus_skill_label || d.focus_label || d.focus_skill || "Mixed review";
      card.innerHTML = `
        <div class="day-name">${d.day}</div>
        <div class="day-focus">${focusLabel}</div>
        <div class="day-meta">${d.num_questions} questions</div>
        <div class="day-note">${d.note || ""}</div>`;
      daysEl.appendChild(card);
    });
  });
})();
