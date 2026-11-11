# Public Repository Checklist

This checklist supports a manual publication decision. It is not legal, security, privacy, or regulatory approval.

## Credential Security

- [x] Root `.env` is excluded by `.gitignore`.
- [x] `.env.*` files are excluded, with `.env.example` explicitly retained.
- [x] `.env.example` contains placeholders and disabled live-provider flags.
- [x] Common private-key, certificate, keystore, credential JSON, database, upload, and log patterns are ignored.
- [x] Source scan found no configured hardcoded-key, token, or private-key patterns.
- [ ] Manually inspect the final GitHub file list before publication.
- [ ] If this directory ever had Git history, inspect all history for removed secrets before publishing it.
- [ ] Rotate any credential that may previously have been copied into a tracked file, terminal recording, or screenshot.

## Synthetic Data and Privacy

- [x] Included example documents identify themselves as synthetic.
- [x] Automated tests use fictional content and placeholders.
- [ ] Review every future example and screenshot for names, addresses, account data, client identifiers, and document metadata.
- [ ] Confirm that no real uploaded document, generated response, browser session history, or local log is included.

## Authorship and Right to Publish

- [x] README describes the repository as an independently authored personal project.
- [ ] Author must manually confirm ownership of every source file, prompt, example, visual asset, and documented result.
- [ ] Confirm there is no confidential information, employer-owned material, client work, or restricted taxonomy.
- [ ] Review employment, contractor, confidentiality, and invention-assignment obligations if applicable.
- [ ] Obtain qualified advice where ownership or publication rights are uncertain.

## Dependency Licenses

- [ ] Review licenses and notices for all direct and transitive Python dependencies.
- [ ] Review licenses and notices for all direct and transitive npm dependencies.
- [ ] Select and add an appropriate repository `LICENSE`; none is currently committed.
- [ ] Add attribution or notice files where a dependency license requires them.

## Screenshots

- [ ] Capture `docs/screenshots/dashboard.png` from the real local application.
- [ ] Capture `docs/screenshots/live-analysis.png` using only a synthetic document.
- [ ] Capture `docs/screenshots/execution-metrics.png` from the same synthetic run.
- [ ] Review pixels and metadata for credentials, personal data, filesystem paths, bookmarks, terminals, and API consoles.
- [ ] Add README image links only after reviewed image files exist.

## Tests and Documentation

- [x] Backend pytest suite is present and provider calls are mocked.
- [x] Frontend typecheck and production build scripts are present.
- [x] README documents architecture, modes, setup, environment, testing, limitations, and the author.
- [x] The real integration result is labeled as a single-run observation rather than a benchmark.
- [x] Local checks were rerun on 2026-11-11 and recorded in `docs/validation-results.md`.
- [ ] Rerun all local checks again immediately before the eventual publication action.

## Excluded and Generated Files

- [x] `.venv`, `venv`, `node_modules`, `dist`, caches, coverage, logs, uploads, storage, databases, and temporary files are ignored.
- [x] TypeScript incremental build metadata is ignored.
- [ ] Manually verify that no important source, example, lockfile, documentation, or configuration template is excluded.
- [ ] Confirm `package-lock.json` remains included for reproducible frontend installation.

## Manual Review

- [ ] Read the repository from the perspective of an unauthenticated public visitor.
- [ ] Check all Markdown links and Mermaid rendering on GitHub.
- [ ] Confirm commands work in a clean directory without relying on global packages.
- [ ] Review API error messages and logs for safe disclosure.
- [ ] Confirm documented model names and provider behavior remain current.

## GitHub Repository Setup

- [ ] Create `gcipolla1402/ai-decision-lab` manually with the intended visibility.
- [ ] Add a concise repository description and relevant topics.
- [ ] Configure the default branch and branch protection as appropriate.
- [ ] Enable secret scanning, dependency alerts, and automated security updates when available.
- [ ] Add CI after reviewing workflow permissions and third-party actions.
- [ ] Push only after every required item above has been reviewed by the author.
