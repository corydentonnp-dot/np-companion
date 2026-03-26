# CareCompanion -- Master Test Plan

> **Generated:** 03-24-26
> **Purpose:** Defines what to test, in what order, and what "done" looks like for each feature.
> **Format:** Tier 1 (critical path first), Tier 2 (secondary features), Tier 3 (admin/edge cases)
> **Cross-reference:** FEATURE_REGISTRY.md for feature IDs; COVERAGE_MAP.md for file-level mapping.

---

## Tier 1 -- Critical Path (Test First)

These features represent the core clinical workflow. A regression here blocks the practice.

### TP-001: Authentication (F-001)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 1.1 | Valid login with username/password | Integration | Redirects to /dashboard, session active |
| 1.2 | Invalid password | Integration | Stays on /login, flash error shown |
| 1.3 | @login_required enforced on all protected routes | Unit | 302 redirect to /login for unauthenticated |
| 1.4 | Role-based access: MA cannot reach /admin/* | Integration | 403 returned |
| 1.5 | Role-based access: provider cannot reach /admin/users | Integration | 403 returned |
| 1.6 | Logout clears session | Integration | /dashboard returns 302 after logout |

### TP-002: Dashboard and Schedule (F-002)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 2.1 | Dashboard loads with schedule data | Integration | 200, schedule rows rendered |
| 2.2 | Empty schedule shows "No appointments" | Integration | 200, no errors |
| 2.3 | Schedule add endpoint validates required fields | Integration | 400 on missing patient_name |
| 2.4 | Active chart endpoint returns JSON | Integration | 200, JSON with expected keys |
| 2.5 | Double-booking detection flag | Unit | Flag raised when same slot/provider overlap |

### TP-003: Patient Chart (F-004)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 3.1 | Patient chart loads for known MRN | Integration | 200, tab structure visible |
| 3.2 | Patient chart 404 for unknown MRN | Integration | 404 or empty state |
| 3.3 | Patient roster loads | Integration | 200, list of patients |
| 3.4 | Chart scoped to current user | Integration | Other user's patients not visible (unless shared) |

### TP-004: Billing Engine (F-006)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 4.1 | Engine initializes with 27 detectors | Unit | len(engine._detectors) == 27 |
| 4.2 | G2211 detector fires for qualifying visit | Unit | Returns BillingOpportunity with code G2211 |
| 4.3 | AWV detector identifies initial vs subsequent | Unit | Correct CPT based on last AWV date |
| 4.4 | TCM detector respects 30-day window | Unit | No opportunity outside window |
| 4.5 | CCM detector checks enrollment + minutes | Unit | Opportunity only when enrolled + >= 20 min |
| 4.6 | Payer routing: Medicare vs Commercial | Unit | Different opportunities for same patient |
| 4.7 | Detector disabled via provider toggle | Unit | Category skipped, suppression logged |
| 4.8 | Full evaluate() with demo patient data | Integration | Returns non-empty list of opportunities |
| 4.9 | Deduplication: no duplicate opportunity_codes | Unit | evaluate() returns unique codes |
| 4.10 | Engine handles detector exception gracefully | Unit | Exception logged, other detectors still run |

### TP-005: Care Gap Detection (F-008)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 5.1 | Care gaps generated for patient missing screenings | Unit | Gap list non-empty |
| 5.2 | Addressed care gap disappears from active list | Integration | POST address removes from view |
| 5.3 | Dismissed care gap with reason | Integration | Suppression recorded |
| 5.4 | Care gap panel aggregates across patients | Integration | Panel view shows all active gaps |

### TP-006: Clinical Summary Parser (F-005)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 6.1 | Parse valid CDA XML into patient record | Unit | All patient fields populated |
| 6.2 | Parse XML with missing optional sections | Unit | No crash, fields are None/empty |
| 6.3 | Parse medications from XML | Unit | Correct medication list |
| 6.4 | Parse diagnoses with ICD-10 codes | Unit | Code format validated |

---

## Tier 2 -- Secondary Features

### TP-007: Bonus Dashboard (F-007)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 7.1 | Below threshold: no bonus, deficit grows | Unit | exceeded=False, deficit=difference |
| 7.2 | Above threshold: bonus = surplus * multiplier | Unit | Correct bonus_amount |
| 7.3 | Deficit carry-forward reduces surplus | Unit | Net surplus calculated correctly |
| 7.4 | Projection engine returns future quarters | Unit | first_bonus_quarter is a string date |
| 7.5 | Dashboard route loads | Integration | 200, all 7 sections present |
| 7.6 | Receipt entry via POST | Integration | 201 or redirect, data saved |
| 7.7 | Threshold confirmation toggle | Integration | threshold_confirmed updated |

### TP-008: Lab Tracking (F-009)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 8.1 | Add lab track entry | Integration | New LabTrack row created |
| 8.2 | Record lab result | Integration | LabResult linked to LabTrack |
| 8.3 | Status calculation: critical/overdue/due_soon/on_track | Unit | Correct status based on dates |
| 8.4 | Archive sets is_archived flag | Integration | Row no longer in active view |

### TP-009: Time Tracking (F-017)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 9.1 | Timer page loads (authenticated) | Integration | 200 |
| 9.2 | Room widget loads (no auth) | Integration | 200, no login redirect |
| 9.3 | Room toggle endpoint (no auth) | Integration | 200 |
| 9.4 | TimeLog created on timer save | Integration | Row in DB |

### TP-010: Orders (F-018)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 10.1 | Master order list loads | Integration | 200 |
| 10.2 | Create order set | Integration | New OrderSet row |
| 10.3 | Fork order set | Integration | Copy created with new user_id |
| 10.4 | Order execution logged | Integration | OrderExecution row created |

### TP-011: CCM Management (F-025)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 11.1 | Enroll patient in CCM | Integration | CCMEnrollment created |
| 11.2 | Log CCM time entry | Integration | CCMTimeEntry with minutes |
| 11.3 | Bill CCM only when threshold met | Integration | No bill < 20 min |

### TP-012: TCM Workflow (F-026)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 12.1 | Create TCM watch entry | Integration | TCMWatchEntry with discharge_date |
| 12.2 | TCM expires after 30 days | Unit | Status = expired beyond window |
| 12.3 | Contact deadline is 2 business days | Unit | Correct date calculation |

### TP-013: Medication Monitoring (F-013)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 13.1 | Monitoring rules generate schedules | Unit | MonitoringSchedule rows created |
| 13.2 | Override applied correctly | Unit | Schedule reflects override |
| 13.3 | REMS tracking for high-risk drugs | Unit | REMSTrackerEntry created |

### TP-014: Calculators (F-024)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 14.1 | BMI calculator with known inputs | Unit | Correct BMI value |
| 14.2 | Calculator result saved | Integration | CalculatorResult row |
| 14.3 | Auto-prefill from patient data | Integration | Fields pre-populated |

---

## Tier 3 -- Admin and Edge Cases

### TP-015: Revenue Reporting (F-010)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 15.1 | Revenue summary endpoint | Integration | JSON with totals |
| 15.2 | Dx family breakdown | Integration | Non-empty categories |

### TP-016: Admin Panel (F-034)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 16.1 | Admin dashboard requires admin role | Integration | 403 for non-admin |
| 16.2 | User management CRUD | Integration | Create/edit/disable users |
| 16.3 | Audit log shows recent actions | Integration | AuditLog rows displayed |
| 16.4 | Practice config editable | Integration | Settings saved to DB |

### TP-017: On-Call and Handoff (F-020)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 17.1 | Create on-call note | Integration | OnCallNote row |
| 17.2 | Public handoff link is accessible without auth | Integration | 200 on /oncall/handoff/<token> |
| 17.3 | Expired handoff link shows error | Integration | 403 or 410 |

### TP-018: Telehealth Logging (F-031)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 18.1 | Log telehealth encounter | Integration | CommunicationLog row |
| 18.2 | Billing check returns applicable codes | Integration | JSON with CPT suggestions |

### TP-019: Note Reformatter (F-033)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 19.1 | Reformat a note successfully | Integration | Reformatted text returned |
| 19.2 | Discarded items logged to ReformatLog | Unit | JSON field populated |

### TP-020: Notifications (F-022)
| # | Test Case | Type | Pass Criteria |
|---|-----------|------|---------------|
| 20.1 | Notification created on event | Unit | Notification row |
| 20.2 | Mark notification as read | Integration | read_at timestamp set |
| 20.3 | No PHI in Pushover payload | Unit | Only counts in message body |

---

## Execution Priority

Run in this order during a full QA session:
1. **Smoke test** (scripts/smoke_test.py) -- app starts, DB connects, all blueprints loaded
2. **Tier 1** -- TP-001 through TP-006
3. **Tier 2** -- TP-007 through TP-014
4. **Tier 3** -- TP-015 through TP-020
5. **Billing engine deep dive** -- test_billing_engine.py (all 27 detectors)
6. **PHI scrubbing** -- test_phi_scrubbing.py
7. **E2E UI flows** -- tests/e2e/test_ui_flows.py (if Playwright available)

---

## Pass/Fail Criteria

- **Full Pass:** All Tier 1 + Tier 2 tests green, zero regressions from last run
- **Conditional Pass:** Tier 1 all green, Tier 2 has < 3 failures with tickets filed
- **Fail:** Any Tier 1 test fails, or > 5 total failures across all tiers
