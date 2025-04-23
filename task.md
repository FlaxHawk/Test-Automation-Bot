# Automated Website Testing Bot – `task.md`

## Objective
Build a Python‑based bot that accepts a target website URL, automatically discovers pages & critical user flows, and then generates and executes Playwright‑driven tests orchestrated by Pytest. The bot should output rich HTML/JUnit reports, screenshots, videos, and traces.

## Scope
* **Browsers**: Chromium, Firefox, WebKit (headless & headed).
* **Discovery**: Depth‑controlled crawl; capture forms, links, SPA routes, and dynamic elements.
* **Tests**: Functional navigation, form submission, basic accessibility, HTTP error checks.
* **Artifacts**: Screenshots on failure, full video per test, Playwright traces.
* **CI/CD**: GitHub Actions workflow for every push + nightly regression run.

## High‑Level Architecture
1. **CLI/App Entry** – `bot run <url> [--depth 3] [--headful]`.
2. **Crawler** – Uses Playwright to explore and snapshot DOM/state.
3. **Test Generator** – Builds Page Object Models + Pytest test files from crawl data.
4. **Runner** – Executes tests in parallel via Pytest‑xdist.
5. **Reporter** – Merges Playwright HTML + JUnit; uploads artifacts.

```
┌────────┐   crawl   ┌──────────┐   generate   ┌──────────┐   run   ┌──────────┐
│  CLI   │──────────▶│  Crawler │─────────────▶│ Generator│────────▶│  Runner  │
└────────┘           └──────────┘              └──────────┘         └──────────┘
      ▲                                                                  ▲ 
      └──────────────────────── report ──────────────────────────────────┘
```

## Prerequisites
* Python ≥ 3.11
* `playwright` ≥ 1.44 (`pip install playwright && playwright install`)
* `pytest`, `pytest‑xdist`, `pytest‑html`
* Optional: `rich`, `poetry`, `black`, `ruff`

## Implementation Tasks
- [ ] **Project scaffolding**: Poetry, pre‑commit hooks, `src/`, `tests/` layout
- [ ] **Config schema**: `bot.yaml` + `pydantic` validation
- [ ] **Crawler module**: depth‑first traversal, SPA router support, concurrency
- [ ] **Page Object generator**: unique selectors, helper methods
- [ ] **Test template generator**: navigation + assertions skeleton
- [ ] **Runner orchestration**: parametrized browsers, parallel execution
- [ ] **Reporting**: combine Playwright HTML with Pytest‑html/JUnit outputs
- [ ] **CI workflow**: GitHub Actions, cache, matrix strategy
- [ ] **Demo site examples** & end‑to‑end smoke test

## Deliverables
1. Public Git repository
2. `task.md` (this spec)
3. Detailed `README.md` with setup & usage
4. Example HTML report + trace archive
5. Architecture diagram (PNG/SVG)

## Acceptance Criteria
| ID | Description | Metric |
|----|-------------|--------|
| AC‑1 | `bot run https://example.com` completes | ≤ 5 min on 4‑core runner |
| AC‑2 | Playwright report shows ≥ 95 % page coverage | % pages visited |
| AC‑3 | All generated tests pass against target | 0 failures |
| AC‑4 | Artifacts stored under `./reports/YYYY‑MM‑DD` | Structured dir |
| AC‑5 | CI run green on default branch | ✔ |

## Stretch Goals
* Visual regression snapshots & diff gallery
* AI‑assisted flaky selector healing
* Slack/Teams webhook notifications on failure
* Docker image for one‑command execution

## Suggested Timeline
| Phase | Duration | Owner |
|-------|----------|-------|
| Discovery & design | 3d | QA Lead |
| MVP implementation | 8d | Dev Team |
| Hardening & CI | 3d | Dev Team |
| Docs & hand‑off | 2d | QA Lead |

## References
* Playwright Docs – https://playwright.dev
* Pytest Docs – https://docs.pytest.org
* Playwright Pytest plugin – https://playwright.dev/python/docs/test-runners

---
_Revision 0 – April 22 2025_

