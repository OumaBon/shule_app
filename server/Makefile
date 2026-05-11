run:
	python3 run.py 

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

init-db:
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

migrate:
	flask db migrate -m "$(message)"

upgrade:
	flask db upgrade

seed:
	flask seed-db

reset-db:
	flask db downgrade base
	flask db upgrade