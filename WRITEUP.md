# AceSAT — Adaptive SAT Prep Agent
### One-page write-up

## The problem

SAT prep is one of the clearest places the education gap shows up in
plain numbers. A student whose family can afford $100+/hour tutoring or a
structured prep course walks into the test having drilled their exact
weak spots for months. A student at an underserved public school is
usually handed a generic practice book, if anything at all — no
diagnosis of where they're actually losing points, no plan, and no one
checking in when they stop practicing after week one. The gap isn't
really about motivation or intelligence; it's about access to a tutor
who can pay attention to *one student's* specific gaps for as long as it
takes. That kind of attention doesn't scale through human tutors at a
price every school can afford — but it can scale through software, if the
software actually behaves like a tutor instead of a static worksheet.

## Our approach

AceSAT is built as an **agent**, deliberately scoped around four
decisions a real tutor makes without being asked:

1. **Diagnose first.** Before adapting to anything, the agent runs the
   student through one question in each of the 8 official SAT skill
   domains (Heart of Algebra, Problem Solving & Data Analysis, Passport
   to Advanced Math, Geometry & Trig, and the four Reading & Writing
   domains), so it isn't guessing what's weak from zero data.
2. **Adapt continuously.** After the diagnostic, the agent maintains a
   live mastery score per skill and always serves the next question from
   the weakest, least-practiced area — at a difficulty matched to a
   simple up/down staircase — rather than letting the student pick a
   chapter and stay in their comfort zone.
3. **Intervene, not just grade.** If a student misses the same skill
   three times in a row, the agent stops drilling and inserts a short,
   plain-language re-teach of the underlying concept before the next
   question. This is the difference between "marking wrong" and actually
   tutoring.
4. **Plan ahead.** On request, the agent reviews the student's entire
   mastery profile and writes a structured 7-day study plan — which days
   focus on which skill, how many questions, and a note grounded in their
   actual numbers — the same task a human tutor would do at the end of a
   session, done automatically.

Every one of these is visible to the student in an "Agent's move" panel
that states *why* a question was chosen, so the system stays legible
instead of feeling like a black box.

We also designed for the realities of the classrooms we're trying to
reach: no login wall, a page that loads in under a second on slow wifi,
large mobile tap targets, and — critically — every AI-generated feature
has a deterministic fallback, so a flaky school internet connection
degrades the experience instead of breaking it.

## The impact

For a student at an underserved school, the value isn't a slicker
interface — it's three things they currently can't get without paying
for a tutor: an honest diagnosis of where they actually stand, a plan
that updates itself as they improve instead of going stale, and a system
that notices when they're stuck on the same misconception and stops to
explain it, rather than burying them in more wrong answers. None of that
requires expensive hardware or a stable broadband connection, which means
it can realistically run on a shared school Chromebook or a student's own
phone on a data plan.

At a program level, this also gives schools and counselors a concrete
mastery dashboard per student — the same kind of progress signal a paid
tutor would report back to a parent, now available for every student a
school serves, not just the ones whose families can afford one.

## What we'd build next

A production version needs a much larger, professionally vetted question
bank (the 40 questions here are an original hackathon-scale demo set,
not sourced from College Board), a stronger mastery model (full Bayesian
Knowledge Tracing instead of our exponential approximation), and real
push reminders via SMS or email — the `check_in()` logic in this repo is
already structured to plug straight into that.
