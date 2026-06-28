# Reviewer Guidelines

Practical guidance for university reviewers using the Marksheet Verifier. The
system produces **risk signals only**. A human reviewer always makes the final
decision. Nothing here authorises automatic rejection of a student.

> Every report carries: *"This is an MVP signal report, not final proof of tampering."*

---

## Document review workflow

1. Open the case from the Admin Dashboard and read the **risk label** and
   **risk score**.
2. Read the **Agentic Workflow Trace** to see what each agent (OCR, Metadata,
   Forensics, Rule Validation, Decision) found.
3. Look at the **detected fields** (board, roll number, total marks, percentage,
   result) and the **OCR text preview**.
4. Review **metadata warnings** and the **image-forensics** visualizations as
   *weak supporting context only*.
5. Decide a next step: approve, request more documents, request official
   verification, or escalate for manual review. Record the decision.

A missing field or a warning is usually a sign that the system could not read
something cleanly — not evidence that the document is fake.

---

## What to do for each risk level

- **verified / low risk** — No tampering signals, or only minor ones. Standard
  processing can continue. No manual review is required for the signals alone.
- **medium risk** — Some weak signals are present. A quick manual review is
  recommended before a decision. Re-read the OCR text and confirm the key fields.
- **needs_review** — Several weak signals were aggregated. Manual review is
  recommended. Consider requesting official verification if the document is
  decision-critical.
- **high risk** — Multiple stronger signals. Prioritise manual review and
  request official verification from the issuing board / DigiLocker / NAD before
  relying on the document.
- **unable_to_verify** — The document could not be analysed automatically (for
  example, OCR produced little readable text). Request a clearer re-upload or an
  official copy. This is **not** a negative finding about the student.

In all cases the recommendation is a workflow suggestion, never an automatic
admission decision.

---

## How to interpret OCR confidence

OCR confidence (0–100) is the average certainty of the text-recognition engine,
not a measure of authenticity.

- **High (about 80–100)** — text was read cleanly; detected fields are likely
  reliable.
- **Moderate (about 60–80)** — some text may be misread; double-check key fields
  such as roll number, total marks, and percentage against the OCR preview.
- **Low (below 60)** — the scan/photo is hard to read. Low confidence often
  means a poor image (glare, blur, low resolution), not tampering. Request a
  clearer re-upload before drawing conclusions.

---

## How to interpret metadata warnings

Metadata warnings (for example "editing software detected", "CreateDate and
ModifyDate mismatch", "missing metadata dates", "suspicious PDF producer") are
**weak evidence only**.

- Editing-software tags (Photoshop, Canva, GIMP, Illustrator) can appear because
  a student legitimately cropped, rotated, or compressed a scan, or because a
  scanning/phone app added the tag.
- Date mismatches and missing dates happen routinely when files are forwarded,
  re-saved, or exported.
- A metadata warning is a reason to look more closely, never proof of tampering.

If metadata shows editing software, do not reject the document. Note the signal,
read the rest of the evidence, and if the case is decision-critical, request
official verification.

---

## How to interpret image forensics

Image/pixel forensics (ELA, edge map, sharpness map, noise map, anomaly heatmap)
are **weak signals only**. Compression, scanning, mobile-camera capture,
screenshots, WhatsApp forwarding, and PDF conversion all create artefacts that
look like "tampering" to these algorithms.

- A higher anomaly score means "a human may want to look at the highlighted
  regions", not "this document is forged".
- Pixel forensics are never proof. Treat them as a pointer for where to look.
- Official verification is far stronger than any pixel analysis.

---

## When to request a re-upload

Request a clearer re-upload when:

- OCR confidence is low and key fields could not be read,
- the status is `unable_to_verify`,
- the image is cropped, rotated, glare-affected, or very low resolution.

A re-upload request is a quality step, not an accusation.

---

## When to request official verification

Request official verification (issuing board, DigiLocker, NAD) when:

- the case is `high` risk or decision-critical,
- multiple independent signals point to a possible inconsistency,
- a marks/percentage inconsistency was flagged by rule validation,
- you need certainty rather than a signal.

Official verification is the strongest form of confirmation and outweighs every
signal this system produces.

---

## When to escalate to manual review

Escalate to a senior reviewer or committee when:

- the status is `needs_review` or `high`,
- automated signals conflict with each other,
- the student disputes the result,
- the decision has significant consequences.

The goal of the system is to route the right cases to the right humans — not to
decide on its own.
