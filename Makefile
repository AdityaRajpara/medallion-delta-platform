.PHONY: setup run sample clean
setup:
	python -m pip install -e '.[dev]'
sample:
	medallion run --source sample --config config/local.json
run:
	medallion run --source treasury --config config/local.json
clean:
	python -c "from pathlib import Path; [__import__('shutil').rmtree(Path('data')/p, ignore_errors=True) for p in ('raw','bronze','silver','gold')]"
