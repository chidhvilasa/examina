# EXAMINA Security Notes

This document records the security verification performed during Phase 6
(Hardening and Beta Preparation) and is maintained as new verification
work is done in future phases. It implements Constitution Principle 8
(security before features) and Principle 11 (security threat model) by
giving each control a concrete, checkable claim rather than an assumed one.

## ZIP Extraction — Verified: EXAMINA Never Extracts Archive Contents to Disk

**Claim:** No code path in `src/examina/` calls `zipfile.ZipFile.extract()`
or `.extractall()`, or writes any archive member's content to a
filesystem path. A zip-slip path-traversal attack (a malicious member
name like `../../etc/passwd`) has no effect on EXAMINA because EXAMINA
never resolves or writes a member path anywhere.

**Verification performed:** `src/examina/pipeline/steps/archive_check.py`
was read in full and the repository was searched for every call site of
`zipfile`, `.extract(`, and `.extractall(`. The only match is
`zipfile.ZipFile(BytesIO(data))` in `_check_zip_bomb()`, used exclusively
to call `.infolist()` and read each member's declared `file_size` — pure
in-memory metadata inspection, never a `.read()`, `.extract()`, or
`.extractall()` call. `check_archive_bomb()` exists purely as
defense-in-depth: none of EXAMINA's four allowed file types
(JPEG/PNG/WebP/PDF) are archives, so this step only runs at all if a
future MIME-signature change lets archive bytes reach it. The DOCX
adapter that does perform ZIP-container extraction lives inside PRISM,
a separate codebase EXAMINA never imports or modifies (Constitution
Principle 10 — the bridge is one-way).

**Conclusion:** No zip-slip fix is required in EXAMINA's own code, because
there is no extraction call to harden. This finding is re-verified any
time `archive_check.py` changes; a future change that introduces an
`.extract()` call must add the `safe_zip_member()` path-traversal check
described in the Phase 6 prompt before it ships.

## Archive Bomb Detection — Metadata Only

`check_archive_bomb()` (`src/examina/pipeline/steps/archive_check.py`)
determines uncompressed size and compression ratio without ever
decompressing untrusted data:

- **ZIP:** sums each member's `ZipInfo.file_size` (a value taken from the
  archive's central directory) via `zipfile.ZipFile(...).infolist()`.
- **gzip:** reads the trailing 4 bytes of the stream, which per RFC 1952
  store the uncompressed size modulo 2³², without decompressing anything.
- **tar / bzip2 / 7z:** rejected outright with `DecompressionBombError`,
  since no vetted stdlib-only size-inspection path exists yet for these
  formats (`specs/TECH_DEBT.md` TD-007).

## MIME Detection — Magic Bytes Only

`check_mime_type()` (`src/examina/pipeline/steps/mime_check.py`) inspects
only the file's own leading byte signature (`_SIGNATURES` table: JPEG
`FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, WebP `RIFF`...`WEBP`, PDF
`%PDF-`). It never trusts a client-supplied `Content-Type` header or the
uploaded filename/extension — both are attacker-controlled per
Constitution Principle 11's threat model (the malicious uploader).

## Filename Sanitization — Original Filename Discarded

`sanitize_filename()` (`src/examina/pipeline/steps/filename_sanitize.py`)
never reads, inspects, or logs the original filename in any way. It
returns a fresh `uuid4()` string as the file's only internal identity,
satisfying Constitution Principle 7 (original filenames are never logged
or retained).

## ClamAV Scan — Temp File Always Deleted

`scan_for_malware()` (`src/examina/pipeline/steps/clamav_scan.py`) writes
the upload to a temp path named with a fresh `uuid4()` (never the
original filename or a predictable name) before invoking `clamdscan`, and
deletes it in a `finally` block (`temp_path.unlink(missing_ok=True)`) on
every exit path — success, detection, or scan failure alike. In
`clamav_mode="skip"` (development only) no temp file is ever written, and
the bypass is always logged at WARNING level so it can never be silently
mistaken for a passed scan.

## Dependency Security Audit

See the "Dependency Security Audit" section below, updated each time
`pip-audit` is re-run.

### Audit run — Phase 6 (2026-07-17)

`pip-audit --requirement requirements/dev.txt` was run against this
repository's pinned dependency set (all Python packages: pydantic,
httpx, pytest, pytest-cov, ruff, mypy, fastapi, uvicorn, slowapi,
SQLAlchemy, psutil, python-multipart, types-psutil, Pillow, PyMuPDF, and
pip-audit itself).

**Result: no known vulnerabilities found.** No CRITICAL, HIGH, or any
other severity findings — no package updates or pin changes were
required this phase.

This check now runs automatically on every push/PR via the
`dependency-audit` CI job (`.github/workflows/ci.yml`); re-run manually
at any time with `pip install pip-audit && pip-audit --requirement
requirements/dev.txt` and update this section if a future run finds
something.
