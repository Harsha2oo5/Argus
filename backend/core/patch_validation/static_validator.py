import os
import logging
from typing import List
from backend.core.analysis.engine import AnalysisEngine
from backend.core.analysis.schemas import NormalizedFinding
from backend.core.patch_validation.validation_models import StaticReanalysisResult
from backend.core.patch_validation.exceptions import StaticAnalysisError

logger = logging.getLogger("backend.patch_validation.static_validator")


class StaticValidator:
    """Re-runs the static analysis pipeline to compare findings before and after patch application."""

    def __init__(self) -> None:
        self.engine = AnalysisEngine()

    def validate_patch(
        self,
        original_file_path: str,
        patched_file_path: str,
        original_finding: dict
    ) -> StaticReanalysisResult:
        """
        Compare static findings between original and patched versions.

        Parameters
        ----------
        original_file_path : Absolute path to the original source file.
        patched_file_path : Absolute path to the patched source file.
        original_finding : Dict representing the target finding being resolved.
        """
        if not os.path.exists(original_file_path):
            raise StaticAnalysisError(f"Original file not found: {original_file_path}")
        if not os.path.exists(patched_file_path):
            raise StaticAnalysisError(f"Patched file not found: {patched_file_path}")

        try:
            with open(original_file_path, "r", encoding="utf-8", errors="ignore") as f:
                original_code = f.read()
            with open(patched_file_path, "r", encoding="utf-8", errors="ignore") as f:
                patched_code = f.read()

            # Run analysis before and after patch application
            ext = os.path.splitext(original_file_path)[1].replace(".", "") or "cpp"
            
            before_findings = self.engine.analyze_plain(original_code, extension=ext)
            after_findings = self.engine.analyze_plain(patched_code, extension=ext)

            # Check if the target bug was removed
            target_rule_id = original_finding.get("rule_id")
            target_line = original_finding.get("line_number")

            # Check if target bug exists in 'after' list (matching by rule_id and line alignment)
            bug_still_present = False
            for f in after_findings:
                if f.rule_id == target_rule_id:
                    # Allow slight line shifting check (e.g. within 5 lines offset)
                    if target_line is None or f.line_number is None or abs(f.line_number - target_line) <= 5:
                        bug_still_present = True
                        break

            original_bug_removed = not bug_still_present

            # Identify if new warnings/bugs were introduced by the patch
            new_findings: List[NormalizedFinding] = []
            for af in after_findings:
                # Is af a new finding? Compare with before findings
                is_new = True
                for bf in before_findings:
                    if af.rule_id == bf.rule_id:
                        if af.line_number is not None and bf.line_number is not None:
                            # If they are at similar lines with similar descriptions, it's not new
                            if abs(af.line_number - bf.line_number) <= 5:
                                is_new = False
                                break
                        else:
                            is_new = False
                            break
                if is_new:
                    # Double check it is not the original finding being matched
                    if af.rule_id == target_rule_id:
                        # If it is the original target bug, we already count it under original_bug_removed
                        pass
                    else:
                        new_findings.append(af)

            warning_delta = len(after_findings) - len(before_findings)

            details_msg = (
                f"Static Reanalysis: original_bug_removed={original_bug_removed}, "
                f"before_count={len(before_findings)}, after_count={len(after_findings)}, "
                f"new_introduced={len(new_findings)}"
            )
            logger.info(details_msg)

            return StaticReanalysisResult(
                success=True,
                original_bug_removed=original_bug_removed,
                new_findings_count=len(new_findings),
                warning_delta=warning_delta,
                before_findings_count=len(before_findings),
                after_findings_count=len(after_findings),
                details=details_msg
            )

        except Exception as e:
            logger.error(f"Static validation reanalysis failed: {e}")
            raise StaticAnalysisError(f"Static analysis failed during verification: {e}") from e
