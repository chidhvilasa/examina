"""Tests for src/examina/pipeline/steps/clamav_scan.py — subprocess is mocked throughout."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import MalwareDetectedError, ScanFailureError
from examina.pipeline.steps import clamav_scan
from examina.pipeline.steps.clamav_scan import scan_for_malware


def _config(tmp_path: Path, mode: str) -> UploadConfig:
    return UploadConfig(clamav_mode=mode, temp_dir=tmp_path / "examina-upload")  # type: ignore[arg-type]


def _completed(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["clamdscan"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class TestSkipMode:
    def test_skip_mode_logs_warning_and_returns_none(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("test-clamav-skip")
        with caplog.at_level(logging.WARNING, logger="test-clamav-skip"):
            result = scan_for_malware(b"data", _config(tmp_path, "skip"), logger)
        assert result is None
        assert any("clamav_mode=skip" in record.message for record in caplog.records)

    def test_skip_mode_never_calls_subprocess(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_run = MagicMock()
        monkeypatch.setattr(clamav_scan.subprocess, "run", mock_run)
        scan_for_malware(b"data", _config(tmp_path, "skip"), logging.getLogger("test"))
        mock_run.assert_not_called()


class TestEnforceMode:
    def test_return_code_zero_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(clamav_scan.subprocess, "run", lambda *a, **kw: _completed(0))
        result = scan_for_malware(b"data", _config(tmp_path, "enforce"), logging.getLogger("test"))
        assert result is None

    def test_return_code_one_raises_malware_detected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stdout = "/tmp/examina-upload/abc: Eicar-Test-Signature FOUND\n"
        monkeypatch.setattr(
            clamav_scan.subprocess, "run", lambda *a, **kw: _completed(1, stdout=stdout)
        )
        with pytest.raises(MalwareDetectedError) as exc_info:
            scan_for_malware(b"data", _config(tmp_path, "enforce"), logging.getLogger("test"))
        assert exc_info.value.detection_name == "Eicar-Test-Signature"

    def test_return_code_two_raises_scan_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(clamav_scan.subprocess, "run", lambda *a, **kw: _completed(2))
        with pytest.raises(ScanFailureError) as exc_info:
            scan_for_malware(b"data", _config(tmp_path, "enforce"), logging.getLogger("test"))
        assert exc_info.value.scan_type == "clamav"

    def test_file_not_found_raises_scan_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise_not_found(*args: object, **kwargs: object) -> None:
            raise FileNotFoundError("clamdscan not found")

        monkeypatch.setattr(clamav_scan.subprocess, "run", _raise_not_found)
        with pytest.raises(ScanFailureError) as exc_info:
            scan_for_malware(b"data", _config(tmp_path, "enforce"), logging.getLogger("test"))
        assert exc_info.value.scan_type == "clamav"
        assert exc_info.value.message == "ClamAV is not available"

    def test_temp_file_deleted_after_successful_scan(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _config(tmp_path, "enforce")
        monkeypatch.setattr(clamav_scan.subprocess, "run", lambda *a, **kw: _completed(0))
        scan_for_malware(b"data", config, logging.getLogger("test"))
        assert list(config.temp_dir.iterdir()) == []

    def test_temp_file_deleted_even_when_scan_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _config(tmp_path, "enforce")
        monkeypatch.setattr(
            clamav_scan.subprocess, "run", lambda *a, **kw: _completed(1, stdout="x: Y FOUND")
        )
        with pytest.raises(MalwareDetectedError):
            scan_for_malware(b"data", config, logging.getLogger("test"))
        assert list(config.temp_dir.iterdir()) == []

    def test_detection_name_falls_back_to_unknown_without_found_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            clamav_scan.subprocess, "run", lambda *a, **kw: _completed(1, stdout="")
        )
        with pytest.raises(MalwareDetectedError) as exc_info:
            scan_for_malware(b"data", _config(tmp_path, "enforce"), logging.getLogger("test"))
        assert exc_info.value.detection_name == "unknown"

    def test_malware_detected_message_is_user_safe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stdout = "/tmp/x: Win.Trojan.SecretInternalName-1 FOUND\n"
        monkeypatch.setattr(
            clamav_scan.subprocess, "run", lambda *a, **kw: _completed(1, stdout=stdout)
        )
        with pytest.raises(MalwareDetectedError) as exc_info:
            scan_for_malware(b"data", _config(tmp_path, "enforce"), logging.getLogger("test"))
        assert "Win.Trojan.SecretInternalName-1" not in exc_info.value.message
        assert exc_info.value.message == "File rejected for security reasons"
