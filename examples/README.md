# Example outputs: invented toy-data demonstration only

Run locally:

```bash
python -m medicare_claims.cli make-fixture --dest data/toy
python -m medicare_claims.cli run --data-dir data/toy --year 2022 --output-dir reports/toy
```

All resulting model coefficients and charts use invented fixture data, **NOT official CMS files or actual patient records**. They must not be cited as clinical, population or policy findings. The public-facing examples are generated on demand and not included as real research findings.
