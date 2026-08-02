import logging
from backend.core.patch_validation.validation_models import ValidationMetrics

logger = logging.getLogger("backend.patch_validation.quality_metrics")


class QualityMetricsCalculator:
    """Computes multidimensional validation scores and code quality metrics."""

    def compute_metrics(
        self,
        compilation_success: bool,
        syntax_success: bool,
        bug_removed: bool,
        regression_success: bool,
        new_bug_count: int,
        warning_delta: int,
        lines_changed: int,
        patch_size: int,
        duration_ms: float,
    ) -> ValidationMetrics:
        """
        Evaluate metrics and calculate an overall quality score.

        Returns
        -------
        ValidationMetrics object.
        """
        # Strict rules: compilation and basic syntax are absolute prerequisites
        if not compilation_success or not syntax_success:
            score = 0.0
        else:
            score = 0.0

            # 1. Bug removal (Weight: 0.4)
            if bug_removed:
                score += 0.4

            # 2. Regression verification (Weight: 0.3)
            if regression_success:
                score += 0.3

            # 3. Patch simplicity bonus (Weight: 0.1)
            # Penalise excessively large patches; ideal patch touches few lines
            simplicity_bonus = 0.1
            if lines_changed > 50:
                simplicity_bonus = 0.02
            elif lines_changed > 20:
                simplicity_bonus = 0.05
            elif lines_changed > 10:
                simplicity_bonus = 0.08

            score += simplicity_bonus

            # 4. Code regressions penalties (Deductions)
            # New bugs introduced are highly penalized
            if new_bug_count > 0:
                score -= min(0.4, 0.15 * new_bug_count)

            # Warning delta penalty
            if warning_delta > 0:
                score -= min(0.1, 0.01 * warning_delta)

            # Ensure final score range [0.0, 1.0]
            score = max(0.0, min(1.0, round(score, 3)))

        bug_removal_rate = 1.0 if bug_removed else 0.0

        logger.info(f"Computed validation score: {score} (compilation={compilation_success}, bug_removed={bug_removed})")

        return ValidationMetrics(
            compilation_success=compilation_success,
            syntax_success=syntax_success,
            bug_removal_rate=bug_removal_rate,
            regression_success=regression_success,
            new_bug_count=new_bug_count,
            warning_delta=warning_delta,
            lines_changed=lines_changed,
            patch_size=patch_size,
            duration_ms=duration_ms,
            score=score
        )
