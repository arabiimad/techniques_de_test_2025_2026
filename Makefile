# Makefile pour le projet Triangulator
# TP Techniques de Test 2025/2026

.PHONY: test unit_test perf_test coverage lint doc clean install

# Variables
PYTHON = python3
PYTEST = pytest
COVERAGE = coverage
RUFF = ruff
PDOC = pdoc3

# Installation des dépendances
install:
	pip install -r requirements.txt
	pip install -r dev_requirements.txt

# Lance tous les tests (unitaires + intégration + performance)
test:
	PYTHONPATH=src $(PYTEST) tests/ -v

# Lance tous les tests sauf les tests de performance
unit_test:
	PYTHONPATH=src $(PYTEST) tests/ -v -m "not performance"

# Lance uniquement les tests de performance
perf_test:
	PYTHONPATH=src $(PYTEST) tests/ -v -m "performance"

# Génère un rapport de couverture de code
coverage:
	PYTHONPATH=src $(COVERAGE) run -m pytest tests/ -m "not performance"
	$(COVERAGE) report -m
	$(COVERAGE) html
	@echo "Rapport HTML généré dans htmlcov/index.html"

# Valide la qualité du code avec ruff
lint:
	$(RUFF) check src/ tests/

# Corrige automatiquement les problèmes de style
lint-fix:
	$(RUFF) check src/ tests/ --fix

# Génère la documentation HTML
doc:
	PYTHONPATH=src $(PDOC) --html --output-dir docs src/triangulator --force
	@echo "Documentation générée dans docs/"

# Lance le serveur en mode développement
run:
	PYTHONPATH=src FLASK_APP=src/triangulator/app.py FLASK_DEBUG=1 flask run --port 5001

# Nettoie les fichiers générés
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov docs
	rm -rf src/**/__pycache__ tests/**/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Affiche l'aide
help:
	@echo "Commandes disponibles:"
	@echo "  make install    - Installe les dépendances"
	@echo "  make test       - Lance tous les tests"
	@echo "  make unit_test  - Lance les tests unitaires (sans performance)"
	@echo "  make perf_test  - Lance les tests de performance"
	@echo "  make coverage   - Génère le rapport de couverture"
	@echo "  make lint       - Vérifie la qualité du code"
	@echo "  make lint-fix   - Corrige automatiquement les problèmes de style"
	@echo "  make doc        - Génère la documentation"
	@echo "  make run        - Lance le serveur en mode dev"
	@echo "  make clean      - Nettoie les fichiers générés"
