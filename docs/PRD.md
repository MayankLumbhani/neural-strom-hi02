# Product Requirements Document (PRD)

**Project:** neural-storm-hi02, Multilingual Citizen Grievance Chatbot
**Event:** Neural Storm 2026, problem statement HI-02
**Status:** Design stage. Nothing here is implemented yet. Requirement status is tracked in `docs/TASKS.md`.
**Demo setting:** a fictional city, "Furfuri Nagar Municipal Corporation" (FMC). All data is synthetic.

---

## 1. Overview

A chatbot that lets a citizen file a civic complaint by typing in their own language. English, Hindi, Gujarati and Hinglish are fully tested (Tier 1), and seven more major Indian languages are supported experimentally (Tier 2). The system detects the language, understands the complaint, routes it to the correct municipal department, creates a ticket, and keeps the citizen informed until resolution. Department officers get a dashboard to work tickets, and overdue tickets escalate automatically.

**One-line pitch:** File a complaint in your own language, get it routed to the right department automatically, and track it until it is resolved.

## 2. Problem

Citizens who want to report a broken streetlight, a water outage or uncollected garbage face three failures:

1. **Language barrier.** Forms and portals are mostly in English or Hindi, and many people write in Gujarati or mix languages ("mere ghar ke bahar paani nahi aa raha 3 din se").
2. **Wrong routing.** The citizen must pick a category or department. Wrong picks cause complaints to bounce between offices or be ignored.
3. **No visibility.** After filing, the citizen cannot easily tell who is handling the complaint or whether anything has happened. Stuck tickets go unnoticed by management.

## 3. Goals and non-goals

### Goals
- G1. Let a citizen file a complaint with a single natural-language message, no forms or dropdowns.
- G2. Route complaints to the right department with a measured, reported accuracy.
- G3. Ask for missing information (department confusion, missing location) at filing time instead of guessing.
- G4. Give the citizen a ticket ID and a way to check status in their own language.
- G5. Escalate stale tickets automatically and give officers a working dashboard with basic analytics.
- G6. Be deployable, documented and demonstrably scalable by design (see `docs/ARCHITECTURE.md`).

### Non-goals (this version)
- Integration with any real government system or real citizen data.
- Languages outside the registry in section 5 (for example Urdu, Odia, Assamese) and romanized text in any language other than Hindi.
- Mobile apps, SMS or WhatsApp delivery.
- Payments, document uploads, photo-based complaints.
- Legal guarantees about resolution times. SLAs are configurable demo values.

## 4. Personas

| Persona | Description | Key need |
|---|---|---|
| **Citizen** (primary) | Resident reporting a civic issue. May be more comfortable in Gujarati or Hinglish than English. Not technical. | File fast, in my language, and know what happens next |
| **Department officer** | Staff member of one department (for example Water Supply). | See my department's tickets, update status, avoid missing deadlines |
| **Nodal admin** | Senior officer overseeing all departments. | See all tickets, escalations and department performance |

## 5. Scope

**Languages** are defined in one language registry. Support is split into two tiers so that every claim matches what has actually been verified.

| Language | Code | Tier | Status |
|---|---|---|---|
| English | `en` | 1 | Verified: full dataset, hand-written test set, real metrics |
| Hindi | `hi` | 1 | Verified |
| Gujarati | `gu` | 1 | Verified |
| Hinglish (romanized Hindi) | `hinglish` | 1 | Verified |
| Marathi | `mr` | 2 | Experimental |
| Bengali | `bn` | 2 | Experimental |
| Tamil | `ta` | 2 | Experimental |
| Telugu | `te` | 2 | Experimental |
| Kannada | `kn` | 2 | Experimental |
| Malayalam | `ml` | 2 | Experimental |
| Punjabi | `pa` | 2 | Experimental |

Tier 2 means: reply templates are machine-translated, datasets are smaller and LLM-drafted, and the test sets are small and not checked by native speakers. Tier 2 results are always reported separately and labelled unverified.

**Not supported now:** Urdu and other right-to-left scripts, Odia, Assamese, and romanized text in any language other than Hindi.

**Departments (9):**

| Code | Department | Typical complaints |
|---|---|---|
| WATER | Water Supply | No water, low pressure, dirty water, pipe leakage |
| ROADS | Roads and Infrastructure | Potholes, damaged roads, broken footpaths |
| SANITATION | Sanitation and Waste | Garbage not collected, overflowing bins, dead animals |
| ELECTRICITY | Electricity | Power cuts, damaged poles or wires, transformer issues |
| STREETLIGHT | Street Lights | Light not working, flickering, always on during day |
| DRAINAGE | Drainage and Sewage | Blocked drain, overflowing sewage, waterlogging |
| HEALTH | Public Health | Mosquito breeding, stray animals, unhygienic food stalls |
| TAX | Property Tax and Billing | Wrong bill, payment not reflected, tax queries |
| OTHER | General or Unclear | Anything that fits no department, routed to the nodal admin |

**Ticket statuses:** Filed, Assigned, In Progress, Resolved, Escalated.

## 6. User stories

Priority: **P0** = must have for the MVP, **P1** = should have, **P2** = stretch.

### Citizen
| ID | Story | Priority |
|---|---|---|
| US-01 | As a citizen, I can type my complaint in any supported language (section 5) and the bot understands it. | P0 |
| US-02 | As a citizen, I get a reply in the same language I wrote in. If my language is not supported, I get a reply in English and Hindi. | P0 |
| US-03 | As a citizen, when the bot is unsure of the department it asks me a short question or offers choices, instead of guessing. | P0 |
| US-04 | As a citizen, if I did not say where the problem is, the bot asks for the location. | P0 |
| US-05 | As a citizen, I receive a ticket ID, the assigned department and a confirmation of what was filed. | P0 |
| US-06 | As a citizen, I can send my ticket ID in chat (or use a status page) and see its status and history. | P0 |
| US-07 | As a citizen, I can optionally leave a contact number so the department can reach me. | P1 |
| US-08 | As a citizen, I can speak my complaint instead of typing it. | P2 |

### Officer
| ID | Story | Priority |
|---|---|---|
| US-10 | As an officer, I can log in and see only my department's tickets. | P0 |
| US-11 | As an officer, I can update a ticket's status and add a note, and the citizen sees the change. | P0 |
| US-12 | As an officer, I can filter and search tickets by status, date and keyword. | P1 |

### Admin
| ID | Story | Priority |
|---|---|---|
| US-20 | As an admin, I can see all tickets across departments. | P0 |
| US-21 | As an admin, I can see tickets that were auto-escalated. | P0 |
| US-22 | As an admin, I can see analytics: complaints per department, status breakdown, average resolution time, language mix. | P1 |

### System
| ID | Story | Priority |
|---|---|---|
| US-30 | The system escalates tickets that have not progressed within a department's SLA window. | P0 |
| US-31 | The system exposes health and readiness endpoints and structured logs. | P0 |

## 7. Functional requirements

**Chat and language**
- FR-01. The chat endpoint accepts free text up to a configured maximum length.
- FR-02. The system detects the script and language using the language registry. Devanagari text is disambiguated between Hindi and Marathi. Latin-script text is classified as English or Hinglish by a heuristic. If the language is unknown or unsupported, the reply is in English and Hindi.
- FR-03. All fixed system replies (confirmations, status labels, errors, prompts) come from per-language templates, not from an LLM. Tier 2 templates are machine-translated and are flagged as such in the template files and the documentation.

**Understanding**
- FR-10. The system classifies each complaint into one of the 9 departments and returns a confidence score.
- FR-11. Confidence is compared with two configurable thresholds:
  - at or above the high threshold: accept the department,
  - between the thresholds: ask the citizen to confirm, offering the top-2 departments as quick replies,
  - below the low threshold: ask an open clarifying question, then offer all departments as quick replies if still unclear.
- FR-12. The system extracts a free-text location (area, landmark, ward or street) from the message. If none is found, it asks for it.
- FR-13. Messages that look like a ticket ID are treated as status lookups, not complaints.
- FR-14. Greetings and help requests receive a short guidance message with examples.

**Ticketing**
- FR-20. A ticket is created only when a department and a location are known.
- FR-21. A ticket has a human-friendly ID (for example `FMC-261030-7K3F`), the original complaint text, the language, the department, the location, a status, timestamps and a history of events.
- FR-22. Status transitions are validated (see `docs/ARCHITECTURE.md`). Invalid transitions return an error.
- FR-23. Every change to a ticket records an event with who or what changed it, and an optional note.
- FR-24. A public status lookup by ticket ID returns status, department, timestamps and public notes only, never internal data.

**Escalation**
- FR-30. A scheduled job finds tickets whose time in the current status exceeds the department's SLA and marks them Escalated, recording an event.
- FR-31. SLA windows are configuration. A demo mode shortens them to minutes so escalation can be shown in the video.

**Officer and admin**
- FR-40. Officers authenticate with username and password and receive a token.
- FR-41. Officers see and update only their own department's tickets. Admins see everything.
- FR-42. An analytics endpoint returns counts by department, by status and by language, and average resolution time.

**Platform**
- FR-50. `GET /health` (liveness) and `GET /ready` (database and model loaded).
- FR-51. Per-IP rate limiting on public endpoints.
- FR-52. Consistent JSON error format with a request ID.

## 8. Non-functional requirements

Values below are **targets to design for and verify**, not results. Actual measurements are recorded in `ml/reports/` and `loadtests/`.

| Area | Requirement | Target |
|---|---|---|
| Accuracy | Macro-F1 of the MuRIL classifier on the hand-written evaluation set (Tier 1 languages) | At least 0.85, and above the TF-IDF baseline |
| Latency | p95 latency of the chat endpoint on one CPU instance | Under 1 second, measured by load test |
| Throughput | Sustained requests per second on one CPU instance | Measured and reported, not assumed |
| Scalability | API is stateless so replicas scale horizontally | Verified by running two replicas in the load test if time permits |
| Availability | Health and readiness checks | Both endpoints present |
| Security | Secrets in environment only, hashed passwords, input validation, rate limiting, role checks | No secrets in repo |
| Privacy | No real citizen data. Complaint text is not written to logs. Contact numbers are optional and masked in logs. | Enforced in code review |
| Accessibility | Keyboard use, labels, sufficient contrast, readable on mobile | Basic WCAG-aligned checks |
| Maintainability | Layered code, typed, linted, tested, documented | CI green on every commit |

## 9. Conversation flows

### 9.1 Filing a complaint (happy path)
1. Citizen: "mere ghar ke bahar paani nahi aa raha 3 din se, Shivaji Nagar mein"
2. System detects Hinglish, classifies WATER with high confidence, extracts location "Shivaji Nagar".
3. System creates the ticket and replies in Hinglish with the ticket ID, department and location.

### 9.2 Missing location
1. Citizen: "Streetlight is not working for a week"
2. System classifies STREETLIGHT confidently but finds no location.
3. System asks: "Which area or street is this in?"
4. Citizen answers, system creates the ticket.

### 9.3 Ambiguous complaint
1. Citizen: "gandhi road pe bahut problem hai"
2. Confidence is low. System asks what the problem is and offers quick replies (Water, Roads, Sanitation, Electricity, Other).
3. Citizen picks one or describes it further. System continues as above.

### 9.4 Status check
1. Citizen sends `FMC-261030-7K3F`.
2. System replies with the current status, department, last update and notes, in the citizen's language.

## 10. Success metrics

| Metric | How it is measured | Where reported |
|---|---|---|
| Routing accuracy and macro-F1, MuRIL vs baseline (Tier 1) | Evaluation script on the hand-written set (about 100 to 150 messages across the four Tier 1 languages, including ambiguous ones) | `ml/reports/`, README, MODEL_CARD |
| Per-language metrics for Tier 2 | Evaluation on about 20 LLM-assisted messages per language, labelled unverified and reported in a separate table | `ml/reports/`, MODEL_CARD |
| Clarification behavior | Share of low-confidence evaluation messages that trigger a question rather than a wrong auto-route | `ml/reports/` |
| Latency and throughput | k6 or Locust load test against one instance | `loadtests/`, README |
| Escalation | Demonstrated live in the demo video with the short demo SLA | Demo video |
| Code quality | CI green, tests passing, lint and type checks clean | CI badge |

No impact statistic (for example "reduces resolution time by X%") is claimed unless it is measured.

## 11. Demo plan (for the video)

1. Problem in 20 seconds: a Gujarati speaker facing an English form.
2. Live chat: file a Gujarati complaint, a Hinglish complaint and an ambiguous one (clarification), then one in a Tier 2 language such as Tamil or Marathi, clearly shown as experimental.
3. Show the ticket ID and the department assigned.
4. Status check in chat.
5. Officer dashboard: update the ticket to In Progress, citizen sees the change.
6. Escalation: show a ticket auto-escalating using the short demo SLA.
7. Admin analytics view.
8. Results slide: classifier metrics vs baseline and the load test numbers.
9. Architecture and scale-out path, then the tech stack and the note that the project was built with AI assistance.

## 12. Judging criteria mapping

| Criterion (weight) | How this project addresses it |
|---|---|
| Technical Implementation (35%) | Fine-tuned multilingual model vs baseline with reported metrics, clarification logic, layered architecture, tests, CI, load test |
| Impact and Usefulness (25%) | Real, specific problem (language barrier, misrouting, no visibility), end-to-end flow including officers and escalation |
| README and Documentation (20%) | README, PRD, architecture, decisions, model card, API doc, runbook, scaling notes, screenshots |
| Demo and Presentation (20%) | Live deployed link, scripted video covering the full citizen and officer flow |

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Synthetic training data inflates accuracy | Separate hand-written evaluation set that is never trained on; report both results honestly |
| Hinglish and code-mixed text confuse the classifier | Include Hinglish heavily in training data; per-language metrics reveal weak spots |
| Tier 2 language quality cannot be verified without native speakers | Label Tier 2 as experimental, sample-check with native speakers where possible, report Tier 2 results separately from Tier 1 |
| Free LLM API rate limits or outage | LLM is optional for extraction; fall back to asking the citizen directly |
| Free hosting sleeps or has limited RAM | Host the model on Hugging Face Spaces; wake the app before judging; show a waking-up message in the UI |
| Too much scope for 5 days solo | Strict P0 first; stretch goals only after the core works; skip monitoring stack |
| Rule on building during the hackathon window | Organiser permission to start early is kept in writing; README notes the start date |

## 14. Open questions

- Final set of demo SLA values (proposal: Filed to Escalated after 3 minutes in demo mode, 48 hours in normal mode).
- Whether to include the voice input stretch goal. Decide after the core flow is deployed.
- Which Tier 2 languages can be sample-checked by native speakers (friends, classmates) before submission. Any language that cannot be checked stays labelled experimental.