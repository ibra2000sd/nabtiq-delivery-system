---
name: website-migration
description: Audits a client's current public website and creates a migration/redirect plan before replacement. Uses the same-origin crawler, compares current URLs and claims with the new sitemap, and prevents silently losing valuable content or indexed routes.
---
# website-migration

Dry-run `scripts/crawl_site.py <project> <https-url>` first. After operator approval use `--execute`;
the crawler stays on the exact origin, honours robots rules, and caps the page count. Review the resulting
inventory against supplied client files and the truth ledger. Public content is a source to verify, not proof.

Produce a route-by-route decision: retain, consolidate, redirect, or retire. Preserve canonical intent,
language pairing, and contact conversions. Do not change DNS or deploy. Request migration review and
record unresolved ownership, email, analytics, form, and redirect questions as blockers.
