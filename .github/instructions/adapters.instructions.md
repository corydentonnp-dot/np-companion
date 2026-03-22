---
applyTo: "adapters/**/*.py"
---

# Adapter Rules

## Purpose
Adapters isolate EHR-specific logic from the core application. The app talks to `BaseAdapter` — never directly to Amazing Charts, FHIR, or any specific EHR.

## Pattern
- `adapters/base.py` defines the `BaseAdapter` ABC with all required methods.
- Each EHR gets its own adapter file (e.g., `adapters/amazing_charts.py`).
- `get_adapter()` factory returns the correct adapter based on config.
- Routes and utils call `get_adapter()` — never import a specific adapter directly.

## Adding a New Adapter
1. Create `adapters/{ehr_name}.py`.
2. Inherit from `BaseAdapter`.
3. Implement ALL abstract methods — the ABC enforces this.
4. Register in `get_adapter()` factory.
5. Add tests in `tests/test_adapter_{ehr_name}.py`.

## SaaS Readiness
- This is the critical boundary for multi-EHR support.
- Future adapters: FHIR R4, HL7v2, direct database connectors.
- `ClinicalData` TypedDicts in `base.py` define the canonical data format — all adapters must output this format.
- Never add Amazing Charts-specific fields to `ClinicalData` — keep it EHR-agnostic.

## Rules
- Never import desktop packages (`pyautogui`, `win32gui`, etc.) in adapter files.
- Adapters handle data transformation only — no UI, no routes, no notifications.
- All adapter methods must be safe to call from both desktop agent and web routes.
