# ADR-0002: MIME detection via dependency-free signature table, not python-magic

Status: ACCEPTED

## Context

The Phase 3 upload pipeline prompt (`specs/DEPLOYMENT_SPEC_v1.0.md`'s
upload security section) requires `check_mime_type()`
(`src/examina/pipeline/steps/mime_check.py`) to detect a file's true type
from its raw bytes — never trusting a client-supplied `Content-Type`
header or filename extension (Constitution Principle 11's threat model:
"attackers control HTTP headers including Content-Type").

`python-magic-bin` was evaluated as the primary approach, mirroring the
Windows libmagic packaging PRISM uses. It was installed and tested
directly against this repository's development environment
(`.venv` on Windows 11, Python 3.12):

```
import magic
m = magic.Magic(mime=True)
m.from_buffer(<JPEG bytes>)  # -> "image/jpeg", ~0.02s, no hang
```

No deadlock or hang was observed locally — unlike the issue this ADR's
prompt anticipated. The actual blocker is different and more fundamental:
`python-magic-bin` ships as a **Windows/macOS-only prebuilt wheel**
bundling a platform-specific `libmagic` binary. This repository's CI
(`.github/workflows/ci.yml`) runs every job, including `type-check` and
`unit-tests`, on `ubuntu-latest` via `pip install -e .`. Adding
`python-magic-bin` (or plain `python-magic`, which requires a
system-installed `libmagic` that the CI image does not provision) to
`pyproject.toml` would make `pip install -e .` fail on every PR — an
unacceptable CI regression for a MIME-detection convenience.

EXAMINA only needs to distinguish exactly four allowed file types (JPEG,
PNG, WebP, PDF) plus five archive types for the decompression-bomb check
(`archive_check.py`). All nine have short, well-documented, invariant
byte signatures. A native Python signature table fully covers this
closed set without any new runtime dependency, on every platform,
in CI and in production alike (Constitution Principle 8: dependencies
are added only when a phase actually needs them).

## Decision

`check_mime_type()` is implemented as a dependency-free magic-byte
signature table (`_SIGNATURES` in `mime_check.py`), matching prefixes at
fixed offsets against the raw file bytes:

| Type | Signature | Offset |
|---|---|---|
| JPEG | `FF D8 FF` | 0 |
| PNG | `89 50 4E 47 0D 0A 1A 0A` | 0 |
| WebP | `52 49 46 46` ... `57 45 42 50` | 0, 8 |
| PDF | `25 50 44 46 2D` (`b"%PDF-"`) | 0 |

No `python-magic` / `python-magic-bin` dependency is added to
`pyproject.toml` or `requirements/dev.txt`. `magic` is never imported
anywhere in `src/examina/`.

## Consequences

- MIME detection is deterministic, dependency-free, and identical across
  Windows development machines and the Ubuntu-based CI/production
  environments — no platform-conditional behavior to test or document.
- The signature table only recognizes the nine types EXAMINA's pipeline
  currently cares about (4 allowed + 5 archive-bomb-check types). Any
  byte sequence not matching one of these signatures is treated as
  unrecognized and rejected via `InvalidMimeTypeError`, which is the
  conservative, correct behavior for a closed allowlist — EXAMINA never
  needs to identify arbitrary file types "in the wild."
- If a future phase needs broader MIME sniffing (e.g. supporting new
  input formats), that is a new ADR and a deliberate dependency addition
  with an accompanying CI/cross-platform verification step, not a silent
  expansion of this table.

## Specification Impact

None — `specs/DEPLOYMENT_SPEC_v1.0.md` does not mandate a specific MIME
detection library, only that detection reads bytes, not headers or
filenames. `specs/TECH_DEBT.md` notes this decision for future
reference.
