"""
Cloud upload client for flaky results.
"""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flaky.git import GitContext
    from flaky.reporter import EvalReport


@dataclass
class CloudConfig:
    """Configuration for cloud uploads."""

    project: str
    api_key: str
    supabase_url: str = "https://your-project.supabase.co"

    @classmethod
    def from_config(cls, config: dict) -> "CloudConfig | None":
        """
        Create CloudConfig from [tool.flaky.cloud] config dict.
        Returns None if cloud is not configured.
        Raises ValueError if configured but API key is missing.
        """
        cloud_config = config.get("cloud", {})
        if not cloud_config:
            return None

        project = cloud_config.get("project")
        if not project:
            return None

        api_key = os.environ.get("FLAKY_API_KEY")
        if not api_key:
            raise ValueError(
                "FLAKY_API_KEY environment variable is required when "
                "[tool.flaky.cloud] is configured.\n"
                "Set it with: export FLAKY_API_KEY=your_api_key"
            )

        supabase_url = cloud_config.get("url", "https://your-project.supabase.co")

        return cls(
            project=project,
            api_key=api_key,
            supabase_url=supabase_url,
        )


@dataclass
class UploadResult:
    """Result of a cloud upload."""

    success: bool
    run_id: str | None = None
    url: str | None = None
    error: str | None = None


class CloudClient:
    """Client for uploading eval results to Supabase."""

    def __init__(self, config: CloudConfig):
        self.config = config
        self._http_client = None

    def _get_client(self):
        """Lazy-load httpx client."""
        if self._http_client is None:
            try:
                import httpx
                self._http_client = httpx.Client(timeout=30.0)
            except ImportError:
                raise ImportError(
                    "httpx is required for cloud uploads.\n"
                    "Install it with: pip install flaky[cloud]"
                )
        return self._http_client

    def upload_report(
        self,
        report: "EvalReport",
        git_context: "GitContext",
    ) -> UploadResult:
        """
        Upload an eval report to Supabase.

        Args:
            report: The eval report to upload
            git_context: Git context (branch, commit, etc.)

        Returns:
            UploadResult with success status and URL if successful
        """
        client = self._get_client()

        payload = {
            "project": self.config.project,
            "branch": git_context.branch,
            "branch_type": git_context.branch_type,
            "commit_sha": git_context.commit_sha,
            "case_name": report.case_name,
            "num_generations": report.num_generations,
            "total_tests": report.total_tests,
            "total_passed": report.total_passed,
            "success_rate": report.success_rate,
            "total_duration_ms": report.total_duration_ms,
            "per_test_breakdown": {
                name: {"passed": passed, "total": total, "rate": rate}
                for name, (passed, total, rate) in report.per_test_breakdown().items()
            },
            "raw_report": self._report_to_dict(report),
        }

        try:
            response = client.post(
                f"{self.config.supabase_url}/rest/v1/runs",
                json=payload,
                headers={
                    "apikey": self.config.api_key,
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
            )

            if response.status_code in (200, 201):
                data = response.json()
                run_id = data[0]["id"] if isinstance(data, list) and data else None
                return UploadResult(
                    success=True,
                    run_id=run_id,
                    url=self._build_url(git_context, run_id),
                )
            else:
                return UploadResult(
                    success=False,
                    error=f"Upload failed: {response.status_code} - {response.text}",
                )

        except Exception as e:
            return UploadResult(
                success=False,
                error=f"Upload failed: {str(e)}",
            )

    def _report_to_dict(self, report: "EvalReport") -> dict:
        """Convert an EvalReport to a JSON-serializable dict."""
        return {
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

    def _build_url(self, git_context: "GitContext", run_id: str | None) -> str:
        """Build the URL for viewing the uploaded run."""
        base = f"flaky.dev/{self.config.project}/{git_context.full_branch}"
        if run_id:
            return f"{base}/run_{run_id}"
        return base

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "CloudClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
