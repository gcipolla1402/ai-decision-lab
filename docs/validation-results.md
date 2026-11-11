# Validation Results

Validation date: **2026-11-11**  
Environment: local Windows development workstation  
Scope: local automated checks and documentation of one previously observed real integration run

## Verified Local Environment

| Component | Verified version |
| --- | --- |
| Python | 3.14.2 |
| Node.js | 26.13.0 |
| npm | 11.20.0 |
| FastAPI | 0.162.4 |
| Pydantic | 2.14.3 |
| PyMuPDF | 1.28.2 |
| google-genai | 1.75.0 |
| typesafe-sdk | 0.7.5 |
| pytest | 8.4.2 |
| React / React DOM | 19.3.1 |
| Vite | 8.3.8 |
| TypeScript | 7.0.2 |
| Lucide React | 1.72.0 |

These are versions observed in the current local environment and lockfile, not a compatibility guarantee for every platform. The backend declares Python 3.12+ support; this audit executed on Python 3.14.2.

## Automated Validation

The final publication-preparation checks use no real provider calls.

| Check | Command | Result |
| --- | --- | --- |
| Backend tests | `python -m pytest -p no:cacheprovider` | **19 passed** in 0.89 s |
| TypeScript | `npm run typecheck` | **Passed** |
| Frontend build | `npm run build` | **Passed** in 1.03 s; 2,087 modules transformed |

Backend tests use mocks for Gemini and TypeSafe/JEV. They cover local extraction, provider selection, structured-response handling, invalid responses, routing, configuration, and API behavior without paid calls.

pytest emitted one deprecation warning from an installed `pytest-asyncio` plugin under Python 3.14. The package is not declared by this project's current development dependencies, and the warning did not affect the test result.

## Observed Real Gemini + JEV Execution

A single frontend execution was previously observed with a fully synthetic compliance-analysis PDF and the `GEMINI + JEV LIVE` mode.

| Item | Observation |
| --- | --- |
| Gemini provider | `google-gemini` |
| Gemini model | `gemini-2.5-flash` |
| JEV provider | `typesafe-jev` |
| JEV model alias | `jev-latest` |
| Route | `NEEDS_HUMAN_REVIEW` |
| Displayed confidence | 86% |
| Completeness | 20/100 |
| Extraction | 9.0 ms |
| Gemini analysis | 11,738.2 ms |
| JEV routing | 606.1 ms |
| Total | 12,355.8 ms |

The synthetic document deliberately contained inconsistent or missing evidence, including an expired fiscal document, an incomplete contract, a missing declaration, and a bank-account ownership mismatch.

This real call was **not repeated during the publication audit**, preventing additional API consumption. No raw provider response, credential, prompt, or document content is included in this report.

## Methodological Limitations

- This is one observed execution, not a benchmark or statistically meaningful sample.
- No warm-up policy, repetition count, percentile distribution, network-region control, or cost analysis was applied.
- Gemini performs structured document analysis; JEV performs typed routing. Their stage timings do not compare equivalent work.
- Provider aliases can resolve to different model versions over time.
- Latency varies with document length, provider load, network path, account tier, and model behavior.
- The displayed confidence is a provider output for the observed route, not a measured accuracy score.

No claim of improved speed, cost, precision, legal validity, or production readiness should be derived from this observation.

## Mocked Tests vs. Real Calls

**Mocked automated tests** validate application contracts, error paths, serialization, provider selection, and deterministic behavior. They are repeatable and do not verify external availability or model quality.

**Real calls** validate credentials, network access, SDK compatibility, provider availability, and end-to-end behavior at a point in time. They may incur usage and are intentionally excluded from the automated suite.
