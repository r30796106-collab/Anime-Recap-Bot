"""Small standard-library client for a user-managed ComfyUI server."""
from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI rejects a request or cannot be reached."""


class ComfyUIClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("ComfyUI URL must use http:// or https://")
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def submit_workflow(self, workflow: dict[str, Any], client_id: str | None = None) -> str:
        if not isinstance(workflow, dict) or not workflow:
            raise ValueError("A non-empty ComfyUI workflow is required")
        payload: dict[str, Any] = {"prompt": workflow}
        if client_id:
            payload["client_id"] = client_id
        response = self._json_request("POST", "/prompt", payload)
        prompt_id = response.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ComfyUIError("ComfyUI response did not contain a prompt_id")
        return prompt_id

    def get_history(self, prompt_id: str) -> dict[str, Any]:
        if not prompt_id:
            raise ValueError("prompt_id must not be empty")
        return self._json_request("GET", f"/history/{prompt_id}")

    def wait_for_completion(
        self, prompt_id: str, timeout: float = 600.0, poll_interval: float = 2.0
    ) -> dict[str, Any]:
        if timeout <= 0 or poll_interval <= 0:
            raise ValueError("Timeout and poll interval must be positive")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            history = self.get_history(prompt_id)
            record = history.get(prompt_id)
            if isinstance(record, dict) and record.get("outputs"):
                return record
            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
        raise TimeoutError(f"ComfyUI workflow {prompt_id} did not finish in time")

    def _json_request(self, method: str, path: str, payload: dict[str, Any] | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ComfyUIError(f"ComfyUI request failed: {exc}") from exc
