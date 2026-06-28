"""
rule_validation_agent.py
========================

RuleValidationAgent — deterministic, local, explainable checks on the OCR
output. No AI, no external calls. It turns the detected fields into a small set
of pass/warn rules that become human-readable evidence for the DecisionAgent.

These are sanity checks, NOT proof of anything. A missing field usually just
means OCR could not read it, not that the document is fake.
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent


class RuleValidationAgent(BaseAgent):
    name = "Rule Validation Agent"

    def execute(self, context: dict) -> dict:
        fields = context.get("fields", {}) or {}

        findings: list[str] = []
        warnings: list[str] = []
        rules_total = 0
        rules_passed = 0

        # Rule 1: board identified
        rules_total += 1
        if fields.get("board", "unknown") != "unknown":
            rules_passed += 1
            findings.append(f"Examination board identified: {fields['board']}.")
        else:
            warnings.append("Examination board could not be identified.")

        # Rule 2: roll / seat number present
        rules_total += 1
        if fields.get("roll_number"):
            rules_passed += 1
            findings.append("Roll/seat number is present.")
        else:
            warnings.append("Roll/seat number not detected.")

        # Rule 3: total marks present
        rules_total += 1
        if fields.get("total_marks"):
            rules_passed += 1
            findings.append(f"Total marks present: {fields['total_marks']}.")
        else:
            warnings.append("Total marks not detected.")

        # Rule 4: percentage, if present, must be 0..100 (missing is acceptable)
        rules_total += 1
        percentage = fields.get("percentage")
        if percentage is None:
            rules_passed += 1
            findings.append("No percentage detected (not required).")
        else:
            try:
                value = float(percentage)
                if 0.0 <= value <= 100.0:
                    rules_passed += 1
                    findings.append(f"Percentage {value:g}% is within the valid range (0–100).")
                else:
                    warnings.append(f"Percentage {value:g}% is outside the valid range (0–100).")
            except (TypeError, ValueError):
                warnings.append("Percentage value could not be parsed.")

        # Rule 5: a result keyword (pass/fail/etc.) is present
        rules_total += 1
        if fields.get("result_keywords"):
            rules_passed += 1
            findings.append(f"Result keyword(s) present: {', '.join(fields['result_keywords'])}.")
        else:
            warnings.append("No pass/fail/result keyword detected.")

        # Rule 6 (only if totals look like "obtained/maximum"): reasonableness
        total_marks = fields.get("total_marks")
        if total_marks and "/" in str(total_marks):
            rules_total += 1
            try:
                obtained_str, maximum_str = str(total_marks).split("/")[:2]
                obtained = float(obtained_str.strip())
                maximum = float(maximum_str.strip())
                if maximum > 0 and 0.0 <= obtained <= maximum:
                    rules_passed += 1
                    findings.append(
                        f"Obtained marks {obtained:g} are within the maximum {maximum:g}."
                    )
                    # Optional cross-check against a stated percentage.
                    if percentage is not None:
                        try:
                            calc = obtained / maximum * 100.0
                            if abs(calc - float(percentage)) > 5.0:
                                warnings.append(
                                    f"Stated percentage ({percentage}%) differs from the marks "
                                    f"ratio (~{calc:.1f}%) by more than 5 points — possible inconsistency."
                                )
                            else:
                                findings.append(
                                    f"Percentage is consistent with the marks ratio (~{calc:.1f}%)."
                                )
                        except (TypeError, ValueError):
                            pass
                else:
                    warnings.append(
                        f"Obtained marks {obtained:g} are not within the maximum {maximum:g}."
                    )
            except (ValueError, ZeroDivisionError):
                warnings.append("Total marks could not be parsed as 'obtained/maximum'.")

        # Subject-level sum vs total: intentionally skipped — extracting reliable
        # per-subject marks from OCR is not dependable in this MVP.
        findings.append("Subject-level sum check skipped (not reliable from OCR in this MVP).")

        context["rule_validation"] = {
            "rules_total": rules_total,
            "rules_passed": rules_passed,
        }

        confidence = round(rules_passed / rules_total, 3) if rules_total else 0.0
        summary = (
            f"Basic academic document rules checked: {rules_passed}/{rules_total} passed, "
            f"{len(warnings)} warning(s)."
        )
        return {
            "summary": summary,
            "confidence": confidence,
            "findings": findings,
            "warnings": warnings,
        }
