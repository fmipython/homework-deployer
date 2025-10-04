venv:
    . .venv/bin/activate

init:
    python3 -m venv .venv
    venv
    pip install -r requirements.txt

lint: venv
    python3 -m pylint homework_deployer homework-deployer.py --fail-under 9
    mypy homework_deployer homework-deployer.py --ignore-missing-imports
    flake8 homework_deployer homework-deployer.py
    complexipy .

test: venv
    python3 -m unittest discover -s tests

push: venv lint test
    git push

coverage: venv
    coverage run --source=homework_deployer -m unittest discover -s tests
    coverage report -m --fail-under 75 --sort=cover

run: venv
    python3 -m homework_deployer