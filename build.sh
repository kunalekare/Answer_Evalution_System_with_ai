#!/usr/bin/env bash
# Render Build Script for AssessIQ
# This script runs during the build phase

set -e  # Exit on error

echo "=== Installing Python dependencies ==="
pip install --upgrade pip

# Install CPU-only PyTorch first from PyTorch index (saves ~700MB vs full CUDA build)
pip install torch==2.1.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

echo "=== Downloading NLTK data ==="
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

echo "=== Creating directories ==="
mkdir -p uploads/student_answers uploads/model_answers uploads/processed uploads/results uploads/evaluations logs temp

echo "=== Build complete ==="
