.PHONY: install test demo demo-record bench-seed bench-eval bench-mine lint

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests benchmark

demo:
	./demo/run_demo.sh

demo-record:
	vhs demo/demo.tape

bench-seed:
	python -m benchmark.build_seed

bench-eval:
	@if [ -z "$(DATASET)" ]; then echo "Usage: make bench-eval DATASET=benchmark/data/seed.jsonl PROVIDER=mock"; exit 1; fi
	mkdir -p runs
	python -m benchmark.run_eval \
		--dataset $(DATASET) \
		--out runs/$(notdir $(basename $(DATASET)))-$(or $(PROVIDER),anthropic).jsonl \
		--provider $(or $(PROVIDER),anthropic)
	python -m benchmark.metrics --run runs/$(notdir $(basename $(DATASET)))-$(or $(PROVIDER),anthropic).jsonl

bench-mine:
	@if [ -z "$(REPO)$(ORG)" ]; then echo "Usage: make bench-mine REPO=owner/name [or ORG=name] MAX=50"; exit 1; fi
	python -m benchmark.mine_reverts $(if $(REPO),--repo $(REPO),--org $(ORG)) --max $(or $(MAX),50)
