# Changelog

All notable changes to EXAMINA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.6.0] — Hardening and beta preparation

Production readiness pass ahead of the research beta: CORS restricted to
configured origins, security response headers on every API response, a
documented security review of the upload pipeline (no path-traversal
extraction, metadata-only archive inspection), a clean dependency
security audit wired into CI, reproducible frozen dependencies,
production deployment configuration (Nginx, Caddy, systemd), a beta
guide for journalists, and a complete README. No new application
features.

## [0.5.0] — React UI complete

A complete single-page web interface: drag-and-drop upload, invite-code
gating, and a full Digital Evidence Report view — verdict and
recommendation, "what would change this conclusion," processing history,
forensic evidence with correlated-family grouping, a five-dimension
confidence breakdown, and an in-report feedback form.

## [0.4.0] — FastAPI application with auth, persistence, admin

The EXAMINA API: invite-code and admin-token authentication, per-route
rate limiting, report persistence with 24-hour expiry, a feedback and
incorrect-analysis reporting endpoint, and an admin overview surface for
monitoring beta usage.

## [0.3.0] — 7-step upload security pipeline

Every uploaded file passes through size, MIME-signature, filename
sanitization, hashing, malware scanning, and archive-bomb checks before
any analysis begins — untrusted input is never trusted by default.

## [0.2.0] — Report engine with confidence translation and decision model

The engine that turns PRISM's forensic output into a Digital Evidence
Report: evidence clustering into families, a five-dimension plain-language
confidence translation, verdict determination, and processing-history
reconstruction — every finding traceable back to its supporting signal.

## [0.1.0] — BridgeClient abstraction with Local/Remote implementations

The one-way, typed contract between EXAMINA and PRISM's forensic
reasoning engine, plus the foundation of EXAMINA's forbidden-vocabulary
language enforcement.

## [0.0.1] — Repository bootstrap, frozen specifications, CI/CD

The frozen specification set (constitution, product requirements,
report schema, language rules, decision model, and more), continuous
integration (lint, type-check, unit tests, secret scanning), and branch
protection that every later phase builds against.
