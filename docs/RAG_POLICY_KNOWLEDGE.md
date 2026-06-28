# RAG Policy Knowledge

Core policy statements for the Marksheet Verifier. This document is part of the
local knowledge base the Policy Assistant retrieves from. It is written as
short, self-contained statements so each can be quoted as guidance.

> *"This is an MVP signal report, not final proof of tampering."*

---

## System limitations

- The system produces **risk signals only**. It does not prove that a document
  is genuine or tampered with.
- All detectors (OCR, metadata, pixel forensics, field rules) are **weak
  signals** that can be wrong for innocent reasons.
- The risk score is a transparent heuristic used to **prioritise** human review,
  not to make a decision.
- The system has no access to official records and cannot confirm a marksheet
  against the issuing board.

## Privacy rules

- Do not commit real student documents to source control. `uploads/`,
  `reports/`, and `forensic_outputs/` are git-ignored.
- Use only sample or dummy documents for demonstrations and testing.
- Do not store API keys in code. The MVP requires no API keys at all.
- Handle student documents as sensitive personal data and limit access to
  authorised reviewers.

## No automatic rejection policy

- The system must **never automatically reject or accuse a student**.
- A high risk label is a request for human attention, not a verdict.
- Only a human reviewer (or committee) may make an admission decision.

## Human-in-the-loop principle

- Every flagged case requires a human reviewer.
- The Decision Agent outputs a *recommendation* and a `human_review_required`
  flag — it does not act on them.
- The assistant and agents support reviewers; they do not replace them.

## Official verification is stronger than AI signals

- Verifying a marksheet against the issuing board, DigiLocker, or NAD is the
  strongest form of confirmation.
- When certainty matters, request official verification rather than relying on
  any signal from this system.
- Official verification outweighs OCR, metadata, and pixel-forensics signals.

## Metadata is weak evidence

- Editing-software tags, date mismatches, and missing dates have many innocent
  causes (scanning apps, phone cameras, forwarding, re-saving, PDF export).
- A metadata warning is a reason to look closer, never proof of tampering.

## Pixel forensics are weak evidence

- ELA, edge, sharpness, noise, and anomaly-heatmap outputs are review aids only.
- Compression, scanning, mobile capture, screenshots, and messaging-app
  re-encoding routinely create false positives.
- A higher anomaly score means "worth a human glance", not "forged".

## Risk labels and their meanings

- **verified** — No tampering signals detected by the automated checks (not an
  official confirmation against the board).
- **low** — Only minor signals; most likely fine. No manual review required for
  the signals alone.
- **medium** — Some weak signals; a quick manual review is recommended.
- **needs_review** — Several weak signals aggregated; manual review recommended.
- **high** — Multiple stronger signals; prioritise manual review and request
  official verification.
- **unable_to_verify** — The document could not be analysed automatically;
  request a clearer copy or official verification. Not a negative finding about
  the student.

## Approved wording

- Use: "risk signal", "possible inconsistency", "review recommended", "official
  verification recommended", "weak evidence only", "human reviewer decision
  required".
- Never use: "fraud detected", "fake document confirmed", "student cheated",
  "forged document proven".
