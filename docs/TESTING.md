# Testing

Use `make alpha-check` for the reference Functional Internal Alpha.

The command runs the exact sequence documented in
[`ALPHA-VALIDATION.md`](ALPHA-VALIDATION.md).

Use `make demo` to retain the earlier governance self-test:

- `demo-goldenish` must be blocked;
- `demo-fixed` must pass its build-stage gates.

Use `npm ci && npx playwright install chromium && make alpha-first-paint` for
the runtime hero reliability matrix. The GitHub Actions workflow performs that
installation in a separate browser job.

`make release-check` is not expected to pass for the Alpha reference project
until real `release-candidate.json`, `live-verify.json` and
`monitoring-config.json` evidence exists.
