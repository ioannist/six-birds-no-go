.PHONY: test reproduce

test:
	pytest -q

reproduce:
	python3 scripts/run_t19_repro_pipeline.py
