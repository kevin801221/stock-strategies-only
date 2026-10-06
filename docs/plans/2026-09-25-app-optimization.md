# App optimization implementation plan

**Goal:** Make the existing stock strategy app responsive, observable, and resilient throughout strategy creation and screening.

**Architecture:** Keep Next.js and FastAPI, preserve the synchronous `/api/run` contract, and add bounded in-process screening jobs with progress polling and cooperative cancellation. Share result rendering and run controls between dashboard and strategy detail. Validate strategy inputs at the storage boundary and write files atomically.

**Tech stack:** Python, FastAPI, pytest, Next.js, React, TypeScript, Tailwind.

## Tasks and acceptance checks

- [x] Establish the Python test baseline and install existing frontend dependencies.
- [x] Add failing regression tests for strategy IDs, invalid numeric/boolean parameters, timestamps, and corrupt strategy files; fix `stock_strategies/loader.py`.
- [x] Add regression tests for evaluation scoring (zero wins must remain zero), then fix the defect.
- [x] Test screening job progress, failure isolation, cancellation, busy limits, and result parity; implement `api/services/runs.py` and additive API routes.
- [x] Build typed API helpers, shared run controls, and searchable/filterable result cards with stock details and CSV export.
- [x] Improve dashboard, navigation, strategy discovery/editing, and form validation with accessible mobile layouts and recoverable error states.
- [x] Add CI checks and document operating limits and new endpoints.
- [x] Run full pytest, frontend interaction tests, TypeScript checks, production build, local HTTP smoke checks, and `git diff --check`; review changes and record limitations. Browser visual checks remain unavailable (no connected browser).

## Design boundaries

Keep current scoring rules except demonstrated defects. Display only returned market and stock data. Jobs run sequentially to respect external API limits; one active job per process avoids duplicate expensive work. Completed jobs expire and are bounded in memory. Process-local storage requires one API worker and does not survive restart; document this instead of adding infrastructure. Do not connect unfinished V3.4 features or send notifications during verification.

## Verification

`uv run pytest -q`; `cd web && npm run check && npm run build`; `git diff --check`. Use isolated temporary strategy files and mocked external services for integration tests. Browser checks cover empty/error states, responsive navigation, strategy creation/editing, and result rendering when test fixtures are available.


## Verified outcome (2026-09-26)

- Original baseline: 110 Python tests.
- Final backend: 156 passing tests, including scoring/notification regressions, atomic persistence, validation, and job HTTP lifecycle. One upstream Starlette warning about the supported httpx TestClient transport remains.
- Frontend: 11 passing jsdom interaction/API tests; TypeScript and production build pass.
- Clean `npm ci` succeeds. `npm audit --omit=dev` reports zero known vulnerabilities after Next.js 15.5.26, React 19.0.8 and PostCSS 8.5.28 updates. The Next.js PostCSS override is explicit in package.json.
- Production homepage HTTP 200; isolated FastAPI health and defaults endpoints respond successfully.
- Independent review completed; findings fixed and re-reviewed with no substantive issues remaining.
- Browser plugin reported no available browsers, so no visual, mobile-device, or actual-browser end-to-end verification is claimed. Live external stock/AI/Google Sheet requests and notification sends were not exercised.
- Runtime remains a single-worker, process-local job service. Completed jobs expire after one hour; restart clears history. This work improves responsiveness and recovery without claiming a measured screening throughput improvement.
