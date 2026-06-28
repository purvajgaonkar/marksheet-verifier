# Ethics & Limitations

Marksheet Verifier is an **MVP decision-support tool**, not an authority on
authenticity. This document states what the system may and may not be used for.

> **Every report carries this note:**
> *"This is an MVP signal report, not final proof of tampering."*

---

## Core principles

1. **Risk signals only — never an accusation.**
   The system outputs evidence-based statuses (`verified`, `low`, `medium`,
   `needs_review`, `high`, `unable_to_verify`). It must **never** be presented as
   "fraud detected", "fake document", "forged", or "student cheated".

2. **A human makes every final decision.**
   The risk score exists to help a reviewer *prioritise* which uploads to look at
   closely. It does not approve or reject anyone automatically.

3. **Official verification beats image analysis.**
   Verifying a marksheet against the issuing board / DigiLocker / NAD is far
   stronger evidence than any OCR, metadata, or pixel signal produced here.

4. **Protect student privacy.**
   Never commit real student marksheets. `uploads/`, `reports/`, and
   `forensic_outputs/` are git-ignored. Use the dummy generator for demos.

---

## Why each signal is *weak*

- **Metadata** (editor names, dates) can be misleading: scanner apps, phone
  cameras, WhatsApp forwarding, and ordinary re-saving all add software tags and
  change timestamps for completely innocent reasons.
- **OCR confidence** drops on poor scans, photos, and unusual fonts — low
  confidence means "hard to read", not "tampered".
- **Detected fields** use simple pattern matching and will miss unusual layouts.

---

## Limitations of Pixel-Level Forensics

Phase 4 adds image/pixel forensics (ELA-style difference, edge map, sharpness
map, noise map, and a combined anomaly heatmap). **These are weak signals that
can produce false positives. They do not prove tampering.**

Read this before interpreting any forensic output:

- **Compression creates artefacts.** JPEG re-compression (including every time an
  image is saved or sent) produces blocky differences that look like editing to
  Error Level Analysis — especially around sharp text and edges.
- **Scanned documents naturally show uneven noise and blur.** Scanner glass,
  lighting, and focus vary across a page, so sharpness and noise maps differ
  region to region even on a perfectly genuine document.
- **Screenshots and WhatsApp / messaging images are re-encoded.** Forwarding,
  resizing, and re-compression rewrite the pixels and can trigger every signal at
  once, with no editing involved.
- **PDF conversion and rendering change pixels.** Rendering a PDF page to an
  image introduces its own resampling and anti-aliasing.
- **Flat, high-contrast documents over-trigger variance-based signals.** Pure
  black text on pure white (e.g. a freshly generated PDF) maximises block-to-block
  sharpness/noise variance, which can read as "inconsistency" with no tampering.

Because of all this, the forensic anomaly score is:

- **Conservative** — typical clean documents stay low.
- **Capped** — it can add at most **+0.20** to the overall risk score, so it can
  *nudge* but never *drive* a case toward review.
- **Always paired with an explanation and limitations** in both the report and
  the UI.

### What pixel forensics is good for

A *review aid*. The anomaly heatmap can point a human reviewer toward a region
worth a closer manual look. It is a starting point for human judgement, **not**
evidence of wrongdoing.

### What pixel forensics must never be used for

- Automatically rejecting or flagging a student as dishonest.
- Any public statement that a document is "fake", "forged", or "tampered".
- Replacing official board / DigiLocker / NAD verification.

---

## Agentic AI Limitations

Phase 5 organises the analysis as a set of **local, rule-based agents** (OCR,
Metadata, Forensics, Rule Validation, Decision) coordinated by an Orchestrator.
This is an *agentic-style architecture*, not autonomous AI. Be clear about what
it is and is not:

- **The agents are local rule-based modules in this MVP.** There is no LLM and
  no external AI/API. Each agent is deterministic and explainable — you can read
  exactly why it produced a finding.
- **Agents do not make admission decisions.** The Decision Agent produces a
  *recommendation* and a `human_review_required` flag, never an approval or
  rejection.
- **Human review is required for elevated-risk cases.** The workflow is designed
  to route `medium` / `needs_review` / `high` / `unable_to_verify` cases to a
  person, not to act on them automatically.
- **Agent outputs are evidence summaries, not proof.** The trace aggregates weak
  signals (OCR confidence, metadata flags, pixel forensics, field rules). None of
  these — alone or combined — proves a document was tampered with.
- **Official verification remains stronger than any agent signal.** Verifying
  against the issuing board / DigiLocker / NAD outweighs everything the local
  agents produce.
- **No "autonomous fraud judgment."** The system must never be described as an AI
  that "proved tampering" or "confirmed a fake". It surfaces review signals.

---

## RAG Assistant Limitations

Phase 6 adds a local Policy Assistant that answers reviewer questions using the
project's own documents (a local TF-IDF retriever + template answers; no LLM, no
external API). Use it as guidance, with these limits in mind:

- **The assistant is guidance only.** It helps reviewers understand the rules,
  ethics, and next steps — it does not make decisions.
- **Retrieved policy documents may be incomplete or out of date.** The answer is
  only as good as the `docs/` it indexes; after editing the docs, call
  `POST /rag/reindex`.
- **No final admission decision is made by the assistant.** It never approves or
  rejects a student.
- **Sources should be reviewed by a human.** Every answer cites the document
  chunks it used; open them to confirm the context.
- **High-stakes decisions require official verification.** Verifying against the
  issuing board / DigiLocker / NAD outweighs anything the assistant says.
- **Answers are extractive/templated, not authoritative interpretation.** The
  current local mode quotes policy text; it does not reason like a human expert.

---

## LLM Explanation Limitations

Phase 7 adds an **optional** Claude-powered explanation mode. When enabled, Claude
rephrases answers from the same retrieved policy context the local fallback uses.
It is convenience only, and these limits apply:

- **LLM explanations may be imperfect.** A language model can phrase things
  unclearly, omit a nuance, or over-summarise. Read the cited sources.
- **The LLM cannot confirm fraud.** It must not, and is instructed not to, call a
  document fake or forged or accuse a student. It explains weak risk signals only.
- **The LLM does not make final admission decisions.** It produces an explanation;
  a human reviewer decides.
- **It must use retrieved policy context and case evidence.** The system prompt
  forbids inventing policy and asks it to name the source documents it used.
- **The human reviewer is responsible for the final interpretation.** Treat the
  explanation as a starting point, not an authority.
- **Prompt-injection risk exists and is mitigated.** OCR text and the reviewer's
  question are treated as UNTRUSTED data, not instructions. The model is told to
  ignore any embedded instruction that tries to change its rules, the risk score,
  or the case status, and it cannot modify any stored data or decision.
- **No API key is required.** With no key (or the switch off), the app uses the
  local fallback — the LLM is never a hard dependency.

---

## Student-facing results and data handling (Phase 8)

Phase 8 separates the **student portal** from the **admin/reviewer portal**. This
separation is an ethics requirement, not just a UI choice:

- **Student-facing results must be limited.** Students see only a safe workflow
  status (submitted / processing / under review / verified / re-upload required /
  official verification required / closed) and a friendly message.
- **Internal risk scores must NOT be shown to students.** The risk score,
  forensics score, metadata warnings, agent trace, and AI explanation are
  admin-only. A student is never told their document "looks suspicious".
- **AI evidence is advisory.** Every automated signal assists the reviewer; none
  of it decides.
- **The human reviewer is responsible for the final decision.** Only the
  database-backed reviewer decision endpoint (a human action) changes a case
  outcome — the system never auto-decides.
- **Official verification is preferred for high-impact decisions.** When the
  outcome matters, request official board / DigiLocker / NAD verification rather
  than relying on signals.
- **Uploaded documents are sensitive data.** Store them carefully, never commit
  real student documents (`uploads/`, `reports/`, `forensic_outputs/`, and the
  database file are git-ignored), and use only dummy documents for demos.

---

## Authentication & access control (Phase 9)

Phase 9 puts the sensitive document workflow behind authentication and role-based
access control. The ethics rationale:

- **Students should not see internal AI risk scores.** Authenticated student
  views remain limited to safe statuses — the risk score, forensics score,
  metadata warnings, agent trace, and AI explanation are never returned to a
  student account.
- **Students can only see their own submissions.** Ownership is enforced
  server-side; one student cannot view another student's case (the API returns a
  generic "not found" rather than confirming a case exists).
- **Admin/reviewer access must be restricted.** Admin and reviewer tools are
  protected; a request with no token is rejected (401) and a student token is
  refused (403). Staff accounts are created server-side, never self-registered.
- **Authentication protects sensitive document workflows.** Uploaded marksheets
  contain personal data; gating upload, tracking, and review behind login reduces
  casual exposure.
- **AI remains advisory and human-reviewed.** Auth changes *who* can see what; it
  does not change the core principle — automated signals assist a human, and only
  a human reviewer's recorded decision changes a case outcome.
- **Secrets are configuration, not code.** `JWT_SECRET_KEY` and any API keys are
  read from the environment. `backend/.env` is git-ignored and the default dev
  secret must be replaced for any real deployment.

This is a student project: the auth layer is a reasonable baseline (hashed
passwords, signed JWTs, role checks) but is **not** a hardened production identity
system — there is no refresh-token rotation, rate limiting, account lockout,
password reset, or MFA.

---

## Deployment & data handling (Phase 10)

Production cleanup keeps the same ethical commitments and adds operational ones:

- **Uploaded documents may contain sensitive personal information** (names, roll
  numbers, marks, dates of birth). Treat every upload as private data.
- **Student-facing UI must not expose internal risk scores.** The risk score,
  forensics score, metadata warnings, agent trace, and AI explanation are
  admin/reviewer-only — never returned to a student account.
- **Admin-only AI evidence must be protected** behind authentication and role
  checks (no token → 401, student token → 403).
- **AI evidence is advisory.** Automated signals assist a human; they never
  decide. Only a human reviewer's recorded decision changes a case outcome.
- **Human review remains required**, especially before any high-impact action;
  official board / DigiLocker verification is stronger than any image signal.
- **Production deployments should use secure storage and access control:**
  object storage for uploaded files, PostgreSQL for data, HTTPS everywhere,
  strong `JWT_SECRET_KEY` / `SETUP_SECRET`, and CORS restricted to the real
  frontend origin. Secrets live in environment variables, never in git.
- **Upload safety:** size limits and an extension/content allow-list reduce the
  risk of malicious uploads, but this is not a substitute for a full antivirus /
  content-scanning pipeline in a real deployment.

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for the operational steps.

---

## Summary

| Signal | Strength | Can be wrong because… |
|--------|----------|------------------------|
| Official board / DigiLocker check | Strong | (authoritative) |
| Metadata flags | Weak | re-saving, scanners, phone apps |
| OCR confidence / fields | Weak | scan quality, layout, fonts |
| Pixel forensics (ELA/noise/blur/heatmap) | Weakest | compression, scanning, messaging apps, PDF conversion |

When signals conflict or a case looks unusual, the correct action is **human
review and official verification — never an automated accusation.**
