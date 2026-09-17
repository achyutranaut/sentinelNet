# SentinelNet Developer Automation Makefile (MLOps Workflow)

.PHONY: help install test train api dashboard docker-up docker-down clean

help:
	@echo "SentinelNet MLOps Commands:"
	@echo "  make install     - Install required dependencies"
	@echo "  make test        - Run complete 4-pillar ML test suite"
	@echo "  make train       - Run Continuous Training (CT) pipeline"
	@echo "  make api         - Start FastAPI high-throughput scoring service"
	@echo "  make dashboard   - Launch Streamlit SOC Command Center"
	@echo "  make docker-up   - Build and start containerized stack"
	@echo "  make docker-down - Stop containers"
	@echo "  make clean       - Remove cached artifacts and temporary logs"

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest tests/ -v

train:
	PYTHONPATH=. python3 src/pipeline.py

train-quick:
	PYTHONPATH=. python3 src/pipeline.py --quick

api:
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	streamlit run src/dashboard/app.py

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
