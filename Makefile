lint:
	isort -rc .
test:
	flake8
	mypy pulsar/
	pytest --cov-report term-missing --cov-branch --cov=pulsar tests/
tests: test
