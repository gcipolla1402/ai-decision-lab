# Screenshot Capture Checklist

No screenshots were found in the project during the repository audit on 2026-11-11. Do not add generated or reconstructed screenshots as evidence of application behavior.

Capture these images manually from a real local run using synthetic documents only:

1. `dashboard.png`
   - Initial responsive dashboard and the three execution modes.
   - No browser developer tools, local filesystem paths, keys, or personal bookmarks visible.
2. `live-analysis.png`
   - A completed `GEMINI + JEV LIVE` result using a fully synthetic document.
   - Provider trace must show `google-gemini` and `typesafe-jev` without credentials or response payloads.
3. `execution-metrics.png`
   - Extraction, analysis, routing, and total timing cards from the same synthetic run.
   - Present the result as a single observation, not a benchmark.

Before saving each image:

- Clear session history or ensure every filename is synthetic.
- Confirm that summaries, indicators, and attention items contain no real person, company, client, or account data.
- Exclude `.env`, terminal windows, network request headers, API consoles, and browser autofill data.
- Crop unnecessary desktop chrome and verify the image at full resolution.
- Review image metadata before publication if the capture tool stores author or device information.

After the reviewed PNG files exist in this directory, add relative image links to the root README.
