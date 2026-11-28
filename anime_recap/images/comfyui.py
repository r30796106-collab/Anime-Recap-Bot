"""Small standard-library client for a user-managed ComfyUI server."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI rejects a request or cannot be reached."""


class ComfyUIClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_download_bytes: int = 50 * 1024 * 1024,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("ComfyUI URL must use http:// or https://")
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        if not isinstance(max_download_bytes, int) or isinstance(max_download_bytes, bool) or max_download_bytes <= 0:
            raise ValueError("Maximum image download size must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_download_bytes = max_download_bytes

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
            if isinstance(record, dict):
                status = record.get("status")
                status_str = (
                    status.get("status_str", "")
                    if isinstance(status, dict)
                    else ""
                )
                if not isinstance(status_str, str):
                    status_str = ""
                messages = status.get("messages", []) if isinstance(status, dict) else []
                if not isinstance(messages, list):
                    messages = []
                execution_error = any(
                    isinstance(message, (list, tuple))
                    and message
                    and message[0] == "execution_error"
                    for message in messages
                )
                if status_str.lower() in {"error", "failed"} or execution_error:
                    details: list[str] = []
                    for message in messages:
                        if (
                            isinstance(message, (list, tuple))
                            and len(message) > 1
                            and message[0] == "execution_error"
                            and isinstance(message[1], dict)
                        ):
                            for key in ("exception_type", "exception_message"):
                                value = message[1].get(key)
                                if isinstance(value, str) and value.strip():
                                    details.append(value.strip()[:200])
                    summary = " - ".join(details) or status_str or "execution_error"
                    raise ComfyUIError(
                        f"ComfyUI workflow {prompt_id} failed: {summary}"
                    )
                if record.get("outputs"):
                    return record
                if isinstance(status, dict) and status.get("completed") is True:
                    raise ComfyUIError(
                        f"ComfyUI workflow {prompt_id} completed without outputs"
                    )
            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
        raise TimeoutError(f"ComfyUI workflow {prompt_id} did not finish in time")

    def download_image(self, image: dict[str, str], output_path: str | Path) -> Path:
        """Download one bounded-size image descriptor returned by ComfyUI history."""
        required = ("filename", "subfolder", "type")
        if any(not isinstance(image.get(key), str) or not image[key].strip() for key in required):
            raise ValueError("Image descriptor must contain non-empty filename, subfolder and type")
        query = urlencode({key: image[key] for key in required})
        request = Request(self.base_url + "/view?" + query, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                # Read one byte beyond the configured cap so oversized responses
                # are rejected without buffering the entire server response.
                data = response.read(self.max_download_bytes + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ComfyUIError(f"ComfyUI image download failed: {exc}") from exc
        if len(data) > self.max_download_bytes:
            raise ComfyUIError(
                "ComfyUI image download exceeds configured limit "
                f"({self.max_download_bytes} bytes)"
            )
        if not data:
            raise ComfyUIError("ComfyUI returned an empty image")
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return destination

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
