#!/usr/bin/env python
"""
Pre-alpha load test for the EXAMINA API.

Standalone: uses only the Python standard library (urllib,
concurrent.futures, time, json, argparse, uuid) — no external HTTP
client dependency, so it can run against a deployed EXAMINA instance
from any machine with a Python 3.11+ interpreter and nothing else
installed.

Usage:
    python scripts/load_test.py \\
        --url http://localhost:8000 \\
        --invite-code your-code \\
        [--jpeg path/to/small.jpg]

If --jpeg is omitted, minimal JPEG bytes are generated inline.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

_MINIMAL_JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 20

_SEQUENTIAL_REQUESTS = 10
_SEQUENTIAL_DELAY_SECONDS = 5
_CONCURRENT_REQUESTS = 5
_MEMORY_DIFF_THRESHOLD_MB = 50.0


def _load_jpeg_bytes(jpeg_path: str | None) -> bytes:
    if jpeg_path is None:
        return _MINIMAL_JPEG
    return Path(jpeg_path).read_bytes()


def _multipart_body(
    field_name: str, filename: str, content: bytes, content_type: str
) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        content,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    return b"".join(parts), boundary


def _request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, Any] | None, float]:
    """Perform an HTTP request, returning (status_code, json_body_or_None, elapsed_seconds).

    Never raises: urllib.error.HTTPError carries a valid status code and
    body on a non-2xx response, so it is handled the same as a normal
    response rather than treated as a failure to make the request at all.
    """
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            status = response.getcode()
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
    except urllib.error.URLError as exc:
        elapsed = time.monotonic() - start
        return 0, {"error": str(exc.reason)}, elapsed
    elapsed = time.monotonic() - start

    try:
        parsed: dict[str, Any] | None = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = None
    return status, parsed, elapsed


def _analyze(
    base_url: str, invite_code: str, jpeg_bytes: bytes
) -> tuple[int, dict[str, Any] | None, float]:
    body, boundary = _multipart_body("file", "load_test.jpg", jpeg_bytes, "image/jpeg")
    headers = {
        "Authorization": f"Bearer {invite_code}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    return _request("POST", f"{base_url}/analyze", headers=headers, body=body)


def _health(base_url: str) -> dict[str, Any] | None:
    _, body, _ = _request("GET", f"{base_url}/health")
    return body


def run_scenario_1(base_url: str, invite_code: str, jpeg_bytes: bytes) -> dict[str, Any]:
    print("\n=== Scenario 1 — Sequential (warmup + leak detection) ===")
    response_times: list[float] = []
    status_codes: list[int] = []
    report_ids: list[str | None] = []
    memory_samples: list[float | None] = []

    start_health = _health(base_url)
    memory_start = start_health.get("memory_free_mb") if start_health else None

    for i in range(_SEQUENTIAL_REQUESTS):
        status, body, elapsed = _analyze(base_url, invite_code, jpeg_bytes)
        response_times.append(elapsed)
        status_codes.append(status)
        report_ids.append(body.get("report_id") if body else None)

        health_body = _health(base_url)
        memory_free = health_body.get("memory_free_mb") if health_body else None
        memory_samples.append(memory_free)

        print(
            f"  [{i + 1}/{_SEQUENTIAL_REQUESTS}] status={status} "
            f"time={elapsed:.2f}s report_id={report_ids[-1]} memory_free_mb={memory_free}"
        )
        if i < _SEQUENTIAL_REQUESTS - 1:
            time.sleep(_SEQUENTIAL_DELAY_SECONDS)

    memory_end = memory_samples[-1] if memory_samples else None
    # Positive = free memory decreased (consumed, the leak-suspicious
    # direction). Negative = free memory increased (e.g. OS disk-cache
    # reclamation elsewhere on the machine) — never itself a leak
    # signal, regardless of magnitude.
    memory_decrease = (
        memory_start - memory_end if memory_start is not None and memory_end is not None else None
    )

    success_count = sum(1 for s in status_codes if s == 200)
    success_rate = success_count / len(status_codes) if status_codes else 0.0

    result = {
        "response_times": response_times,
        "status_codes": status_codes,
        "report_ids": report_ids,
        "min_response_time": min(response_times) if response_times else None,
        "max_response_time": max(response_times) if response_times else None,
        "mean_response_time": (
            sum(response_times) / len(response_times) if response_times else None
        ),
        "success_rate": success_rate,
        "memory_free_mb_start": memory_start,
        "memory_free_mb_end": memory_end,
        "memory_decrease_mb": memory_decrease,
        "pass": bool(
            success_rate == 1.0
            and (memory_decrease is None or memory_decrease < _MEMORY_DIFF_THRESHOLD_MB)
        ),
    }

    print(
        f"  min={result['min_response_time']:.2f}s max={result['max_response_time']:.2f}s "
        f"mean={result['mean_response_time']:.2f}s success_rate={success_rate:.0%}"
    )
    print(f"  memory: start={memory_start} end={memory_end} decrease={memory_decrease}")
    print(f"  Scenario 1: {'PASS' if result['pass'] else 'FAIL'}")
    return result


def run_scenario_2(base_url: str, invite_code: str, jpeg_bytes: bytes) -> dict[str, Any]:
    print("\n=== Scenario 2 — Concurrent (basic concurrency) ===")
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=_CONCURRENT_REQUESTS) as executor:
        futures = [
            executor.submit(_analyze, base_url, invite_code, jpeg_bytes)
            for _ in range(_CONCURRENT_REQUESTS)
        ]
        for i, future in enumerate(futures):
            status, body, elapsed = future.result()
            results.append(
                {
                    "status": status,
                    "elapsed": elapsed,
                    "report_id": body.get("report_id") if body else None,
                    "error": body.get("error") if body else None,
                }
            )
            print(f"  [{i + 1}/{_CONCURRENT_REQUESTS}] status={status} time={elapsed:.2f}s")

    all_success = all(r["status"] == 200 for r in results)
    errors = [r for r in results if r["status"] != 200]

    result = {
        "results": results,
        "errors": errors,
        "pass": bool(all_success and len(results) == _CONCURRENT_REQUESTS),
    }
    print(f"  Scenario 2: {'PASS' if result['pass'] else 'FAIL'}")
    return result


def run_scenario_3(base_url: str, invite_code: str) -> dict[str, Any]:
    print("\n=== Scenario 3 — Failure paths ===")

    text_body, boundary = _multipart_body(
        "file", "notes.txt", b"plain text content, not a jpeg", "text/plain"
    )
    status_415, _, _ = _request(
        "POST",
        f"{base_url}/analyze",
        headers={
            "Authorization": f"Bearer {invite_code}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        body=text_body,
    )
    print(f"  Text file upload: status={status_415} (expect 415)")

    jpeg_body, jpeg_boundary = _multipart_body("file", "photo.jpg", _MINIMAL_JPEG, "image/jpeg")
    status_401, _, _ = _request(
        "POST",
        f"{base_url}/analyze",
        headers={
            "Authorization": "Bearer wrong-code",
            "Content-Type": f"multipart/form-data; boundary={jpeg_boundary}",
        },
        body=jpeg_body,
    )
    print(f"  Wrong invite code: status={status_401} (expect 401)")

    status_404, _, _ = _request(
        "GET",
        f"{base_url}/report/nonexistent-id",
        headers={"Authorization": f"Bearer {invite_code}"},
    )
    print(f"  Nonexistent report: status={status_404} (expect 404)")

    result = {
        "text_file_status": status_415,
        "wrong_invite_status": status_401,
        "nonexistent_report_status": status_404,
        "pass": bool(status_415 == 415 and status_401 == 401 and status_404 == 404),
    }
    print(f"  Scenario 3: {'PASS' if result['pass'] else 'FAIL'}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EXAMINA pre-alpha load test.")
    parser.add_argument("--url", required=True, help="Base URL of the running EXAMINA API")
    parser.add_argument("--invite-code", required=True, help="Valid invite code")
    parser.add_argument("--jpeg", default=None, help="Path to a JPEG file to upload")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    jpeg_bytes = _load_jpeg_bytes(args.jpeg)

    scenario_1 = run_scenario_1(base_url, args.invite_code, jpeg_bytes)
    scenario_2 = run_scenario_2(base_url, args.invite_code, jpeg_bytes)
    scenario_3 = run_scenario_3(base_url, args.invite_code)

    overall_pass = scenario_1["pass"] and scenario_2["pass"] and scenario_3["pass"]

    print("\nLOAD TEST RESULTS")
    print(f"Scenario 1 (Sequential): {'PASS' if scenario_1['pass'] else 'FAIL'}")
    print(f"Scenario 2 (Concurrent): {'PASS' if scenario_2['pass'] else 'FAIL'}")
    print(f"Scenario 3 (Failure paths): {'PASS' if scenario_3['pass'] else 'FAIL'}")
    print(f"Overall: {'PASS' if overall_pass else 'FAIL'}")

    results = {
        "base_url": base_url,
        "scenario_1_sequential": scenario_1,
        "scenario_2_concurrent": scenario_2,
        "scenario_3_failure_paths": scenario_3,
        "overall_pass": overall_pass,
    }

    output_path = Path(__file__).resolve().parent.parent / "alpha-data" / "load_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
