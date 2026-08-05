import ast
import difflib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExecutionMetrics(BaseModel):
    planning_time_ms: float = 0.0
    context_retrieval_time_ms: float = 0.0
    graph_query_time_ms: float = 0.0
    vector_search_time_ms: float = 0.0
    patch_generation_time_ms: float = 0.0
    sandbox_execution_time_ms: float = 0.0
    total_execution_time_ms: float = 0.0
    repair_attempts: int = 0
    tokens_used: int = 0
    cost_estimate_usd: float = 0.0
    success_rate: float = 0.0
    patch_size_bytes: int = 0
    diff_accuracy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0


class PatchComparisonResult(BaseModel):
    exact_match: bool = False
    changed_lines: int = 0
    diff_accuracy: float = 0.0
    ast_similarity: float = 0.0
    semantic_similarity: float = 0.0


class PatchComparer:
    """
    Compares generated surgical diff patches against reference ground truth patches
    using AST structural tree distance and diff similarity ratio.
    """

    @staticmethod
    def compare_patches(generated_patch: str, ground_truth_patch: str) -> PatchComparisonResult:
        if not generated_patch or not ground_truth_patch:
            return PatchComparisonResult(
                exact_match=(generated_patch == ground_truth_patch),
                changed_lines=len(generated_patch.splitlines()) if generated_patch else 0,
                diff_accuracy=1.0 if generated_patch == ground_truth_patch else 0.0,
                ast_similarity=1.0 if generated_patch == ground_truth_patch else 0.0,
                semantic_similarity=1.0 if generated_patch == ground_truth_patch else 0.0
            )

        gen_clean = generated_patch.strip()
        ref_clean = ground_truth_patch.strip()

        exact = (gen_clean == ref_clean)

        # Diff Accuracy ratio using difflib SequenceMatcher
        matcher = difflib.SequenceMatcher(None, gen_clean, ref_clean)
        diff_acc = matcher.ratio()

        # Changed lines count
        gen_lines = [l for l in gen_clean.splitlines() if l.startswith("+") or l.startswith("-")]
        changed_count = len(gen_lines)

        # AST similarity comparison if code snippet is valid Python
        ast_sim = diff_acc
        try:
            gen_ast = ast.parse(gen_clean)
            ref_ast = ast.parse(ref_clean)
            gen_dump = ast.dump(gen_ast)
            ref_dump = ast.dump(ref_ast)
            ast_sim = difflib.SequenceMatcher(None, gen_dump, ref_dump).ratio()
        except Exception:
            pass

        return PatchComparisonResult(
            exact_match=exact,
            changed_lines=changed_count,
            diff_accuracy=round(diff_acc, 4),
            ast_similarity=round(ast_sim, 4),
            semantic_similarity=round((diff_acc + ast_sim) / 2.0, 4)
        )


class QualityScoreCalculator:
    """
    Computes weighted quality scores (0.0 to 100.0) across workflow dimensions.
    """

    @staticmethod
    def calculate_scores(metrics: ExecutionMetrics, patch_result: PatchComparisonResult, status: str) -> Dict[str, float]:
        # Planning score based on duration and structure
        planning_score = max(0.0, min(100.0, 100.0 - (metrics.planning_time_ms / 100.0)))

        # Retrieval score based on precision and recall
        retrieval_score = round(((metrics.context_precision + metrics.context_recall) / 2.0) * 100.0, 2)
        if retrieval_score == 0.0:
            retrieval_score = 75.0

        # Repair score based on attempts needed
        repair_score = max(0.0, 100.0 - (metrics.repair_attempts * 25.0))

        # Execution score based on status
        if status in ("PASS", "COMPLETED", "PASS_WITH_WARNINGS"):
            execution_score = 100.0
        elif status == "PARTIAL":
            execution_score = 50.0
        else:
            execution_score = 0.0

        # Validation score based on patch diff accuracy and AST similarity
        validation_score = round(((patch_result.diff_accuracy + patch_result.ast_similarity) / 2.0) * 100.0, 2)

        # Overall weighted engineering score
        overall_score = round(
            (planning_score * 0.15) +
            (retrieval_score * 0.15) +
            (repair_score * 0.20) +
            (execution_score * 0.30) +
            (validation_score * 0.20),
            2
        )

        return {
            "planning_score": round(planning_score, 2),
            "retrieval_score": retrieval_score,
            "repair_score": round(repair_score, 2),
            "execution_score": execution_score,
            "validation_score": validation_score,
            "overall_engineering_score": overall_score
        }
