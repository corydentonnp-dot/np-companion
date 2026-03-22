# CareCompanion Ã¢â‚¬â€ Master Planning Prompt for Copilot / Claude Opus 4.6

You are working inside the **CareCompanion** repository.

Your job is **not** to jump into coding yet.
Your job is to perform a deep, reality-based planning pass for the **billing capture / revenue optimization** expansion of CareCompanion, using the **actual current codebase**, the **existing planning documents**, and the **billing/revenue datasets** already provided.

You must produce a planning output that is grounded in what is already built, what is partially built, what is stubbed, what is blocked, and what can be added with the highest operational and financial value.

At the end of your planning pass, **append your full plan to `running_plan.md`** in the repo. Do not replace prior content. Append a clearly labeled new section.

---

## Core Objective

Design a comprehensive implementation plan for evolving CareCompanionÃ¢â‚¬â„¢s billing capture system into a **compliant, payer-aware, net-collections-focused revenue optimization system** that:

- uses the current project architecture as it actually exists,
- expands the current billing engine intelligently,
- prioritizes **collectible** revenue rather than raw billed dollars,
- reduces denials, write-offs, and workflow leakage,
- improves provider bonus acceleration,
- surfaces actionable, chart-supported billing and workflow opportunities,
- and fits the structure and conventions of the existing Flask + SQLAlchemy + SQLite + Jinja application.

This plan must be detailed enough that later implementation work can proceed phase by phase without needing to rediscover architecture, intent, or priorities.

---

## Critical Instructions

1. **Do not assume prior claims are true.** Verify against the actual repository.
2. **Do not write implementation code yet unless absolutely necessary for inspection helpers.** This is a planning pass.
3. **Do not invent architecture that conflicts with the current project.** Extend what already exists.
4. **Use the repo as the source of truth for current implementation state.**
5. **Use the external planning docs and billing datasets as the source of truth for business intent and prioritization.**
6. **Append your plan to `running_plan.md`.**
7. **Preserve existing content in `running_plan.md`.** Add a new section at the bottom.
8. **Clearly separate verified current state from proposed future work.**
9. **Do not design unsupported upcoding behavior.** The system may recommend the **most specific supported code** or the **best-supported compliant alternative** only when the chart supports it.
10. **Optimize for expected net value, not just billed amount.**

---

## First Actions Ã¢â‚¬â€ Read Before Planning

Read all relevant planning and architecture files that already exist in the project and adjacent working documents.

### Required repo / planning docs
Read these first if present:
- `Documents/dev_guide/RUNNING_PLAN.md`
- `Documents/dev_guide/running_plan_done1.md`
- `Documents/dev_guide/running_plan_done2.md`
- `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md`
- `Documents/dev_guide/API_Integration_Plan.md`
- `Documents/dev_guide/ABOUT.md`
- `Documents/dev_guide/ac_interface_reference_v4.md`
- `Documents/dev_guide/copilot-instructions.md`
- `Documents/dev_guide/Companion.instructions.md`

If these exact paths do not exist, locate the equivalent files in the repo root, project docs folders, or the local working directory and read them there.

### Required billing / revenue intent docs
Read these if present in the repo root, docs folder, working directory, or local Downloads folder:
- `BILLING_CAPTURE_PROMPT.md`
- `REVENUE_OPTIMIZATION_COPILOT_PROMPT.md`
- `CareCompanion_Revenue_Optimization_Expansion_Memo.md`
- `CareCompanion_Billing_Data_Utilization_Memo.md`
- `calendar year dx code revenue - Priority ICD10.csv`
- `Bonus Calculation Sample.xlsx`
- `CareCompanion_Billing_Master_List.xlsx`
- `CareCompanion_Billing_Master_List - Master Billing List.csv`
- `2026_DHS_Code_List_Addendum_12_01_2025.xlsx`
- `2026_DHS_Code_List_Addendum_12_01_2025.txt`
- `2026_DHS_Code_List_Addendum_12_01_2025 - LIST OF CPT1 HCPCS CODES.csv`
- `medicare-payer-coding-guide.pdf`
- `private-payer-coding-guide.pdf`
- preventive coverage references already supplied to the project

### Required code areas to inspect
You must inspect the actual billing-related implementation in the codebase, including but not limited to:
- `billing_engine/`
- `billing_engine/detectors/`
- `models/`
- `routes/`
- `templates/`
- `migrations/`
- `agent_service.py`
- any config files that hold payer maps, code maps, or rule constants
- any current dashboard or patient-chart surfaces where billing opportunities are displayed or should be displayed

At minimum, verify:
- current models
- current migrations
- current detector coverage
- current API endpoints
- current templates / UI surfaces
- current jobs / schedulers
- any existing reporting pages
- any billing acceptance / dismissal / audit workflows
- any provider preference toggles

---

## Current-State Guide You Should Use, But Still Verify in Code

A prior repository exploration reported the following billing state. Use this as a **guide**, not as unquestioned truth. Verify all of it against the real files:

- There is a `billing_engine` package with a reasonably solid orchestration foundation.
- The engine auto-discovers detectors, deduplicates opportunities, sorts by priority/revenue, and respects provider category toggles.
- Shared payer routing and helper logic already exist.
- Roughly 11 detectors are meaningfully implemented and around 15 remain stubs.
- `BillingOpportunity` and `BillingRuleCache` exist or were intended; `BillingRule` may still be missing or incomplete.
- Pre-visit and monthly billing jobs may already exist.
- Billing UI templates may exist but still be unconnected because core endpoints are missing.
- Dedicated billing API routes may be absent or incomplete.

You must confirm what is truly implemented, what is broken, and what merely exists in HTML or migration form.

---

## Business / Financial Strategy You Must Incorporate

Your plan must reflect the following realities and planning direction:

### 1. Optimize for net expected collections, not gross billed revenue
The annual diagnosis billing data is a **gold mine** and must be used far beyond reporting.

Use it to drive planning for:
- expected receipts,
- write-off rates,
- adjustment rates,
- probable denial risk proxies,
- documentation burden,
- staff effort burden,
- time-to-cash,
- bonus acceleration,
- opportunity-family prioritization,
- and Ã¢â‚¬Å“do not build yetÃ¢â‚¬Â deprioritization.

The system should eventually reason in terms of **expected net value** rather than raw billed amount.

### 2. Coding suggestions must remain compliant
The system must **not** suggest unsupported or fabricated upcoding.

It may:
- suggest the **most specific supported code**,
- suggest the **best-supported alternative when multiple valid options are available**,
- identify missing documentation elements needed to support a more specific code,
- and rank supported options by expected net value, denial risk, and historical collections.

It must **not** recommend a causal or complication code merely because it pays more if the chart does not support it.

### 3. Bonus logic clarification
Use the user-provided interpretation as the working assumption unless actual governing documentation inside the repo proves otherwise:

- bonus appears to be based on clearing a threshold (example: **$115,000**) and then earning **$0.25 on the dollar above threshold**,
- quarter handling does **not** appear to be a cumulative deficit carry-forward model.

If the workbook or code logic differs, identify that mismatch explicitly in the plan and treat it as a contract/business-rule verification dependency.

### 4. The diagnosis-year billing file should shape roadmap priority
The diagnosis revenue CSV should be treated as a planning input for:
- diagnosis-family prioritization,
- registry/campaign design,
- stack-builder design,
- template improvement targets,
- denial-prevention targets,
- and rollout sequencing.

This system should become a **practice-specific revenue operations engine**, not a generic billing helper.

---

## Planning Themes You Must Cover

Your plan must deeply address all of the following areas.

### A. Current Billing Engine Completion
Plan the completion of the current billing engine foundation, including:
- missing models,
- broken migrations,
- missing routes,
- disconnected UI templates,
- detector completion,
- action workflows,
- monthly reports,
- audit trails,
- testing,
- and admin visibility.

### B. Opportunity Scoring / Expected Net Value Engine
Plan a scoring engine that can eventually combine:
- billed amount,
- historical receipts,
- adjustment/write-off behavior,
- denial risk proxy,
- documentation burden,
- completion probability,
- payer behavior,
- time-to-cash,
- bonus timing,
- and staff effort.

This should produce something like:
- expected net dollars,
- opportunity score,
- urgency / quarter-end value,
- and implementation priority.

### C. Code Specificity Recommender
Plan a compliant module that can:
- evaluate chart-supported diagnosis specificity,
- compare valid supported code options,
- surface missing documentation needed for a more specific option,
- and rank the supported options by expected net value and denial risk.

### D. Standalone vs Stack-Only Classifier
Some services should be chased only when stacked onto a larger visit or workflow.
Plan logic that can classify opportunities as:
- strong standalone,
- strong stack-only,
- weak unless payer + documentation conditions are ideal,
- or not worth prompting except under special conditions.

### E. Diagnosis-Family Intelligence Layer
Plan rollups and dashboards by diagnosis family, such as:
- hypertension,
- diabetes / prediabetes,
- hyperlipidemia,
- thyroid,
- obesity,
- tobacco,
- behavioral health,
- immunization,
- preventive Z-code families,
- etc.

This layer should drive registries, campaigns, rooming priorities, and roadmap ranking.

### F. Closed-Loop Completion Tracking
The system must not stop at Ã¢â‚¬Å“eligible.Ã¢â‚¬Â
Plan closed-loop tracking for:
- ordered,
- scheduled,
- completed,
- resulted,
- billed,
- paid,
- denied / adjusted,
- and follow-up needed.

This is critical for mammograms, LDCT, DEXA, colon screening, vaccines, labs, hospital follow-up, and chronic monitoring.

### G. Visit Stack Builder
Plan visit-specific stack suggestions such as:
- AWV + ACP + depression + alcohol + obesity + CVD counseling + G2211,
- diabetes follow-up + A1c + UACR + lipids + retinal screening + foot exam reminders,
- chronic longitudinal visit + G2211 + tobacco counseling + PHQ/GAD + vaccine opportunities,
- post-hospital follow-up + TCM + med reconciliation + pending test follow-up.

These should reflect payer rules, time rules, documentation rules, and expected value.

### H. Staff Routing / Workflow Ownership
Plan explicit routing of each opportunity to the right actor:
- provider,
- MA,
- nurse,
- front desk,
- referral coordinator,
- biller,
- office manager.

Do not make the entire system provider-centric.

### I. Detected Ã¢â€ â€™ Documented Ã¢â€ â€™ Billed Ã¢â€ â€™ Paid Reconciliation
Plan dashboards and logging that can show leakage across the funnel:
- detected,
- surfaced,
- accepted,
- documented,
- billed,
- paid,
- denied,
- adjusted,
- dismissed,
- deferred.

This must help identify whether leakage is due to detection gaps, workflow drops, documentation failure, modifier failure, payer behavior, or staff bottlenecks.

### J. Payer-Specific Logic
Plan stronger Medicare / commercial / Medicaid / Medicare Advantage separation where appropriate.
This must include:
- preventive logic,
- modifier 25,
- modifier 33,
- G2211,
- vaccine administration pathways,
- screening cost-share logic,
- and payer-specific suppression or warnings.

### K. Medication Monitoring / FDA / Safety Expansion
The existing ideas around medication-list-driven monitoring should be expanded into a real planning module.
Plan how active medications plus current monitoring references can drive:
- overdue monitoring labs,
- due-soon reminders,
- monitoring bundles,
- recall / safety checks,
- and staff prep tasks.

### L. Campaign Mode / Registry Mode
Plan quarterly or monthly campaign workflows such as:
- Medicare AWV push,
- hypertension optimization campaign,
- diabetes registry cleanup,
- immunization catch-up,
- tobacco cessation documentation push,
- behavioral health screening catch-up,
- quarter-end fast-cash campaign.

These campaigns should be ranked using expected net value and time-to-cash.

### M. Office Manager / Admin ROI Layer
Plan an approval-facing and management-facing view showing:
- projected added receipts,
- likely bonus acceleration,
- top leakage families,
- top workflow bottlenecks,
- feature families by ROI,
- and implementation stages.

### N. Why-Not-Suggested Explainability
Plan how the system should explain why a high-value opportunity was **not** shown, for example:
- chart does not support it,
- already completed,
- payer ineligible,
- poor expected value,
- excessive denial risk unless documentation is improved,
- external result already on file,
- suppressed because standalone value is too weak,
- etc.

This is important for trust and testing.

---

## Data Assets Ã¢â‚¬â€ How You Must Use Them

### Annual diagnosis billing file
Treat the annual diagnosis billing file as a strategic planning dataset, not just a report.
Use it in your plan for:
- diagnosis-family ranking,
- opportunity scoring,
- denials / write-off proxy planning,
- rollout sequencing,
- template targets,
- campaign design,
- and quarterly bonus strategy.

### Bonus sample workbook
Use the bonus workbook to:
- identify what the current `/bonus` module may need,
- understand threshold / payout logic,
- identify mismatches between current assumptions and actual workbook behavior,
- and plan future bonus-aware scoring.

### Billing master lists / DHS code list / payer guides
Use these to shape:
- payer routing tables,
- code metadata tables,
- preventive coverage matrices,
- billing rule definitions,
- documentation checklists,
- and route / detector expansion priorities.

---

## Required Deliverables Inside Your Plan

Your appended plan in `running_plan.md` must include all of the following sections.

### 1. Verified Current State
A concise but concrete summary of what exists **today** in the actual repo:
- implemented billing components,
- partial billing components,
- blocked pieces,
- relevant adjacent systems already present,
- and architecture constraints.

### 2. Strategic Design Principles
State the guiding rules for implementation, including:
- compliance first,
- expected net value over gross billing,
- minimal provider friction,
- payer-aware logic,
- local-only PHI handling,
- explainability,
- and phased rollout.

### 3. Opportunity Matrix
Create a structured matrix or equivalent summary of major opportunity families, for example:
- chronic disease families,
- preventive / annual wellness,
- screenings,
- immunizations,
- counseling,
- care management,
- hospital follow-up,
- medication monitoring,
- telehealth / time-based services,
- procedure add-ons.

For each family, estimate or discuss:
- business value,
- implementation complexity,
- likely existing code reuse,
- dependency level,
- and proposed rollout order.

### 4. Phased Implementation Plan
Break the work into explicit phases, with checkboxes and file-level targets where possible.
Each phase should include:
- goal,
- why it belongs in that phase,
- major tasks,
- likely files / modules touched,
- dependencies,
- and suggested validation steps.

### 5. Data Model / Schema Plan
Identify what tables / columns / indexes / caches / audit models may need to be added or extended.
Separate:
- must-have now,
- good next,
- later / optional.

### 6. Route / UI / Workflow Plan
Identify:
- which billing pages should exist,
- which existing templates can be activated,
- what patient-chart widgets should do,
- what pre-visit and post-visit flows should do,
- what admin pages should track,
- and what new UI is worth building vs what can be deferred.

### 7. Testing Plan
Propose how to validate the billing capture system at multiple levels:
- unit tests,
- detector tests,
- payer-routing tests,
- migration tests,
- route tests,
- UI smoke tests,
- regression tests,
- and scenario-based test cases using synthetic patients.

### 8. Risk / Constraint List
Call out:
- compliance risks,
- data quality risks,
- payer ambiguity,
- documentation ambiguity,
- bonus-logic ambiguity,
- missing data sources,
- and anything that should block implementation until verified.

### 9. Immediate Next Step
Conclude with the **single best next implementation phase** to tackle first after planning is approved.

---

## Planning Style Requirements

When writing the plan:
- be highly specific,
- use repo paths when you can verify them,
- do not be vague,
- do not just restate business goals,
- convert ideas into implementation-oriented tasks,
- and distinguish clearly between:
  - already built,
  - partially built,
  - proposed new work,
  - and unresolved questions.

Use the existing `running_plan.md` style if one already exists.
If the file uses phase-based checklists, preserve that convention.

---

## Guardrails

Do **not** plan features that:
- rely on cloud PHI storage,
- send PHI to external APIs,
- depend on frontend frameworks the project does not use,
- replace the current stack unnecessarily,
- or recommend unsupported diagnosis coding.

Prefer:
- Flask,
- SQLAlchemy,
- SQLite,
- Jinja templates,
- background jobs already consistent with the repo,
- rule-driven detection,
- explainable scoring,
- and explicit migrations.

---

## Final Task

After completing your inspection and planning work:

1. Append a new section to `running_plan.md` titled something like:
   - `# Part 3 Ã¢â‚¬â€ Billing Capture Completion & Revenue Optimization Plan`
   or a better title that fits the fileÃ¢â‚¬â„¢s current style.
2. Include the full plan there.
3. Preserve all previous content.
4. Do not start broad implementation yet.
5. In your chat/output summary, briefly state:
   - what you verified,
   - what the biggest blockers are,
   - what the first recommended implementation phase is,
   - and that `running_plan.md` was appended.

