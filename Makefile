lint:
	isort -rc .
_tests:
	flake8
	./scripts/permissions_checker.py
	mypy --no-strict-optional pulsar/ # --html-report .mypy-html pulsar/
	pytest --cov-report term-missing --cov-branch --cov=pulsar tests/
_docs:
	sphinx-build -M html docs/source docs/build
tests: _tests
docs: _docs
