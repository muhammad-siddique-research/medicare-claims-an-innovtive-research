.PHONY: setup test demo run lint
setup:
	python -m pip install -e '.[dev]'
test:
	pytest -q
lint:
	ruff check src tests
demo:
	python -m medicare_claims.cli make-fixture --dest data/toy
	python -m medicare_claims.cli run --data-dir data/toy --year 2022 --output-dir reports/toy
run:
	python -m medicare_claims.cli run --data-dir data/raw --year 2022 --output-dir reports/cms_2022
