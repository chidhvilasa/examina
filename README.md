# EXAMINA — Digital Evidence Intelligence for Journalists

EXAMINA gives journalists and photo editors a fast, evidence-based read
on a digital file's likely processing history — without requiring them
to become forensic analysts, and without ever telling them what to
publish. It is the interface between PRISM's forensic reasoning engine
and a newsroom deadline: upload a file, get a structured, traceable
report in the time it takes to make an editorial decision.

## What EXAMINA Does

- Reconstructs the probable processing history of an uploaded image or
  PDF, translating PRISM's forensic signals into plain language a
  non-specialist editor can read, question, and act on.
- Traces every finding back to the underlying signal that supports it,
  so a skeptical reader can always ask "how do you know that?" and get a
  concrete answer.
- States its own confidence explicitly, across five separate dimensions,
  rather than presenting a single verdict with no accompanying
  uncertainty.

## What EXAMINA Does Not Do

- EXAMINA does not make publication decisions. It produces evidence and
  analysis for a human editor to weigh — the decision always remains
  theirs.
- EXAMINA does not analyze audio or video files.
- EXAMINA does not reimplement forensic analysis — all signal
  extraction, contradiction detection, and confidence scoring happens in
  PRISM; EXAMINA translates and presents PRISM's output.
- EXAMINA is a research beta, not long-hardened production software —
  see `docs/BETA_GUIDE.md` for its current limitations.

## Supported File Types

JPEG, PNG, WebP, PDF — max 20MB each.

## Quick Start (Development)

```
git clone https://github.com/chidhvilasa/examina.git
cd examina
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements/frozen_v060.txt
pip install -e .
cp .env.example .env
# Edit .env with your invite code
python -m examina.api.main

# In a second terminal:
cd src/examina/ui
npm ci
npm run dev
# Open http://localhost:5173
```

## Running Tests

```
pytest tests/ -v
```

## Architecture

EXAMINA is the application layer: upload security pipeline, report
engine, API, and UI. PRISM is the forensic reasoning engine — the only
component that extracts signals, detects contradictions, and generates
hypotheses. The two communicate through a one-way, typed bridge contract
(`specs/BRIDGE_SPEC_v1.1.md`); EXAMINA never imports PRISM internals, and
PRISM never depends on EXAMINA. See `specs/` for the complete frozen
specification set — `CONSTITUTION_v1.0.md` in particular defines the
non-negotiable principles every phase of this codebase is built against.

## Deployment

See `deployment/README.md` for the complete production deployment guide
(Nginx/Caddy, systemd, environment variables, TLS, monitoring).

## Research Beta

See `docs/BETA_GUIDE.md` for what EXAMINA is, who it's for, how to read
a report, and its current limitations.

## Third Party Licenses

EXAMINA uses PRISM as its forensic reasoning engine, via the bridge
contract defined in `specs/BRIDGE_SPEC_v1.1.md`. PRISM is developed and
licensed independently — see PRISM's own repository for its license and
documentation.

## License

[License TBD]
