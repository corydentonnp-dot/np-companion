# CareCompanion — Commands & Agents Quick Reference

## Custom Agent

| Command | Description |
|---------|-------------|
| `@CareCompanion` | Full product team agent. Audits → Plans → Executes on autopilot. Use for any task. |

**How it works:** When you invoke `@CareCompanion` with a task, it automatically:
1. Audits the codebase (reads PROJECT_STATUS, ACTIVE_PLAN, CHANGE_LOG, relevant files)
2. Builds a detailed plan (written to ACTIVE_PLAN.md)
3. Executes the plan step-by-step (tracked via todo list)
4. Updates all docs (changelog, Feature Registry, Risk Register)

**Override:** Say "plan only" or "don't run on autopilot" to stop after the planning phase.

---

## Slash Commands (Prompts)

Use these in the VS Code Copilot chat panel:

| Command | Role | What It Does |
|---------|------|--------------|
| `/keep-working` | All | Find the next highest-priority task and start working on it — full autopilot loop |
| `/sprint-review` | PM | Audit sprint progress, verify Feature Registry accuracy, identify stale work, plan next steps |
| `/security-audit` | Security Officer | Full HIPAA + OWASP scan: PHI leaks, auth gaps, injection risks, dependency CVEs |
| `/saas-check` | CTO | Audit SaaS readiness: desktop boundary violations, tenant isolation, DB portability |
| `/tech-debt` | CTO | Dead code, duplication, pattern violations, test coverage gaps, stale dependencies |
| `/test-plan` | QA Lead | Generate comprehensive test plan for a feature: happy path, edge cases, auth, isolation |
| `/risk-report` | Risk Manager | Review Risk Register, discover new risks, assess blockers, recommend mitigations |

---

## File-Scoped Instructions (Automatic)

These activate automatically when editing files matching their patterns:

| Scope | Applies To | What It Enforces |
|-------|-----------|------------------|
| Models | `models/**/*.py` | Soft-delete, user_id scoping, timestamp patterns, export to __init__.py |
| Routes | `routes/**/*.py` | @login_required, JSON format, error handling, HIPAA, data scoping |
| Agent | `agent/**/*.py` | Desktop-only boundary, OCR-first rule, error handling, no PHI in logs |
| Adapters | `adapters/**/*.py` | BaseAdapter pattern, EHR-agnostic data, no desktop imports |

---

## Always-On Rules

`.github/copilot-instructions.md` loads automatically on every interaction and enforces:
- HIPAA compliance (no PHI in logs, notifications, or outbound calls)
- Tech stack constraints (Python 3.11, Flask, SQLAlchemy, vanilla JS)
- SaaS readiness (desktop isolation, adapter pattern, query scoping)
- Anti-sprawl (search before creating files, 11-file whitelist for dev_guide)
- Session workflow (audit at start, update docs at end)
- Feature Registry and Risk Register maintenance

---

## Launch Scripts (Project Root)

| Command | What It Does |
|---------|--------------|
| `run.bat` | **One-click launch.** Kill servers → test → git commit/push → start Flask + agent → launch exe/Chrome |
| `run.bat --dev` | Dev mode: hot-reload Flask server, opens Chrome (no exe) |
| `run.bat --skip-tests` | Skip verification tests |
| `run.bat --skip-git` | Skip git commit/push |
| `python launcher.py --mode=all` | Full stack: Flask + Agent + tray + pywebview |
| `python launcher.py --mode=dev` | Flask dev server with hot-reload |
| `python launcher.py --mode=server` | Flask only (no agent, no tray) |
| `python launcher.py --mode=agent` | Agent only (tray + scheduler) |
