"""
Eval runner for flaky.
"""

import argparse
import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

from flaky.case import EvalCase, GenerationResult
from flaky.reporter import EvalReport, Reporter, SuiteSummary


def _load_config() -> dict:
    """
    Load [tool.flaky] config from pyproject.toml in the current working directory.
    Returns an empty dict if not found.
    """
    pyproject = Path.cwd() / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("flaky", {})
    except Exception:
        return {}


def _run_single_generation(case_dir: Path, gen_num: int) -> GenerationResult:
    """
    Run a single generation in isolation (designed for subprocess execution).

    Each call imports the eval module fresh, finds EvalCase subclasses,
    runs all their tests, and returns combined results. Process isolation
    via ProcessPoolExecutor prevents state leaking between runs.
    """
    import importlib.util
    import sys
    from pathlib import Path

    from flaky.case import EvalCase, GenerationResult

    case_dir = Path(case_dir)

    if str(case_dir) not in sys.path:
        sys.path.insert(0, str(case_dir))

    parent = str(case_dir.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    eval_file = case_dir / "eval.py"
    if not eval_file.exists():
        py_files = sorted(case_dir.glob("*.py"))
        if py_files:
            eval_file = py_files[0]
        else:
            raise ValueError(f"No Python files found in {case_dir}")

    spec = importlib.util.spec_from_file_location("eval_module", eval_file)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load {eval_file}")

    eval_module = importlib.util.module_from_spec(spec)
    sys.modules["eval_module"] = eval_module
    spec.loader.exec_module(eval_module)

    eval_classes = []
    for name in dir(eval_module):
        obj = getattr(eval_module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, EvalCase)
            and obj is not EvalCase
        ):
            eval_classes.append(obj)

    if not eval_classes:
        raise ValueError(f"No EvalCase subclass found in {eval_file}")

    import time
    start_time = time.perf_counter()
    
    combined_result = GenerationResult(generation_num=gen_num)
    for eval_class in eval_classes:
        eval_case = eval_class()
        result = eval_case.run_all_tests(generation_num=gen_num)
        combined_result.test_results.extend(result.test_results)

    combined_result.duration_ms = (time.perf_counter() - start_time) * 1000
    return combined_result


class EvalRunner:
    """Runs eval cases and collects results."""

    def __init__(self, cases_dir: Path):
        self.cases_dir = cases_dir
        self.reporter = Reporter()

    def discover_cases(self) -> list[str]:
        """Discover available eval cases (directories containing .py files with EvalCase subclasses)."""
        cases = []
        if not self.cases_dir.exists():
            return cases

        for item in sorted(self.cases_dir.iterdir()):
            if item.is_dir() and any(item.glob("*.py")):
                cases.append(item.name)

        return cases

    def load_case(self, case_name: str) -> list[EvalCase]:
        """Load all eval cases by name. Returns list of EvalCase instances."""
        case_dir = self.cases_dir / case_name
        eval_file = case_dir / "eval.py"

        if not eval_file.exists():
            py_files = sorted(case_dir.glob("*.py"))
            if not py_files:
                raise ValueError(f"No Python files found in eval case '{case_name}' at {case_dir}")
            eval_file = py_files[0]

        spec = importlib.util.spec_from_file_location(
            f"flaky.cases.{case_name}.eval",
            eval_file,
        )
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load eval case from {eval_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        eval_cases = []
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, EvalCase)
                and obj is not EvalCase
            ):
                eval_cases.append(obj())

        if not eval_cases:
            raise ValueError(f"No EvalCase subclass found in {eval_file}")

        return eval_cases

    def run_case(
        self,
        case_name: str,
        num_runs: int = 5,
        verbose: bool = True,
        parallel: bool = True,
        max_workers: int | None = None,
    ) -> EvalReport:
        """
        Run an eval case multiple times and collect results.

        Each run executes in an isolated subprocess via ProcessPoolExecutor.
        This prevents state leaking between runs — the core value proposition.
        """
        eval_cases = self.load_case(case_name)
        case_dir = self.cases_dir / case_name

        if verbose:
            mode = "parallel" if parallel else "sequential"
            class_names = ", ".join(ec.get_name() for ec in eval_cases)
            print(f"Running: {case_name} [{class_names}] ({num_runs} generations, {mode})")

        report = EvalReport(case_name=case_name, num_generations=num_runs)

        effective_workers = 1 if not parallel else (max_workers or min(num_runs, 10))
        with ProcessPoolExecutor(max_workers=effective_workers) as executor:
            futures = {
                executor.submit(_run_single_generation, case_dir, i): i
                for i in range(1, num_runs + 1)
            }

            for future in as_completed(futures):
                gen_num = futures[future]
                try:
                    gen_result = future.result()
                    report.generation_results.append(gen_result)
                    if verbose:
                        self.reporter.print_generation_progress(gen_result)
                except Exception as e:
                    print(f"Generation {gen_num} failed: {e}")

        if verbose:
            self.reporter.print_summary(report)

        return report


def main() -> None:
    """CLI entry point."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    config = _load_config()
    default_dir = config.get("evals_dir", "./evals")
    default_runs = config.get("runs", 5)
    default_max_workers = config.get("max_workers", None)

    parser = argparse.ArgumentParser(
        description="Run flaky eval cases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    run_parser = subparsers.add_parser("run", help="Run eval cases")
    run_parser.add_argument(
        "--case",
        type=str,
        help="Name of the eval case to run",
    )
    run_parser.add_argument(
        "--all",
        action="store_true",
        help="Run all eval cases",
    )
    run_parser.add_argument(
        "--runs",
        type=int,
        default=default_runs,
        help=f"Number of generations to run (default: {default_runs})",
    )
    run_parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Run generations in parallel (default: True)",
    )
    run_parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run generations sequentially (overrides --parallel)",
    )
    run_parser.add_argument(
        "--max-workers",
        type=int,
        default=default_max_workers,
        help="Max parallel workers (default: min(runs, 10))",
    )
    run_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    run_parser.add_argument(
        "--dir",
        type=str,
        default=default_dir,
        help=f"Directory containing eval cases (default: {default_dir})",
    )

    list_parser = subparsers.add_parser("list", help="List available eval cases")
    list_parser.add_argument(
        "--dir",
        type=str,
        default=default_dir,
        help=f"Directory containing eval cases (default: {default_dir})",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    cases_dir = Path(args.dir).resolve()
    runner = EvalRunner(cases_dir)

    if args.command == "list":
        cases = runner.discover_cases()
        if cases:
            print("Available eval cases:")
            for case in cases:
                print(f"  - {case}")
        else:
            print(f"No eval cases found in {cases_dir}")

    elif args.command == "run":
        if args.all:
            cases = runner.discover_cases()
            if not cases:
                print(f"No eval cases found in {cases_dir}")
                sys.exit(1)
        elif args.case:
            cases = [args.case]
        else:
            print("Error: Must specify --case or --all")
            sys.exit(1)

        all_reports = []
        parallel = not args.sequential
        for case in cases:
            report = runner.run_case(
                case,
                num_runs=args.runs,
                verbose=(args.format == "text"),
                parallel=parallel,
                max_workers=args.max_workers,
            )
            all_reports.append(report)

        reporter = Reporter()

        if args.format == "json":
            if args.all:
                summary = SuiteSummary(reports=all_reports)
                print(reporter.suite_to_json(summary))
            else:
                for report in all_reports:
                    print(reporter.to_json(report))
        else:
            if args.all and len(all_reports) > 1:
                summary = SuiteSummary(reports=all_reports)
                reporter.print_suite_summary(summary)


if __name__ == "__main__":
    main()
