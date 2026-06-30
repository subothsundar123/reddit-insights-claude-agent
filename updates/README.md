# Connector Update Instructions

Every material connector release must include:

1. A new dated file named `YYYY-MM-DD-HHMM-short-name.md`.
2. Published date and time with timezone.
3. Connector version and minimum commit.
4. What changed.
5. Required installation, data-refresh and verification actions.
6. Any Claude Desktop restart requirement.
7. An update to `updates/latest.md` pointing to the new dated file.

The `/update-connector` command pulls `main`, reads `updates/latest.md` and applies the newest dated instruction. Historical update instructions are retained for auditing and troubleshooting.
