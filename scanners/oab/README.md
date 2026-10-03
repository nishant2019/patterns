# OAB scanner

Opening Absorption Breakout scanner for 30-minute CVD data. See
[OAB_SPEC.md](OAB_SPEC.md) for the logic, parameters and results.

```bash
# Scan one day
python scanners/oab/oab_scanner.py data/CVD_Scanner_01-10-2026 \
    -o scanners/oab/results/oab_01-10-2026.csv

# Validate across one or more days (sweep + out-of-sample check)
python scanners/oab/validate.py data/CVD_Scanner_01-10-2026 data/CVD_Scanner_<date> ...
```

Python 3 standard library only. Parameters live in `PARAMS` in
`oab_scanner.py`.
