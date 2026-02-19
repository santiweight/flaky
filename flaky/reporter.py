"""
Reporter for eval results.
"""

import json
from dataclasses import dataclass, field

from flaky.case import GenerationResult


@dataclass
class SuiteSummary:
    """Aggregated summary across all eval cases in a test run."""

    reports: list["EvalReport"] = field(default_factory=list)

    @property
    def total_cases(self) -> int:
        return len(self.reports)

    @property
    def total_generations(self) -> int:
        return sum(r.num_generations for r in self.reports)

    @property
    def total_tests(self) -> int:
        return sum(r.total_tests for r in self.reports)

    @property
    def total_passed(self) -> int:
        return sum(r.total_passed for r in self.reports)

    @property
    def total_failed(self) -> int:
        return sum(r.total_failed for r in self.reports)

    @property
    def overall_success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.total_passed / self.total_tests) * 100

    def get_per_case_summary(self) -> list[tuple[str, float, int, int]]:
        """
        Returns list of (case_name, success_rate, passed, total) tuples.
        """
        return [
            (r.case_name, r.success_rate, r.total_passed, r.total_tests)
            for r in self.reports
        ]


@dataclass
class EvalReport:
    """Aggregated report across all generations."""

    case_name: str
    num_generations: int
    generation_results: list[GenerationResult] = field(default_factory=list)

    @property
    def total_tests(self) -> int:
        return sum(g.total_count for g in self.generation_results)

    @property
    def total_passed(self) -> int:
        return sum(g.passed_count for g in self.generation_results)

    @property
    def total_failed(self) -> int:
        return sum(g.failed_count for g in self.generation_results)

    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.total_passed / self.total_tests) * 100

    @property
    def total_duration_ms(self) -> float:
        return sum(g.duration_ms for g in self.generation_results)

    @property
    def avg_generation_duration_ms(self) -> float:
        if not self.generation_results:
            return 0.0
        return self.total_duration_ms / len(self.generation_results)

    def per_test_breakdown(self) -> dict[str, tuple[int, int, float]]:
        """
        Returns dict mapping test name to (passed, total, rate) tuples.
        """
        test_stats: dict[str, tuple[int, int]] = {}

        for gen_result in self.generation_results:
            for test_result in gen_result.test_results:
                if test_result.name not in test_stats:
                    test_stats[test_result.name] = (0, 0)
                passed, total = test_stats[test_result.name]
                test_stats[test_result.name] = (
                    passed + (1 if test_result.passed else 0),
                    total + 1,
                )

        return {
            name: (passed, total, (passed / total) * 100 if total > 0 else 0.0)
            for name, (passed, total) in test_stats.items()
        }

    def per_test_timing(self) -> dict[str, dict[str, float]]:
        """
        Returns dict mapping test name to timing stats (min, max, avg, p95).
        """
        from statistics import mean, quantiles

        test_timings: dict[str, list[float]] = {}

        for gen_result in self.generation_results:
            for test_result in gen_result.test_results:
                if test_result.name not in test_timings:
                    test_timings[test_result.name] = []
                test_timings[test_result.name].append(test_result.duration_ms)

        stats = {}
        for name, timings in test_timings.items():
            if not timings:
                continue
            sorted_timings = sorted(timings)
            p95 = quantiles(sorted_timings, n=20)[18] if len(sorted_timings) > 1 else timings[0]
            stats[name] = {
                "min_ms": min(timings),
                "max_ms": max(timings),
                "avg_ms": mean(timings),
                "p95_ms": p95,
            }
        return stats


class Reporter:
    """Formats and outputs eval reports."""

    def __init__(self, use_color: bool = True):
        self.use_color = use_color

    def _green(self, text: str) -> str:
        if self.use_color:
            return f"\033[92m{text}\033[0m"
        return text

    def _red(self, text: str) -> str:
        if self.use_color:
            return f"\033[91m{text}\033[0m"
        return text

    def _bold(self, text: str) -> str:
        if self.use_color:
            return f"\033[1m{text}\033[0m"
        return text

    def _dim(self, text: str) -> str:
        if self.use_color:
            return f"\033[2m{text}\033[0m"
        return text

    def _cyan(self, text: str) -> str:
        if self.use_color:
            return f"\033[96m{text}\033[0m"
        return text

    def print_generation_progress(self, gen_result: GenerationResult) -> None:
        """Print progress for a single generation."""
        duration_s = gen_result.duration_ms / 1000
        print(f"\nGeneration {gen_result.generation_num} {self._dim(f'({duration_s:.2f}s)')}:")

        for test_result in gen_result.test_results:
            if test_result.passed:
                status = self._green("✓")
            else:
                status = self._red("✗")

            timing = self._dim(f"{test_result.duration_ms:.0f}ms")
            line = f"  {status} {test_result.name} {timing}"
            if not test_result.passed and test_result.error:
                error_preview = test_result.error[:60]
                if len(test_result.error) > 60:
                    error_preview += "..."
                line += f" {self._dim(f'({error_preview})')}"

            print(line)

    def print_summary(self, report: EvalReport) -> None:
        """Print the final summary report."""
        print(f"\n{self._bold('Results:')}")
        print(f"  Generations: {report.num_generations}")
        if report.num_generations > 0:
            tests_per_gen = report.total_tests // report.num_generations
        else:
            tests_per_gen = 0
        print(f"  Tests per generation: {tests_per_gen}")

        rate = report.success_rate
        rate_color = self._green if rate >= 80 else self._red
        print(
            f"  Success rate: {rate_color(f'{rate:.1f}%')} "
            f"({report.total_passed}/{report.total_tests} tests passed across all runs)"
        )

        total_s = report.total_duration_ms / 1000
        avg_s = report.avg_generation_duration_ms / 1000
        print(f"\n  {self._bold('Timing:')}")
        print(f"    Total time: {self._cyan(f'{total_s:.2f}s')}")
        print(f"    Avg per generation: {self._cyan(f'{avg_s:.2f}s')}")

        print(f"\n  {self._bold('Per-test breakdown:')}")
        test_breakdown = report.per_test_breakdown()
        test_timing = report.per_test_timing()

        for test_name, (passed, total, rate) in test_breakdown.items():
            rate_color = self._green if rate >= 80 else self._red
            timing_info = ""
            if test_name in test_timing:
                avg_ms = test_timing[test_name]["avg_ms"]
                timing_info = f" {self._dim(f'avg: {avg_ms:.0f}ms')}"
            print(f"    {test_name}: {rate_color(f'{rate:.0f}%')} ({passed}/{total}){timing_info}")

    def print_suite_summary(self, summary: SuiteSummary) -> None:
        """Print a high-level summary of all eval cases."""
        print("\n" + "=" * 70)
        print(self._bold("EVAL SUITE SUMMARY"))
        print("=" * 70)

        rate = summary.overall_success_rate
        rate_color = self._green if rate >= 80 else self._red
        print(f"\n{self._bold('Overall Results:')}")
        print(f"  Cases: {summary.total_cases}")
        print(f"  Total generations: {summary.total_generations}")
        print(f"  Total test executions: {summary.total_tests}")
        rate_str = rate_color(f'{rate:.1f}%')
        print(f"  Success rate: {rate_str} ({summary.total_passed}/{summary.total_tests})")

        print(f"\n{self._bold('Per-Case Results:')}")
        case_summaries = summary.get_per_case_summary()
        case_summaries.sort(key=lambda x: x[1], reverse=True)

        print(f"  {'Case':<30} {'Pass':>8} {'Tests':>8}")
        print(f"  {'-' * 30} {'-' * 8} {'-' * 8}")

        for case_name, case_rate, passed, total in case_summaries:
            rate_color = self._green if case_rate >= 80 else self._red
            print(
                f"  {case_name:<30} "
                f"{rate_color(f'{case_rate:.0f}%'):>8} "
                f"{f'{passed}/{total}':>8}"
            )

        print("\n" + "=" * 70)

    def to_json(self, report: EvalReport) -> str:
        """Convert report to JSON format."""
        data = {
            "case_name": report.case_name,
            "num_generations": report.num_generations,
            "total_tests": report.total_tests,
            "total_passed": report.total_passed,
            "total_failed": report.total_failed,
            "success_rate": report.success_rate,
            "timing": {
                "total_duration_ms": report.total_duration_ms,
                "avg_generation_duration_ms": report.avg_generation_duration_ms,
            },
            "per_test_breakdown": {
                name: {"passed": passed, "total": total, "rate": rate}
                for name, (passed, total, rate) in report.per_test_breakdown().items()
            },
            "per_test_timing": report.per_test_timing(),
            "generations": [
                {
                    "generation_num": g.generation_num,
                    "passed": g.passed_count,
                    "failed": g.failed_count,
                    "duration_ms": g.duration_ms,
                    "tests": [
                        {
                            "name": t.name,
                            "passed": t.passed,
                            "error": t.error,
                            "duration_ms": t.duration_ms,
                        }
                        for t in g.test_results
                    ],
                }
                for g in report.generation_results
            ],
        }
        return json.dumps(data, indent=2)

    def suite_to_json(self, summary: SuiteSummary) -> str:
        """Convert suite summary to JSON format."""
        data = {
            "total_cases": summary.total_cases,
            "total_generations": summary.total_generations,
            "total_tests": summary.total_tests,
            "total_passed": summary.total_passed,
            "total_failed": summary.total_failed,
            "overall_success_rate": summary.overall_success_rate,
            "per_case_results": [
                {
                    "case_name": case_name,
                    "success_rate": case_rate,
                    "passed": passed,
                    "total": total,
                }
                for case_name, case_rate, passed, total in summary.get_per_case_summary()
            ],
        }
        return json.dumps(data, indent=2)
