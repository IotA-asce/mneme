# Testing

Validated with targeted tests covering:

- review storage migration and round trip,
- durable proposal creation,
- correction apply and supersession,
- forget suppression,
- confirmation upgrade,
- confirmed-vs-confirmed conflict preservation,
- reject without mutation,
- `mneme review` JSON commands,
- default benchmark suite and L3 evidence,
- UI review rendering.

Full verification was run with `python scripts/dev_check.py`.
