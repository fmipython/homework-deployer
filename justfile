venv:
    . .venv/bin/activate

lint: venv
    uv run ruff check homework_deployer homework-deployer.py --fix
    uv run ruff format homework_deployer homework-deployer.py
    uv run mypy homework_deployer homework-deployer.py --ignore-missing-imports
    uv run complexipy .

test: venv
    python3 -m unittest discover -s tests

push: venv lint test
    git push

coverage: venv
    coverage run --source=homework_deployer -m unittest discover -s tests
    coverage report -m --fail-under 75 --sort=cover

run: venv
    python3 -m homework_deployer

build: 
    uv build

clean:
    rm -rf __pycache__
    rm -rf .mypy_cache
    rm -rf dist
    rm -rf homework_deployer.egg-info
    rm -rf *.log*