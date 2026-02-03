#!/usr/bin/env bash
# Render Build Script for AssessIQ
# This script runs during the build phase

set -e  # Exit on error

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Downloading NLTK data ==="
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

echo "=== Creating directories ==="
mkdir -p uploads/student_answers uploads/model_answers uploads/processed uploads/results uploads/evaluations logs temp

echo "=== Build complete ==="
