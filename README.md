# AssessIQ - AI-Powered Student Answer Evaluation System :

<div align="center">
  
  ![AssessIQ Logo](https://img.shields.io/badge/AssessIQ-AI%20Evaluation-1565c0?style=for-the-badge&logo=graduation-cap)
  
  [![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
  [![React](https://img.shields.io/badge/React-18.2-61dafb?style=flat-square&logo=react)](https://reactjs.org)
  [![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

_Automated evaluation of student answers using Natural Language Processing and Computer Vision_

</div>

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Scoring Algorithm](#-scoring-algorithm)
- [Screenshots](#-screenshots)
- [Contributors](#-contributors)

---

## 🎯 Overview

**AssessIQ** is an intelligent system designed to automate the evaluation of student answer sheets. It combines:

- **OCR Technology** for extracting text from handwritten answers
- **NLP Processing** for text normalization and keyword extraction
- **Semantic Analysis** using Sentence-BERT for meaning-based comparison
- **Diagram Evaluation** using structural similarity metrics
- **Hybrid Scoring** algorithm for accurate grading

This project is developed as part of the **6th Semester B.Tech Computer Science Engineering** curriculum.

---

## ✨ Features

### 🔤 Text Extraction (OCR)

- Multi-engine support: EasyOCR, Tesseract, PaddleOCR
- Image preprocessing: Noise removal, skew correction, thresholding
- PDF and image file support (PNG, JPG, TIFF, BMP)

### 📝 NLP Processing

- Text cleaning and normalization
- Tokenization and lemmatization
- Stopword removal
- Keyword extraction

### 🧠 Semantic Analysis

- Sentence-BERT embeddings (all-MiniLM-L6-v2)
- Cosine similarity calculation
- TF-IDF vectorization
- Jaccard similarity

### 📊 Diagram Evaluation

- SSIM (Structural Similarity Index)
- ORB feature matching
- Contour analysis
- Shape comparison

### 📈 Scoring System

- Hybrid scoring with dynamic weights
- Keyword coverage analysis
- Length penalty for incomplete answers
- Detailed feedback generation

### 🎨 Professional UI

- Modern React dashboard
- Material-UI components
- Responsive design
- Animated visualizations

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ASSESSIQ SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Frontend   │───▶│   Backend    │───▶│   Database   │      │
│  │   (React)    │◀───│   (FastAPI)  │◀───│   (SQLite)   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                              │                                  │
│         ┌────────────────────┴───────────────────┐             │
│         ▼                    ▼                   ▼             │
│  ┌─────────────┐    ┌─────────────────┐   ┌──────────────┐     │
│  │ OCR Service │    │ Semantic Service │   │Diagram Service│   │
│  │  (EasyOCR)  │    │(Sentence-BERT)  │   │   (OpenCV)   │    │
│  └─────────────┘    └─────────────────┘   └──────────────┘     │
│         │                    │                   │              │
│         └────────────────────┴───────────────────┘             │
│                              │                                  │
│                              ▼                                  │
│                    ┌─────────────────┐                         │
│                    │ Scoring Service │                         │
│                    │(Hybrid Algorithm)│                        │
│                    └─────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input (Image/PDF/Text)
        │
        ▼
┌───────────────┐
│ OCR Extraction│ ──▶ Extract text from images
└───────────────┘
        │
        ▼
┌───────────────┐
│ NLP Processing│ ──▶ Clean, tokenize, normalize text
└───────────────┘
        │
        ▼
┌───────────────┐
│Semantic Analysis│ ──▶ Generate embeddings, calculate similarity
└───────────────┘
        │
        ▼
┌───────────────┐
│Diagram Analysis│ ──▶ Compare visual elements (if applicable)
└───────────────┘
        │
        ▼
┌───────────────┐
│Hybrid Scoring │ ──▶ Combine scores, apply weights
└───────────────┘
        │
        ▼
    Final Result
```

---

## 🛠️ Tech Stack

### Backend

| Technology  | Purpose                   |
| ----------- | ------------------------- |
| Python 3.9+ | Core programming language |
| FastAPI     | REST API framework        |
| Pydantic    | Data validation           |
| SQLAlchemy  | ORM for database          |

### AI/ML

| Technology            | Purpose                       |
| --------------------- | ----------------------------- |
| EasyOCR               | Optical Character Recognition |
| spaCy                 | NLP processing                |
| Sentence-Transformers | Semantic embeddings           |
| OpenCV                | Image processing              |
| scikit-image          | SSIM calculation              |

### Frontend

| Technology    | Purpose            |
| ------------- | ------------------ |
| React 18      | UI framework       |
| Material-UI   | Component library  |
| Framer Motion | Animations         |
| Axios         | HTTP client        |
| Recharts      | Data visualization |

---

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- Node.js 16+ and npm
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/answer-evaluation.git
cd Answer_Evaluation
```

### Step 2: Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### Step 3: Environment Configuration

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings (optional)
```

### Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Return to root
cd ..
```

### Step 5: Initialize Database

```bash
python -c "from database.models import init_db; init_db()"
```

---

## 🚀 Usage

### Start Backend Server

```bash
# From project root
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Start Frontend Development Server

```bash
cd frontend
npm start
```

Frontend will be available at: http://localhost:3000

### Quick Test

```bash
# Test API health
curl http://localhost:8000/

# Test with sample evaluation
curl -X POST http://localhost:8000/api/v1/evaluate/text \
  -H "Content-Type: application/json" \
  -d '{
    "model_answer": "Photosynthesis is the process by which plants convert sunlight into energy.",
    "student_answer": "Plants use photosynthesis to make food using sunlight.",
    "question_type": "descriptive",
    "max_marks": 10
  }'
```

---

## 📖 API Documentation

### Endpoints

| Method   | Endpoint                | Description                 |
| -------- | ----------------------- | --------------------------- |
| `GET`    | `/`                     | Health check                |
| `POST`   | `/api/v1/upload`        | Upload files for evaluation |
| `POST`   | `/api/v1/evaluate`      | Evaluate uploaded files     |
| `POST`   | `/api/v1/evaluate/text` | Evaluate text directly      |
| `GET`    | `/api/v1/results`       | Get all evaluation results  |
| `GET`    | `/api/v1/results/{id}`  | Get specific result         |
| `DELETE` | `/api/v1/results/{id}`  | Delete result               |

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Text Evaluation

**Request:**

```json
POST /api/v1/evaluate/text
{
  "model_answer": "DNA is deoxyribonucleic acid, which carries genetic information.",
  "student_answer": "DNA stands for deoxyribonucleic acid and contains genetic info.",
  "question_type": "factual",
  "max_marks": 5
}
```

**Response:**

```json
{
  "evaluation_id": "abc123",
  "final_score": 85.5,
  "obtained_marks": 4.3,
  "grade": "excellent",
  "score_breakdown": {
    "semantic_score": 0.89,
    "keyword_score": 0.78,
    "diagram_score": null,
    "length_penalty": 0.02
  },
  "concepts": {
    "matched": ["DNA", "deoxyribonucleic acid", "genetic"],
    "missing": ["information", "carries"],
    "coverage_percentage": 75.0
  },
  "explanation": "Good understanding of DNA basics...",
  "suggestions": ["Include more detail about DNA's function"]
}
```

---

## 📁 Project Structure

```
Answer_Evaluation/
├── api/                          # Backend API
│   ├── main.py                   # FastAPI application
│   ├── routes/                   # API endpoints
│   │   ├── upload.py             # File upload handling
│   │   ├── evaluation.py         # Evaluation logic
│   │   └── results.py            # Results retrieval
│   └── services/                 # Core services
│       ├── ocr_service.py        # OCR processing
│       ├── nlp_service.py        # NLP operations
│       ├── semantic_service.py   # Semantic analysis
│       ├── diagram_service.py    # Diagram comparison
│       └── scoring_service.py    # Hybrid scoring
│
├── config/                       # Configuration
│   └── settings.py               # Application settings
│
├── database/                     # Database layer
│   └── models.py                 # SQLAlchemy models
│
├── frontend/                     # React frontend
│   ├── public/                   # Static assets
│   └── src/
│       ├── components/           # Reusable components
│       │   └── Layout.jsx        # Main layout
│       ├── pages/                # Page components
│       │   ├── Dashboard.jsx     # Home dashboard
│       │   ├── Evaluate.jsx      # Evaluation form
│       │   ├── Results.jsx       # Results display
│       │   └── History.jsx       # Past evaluations
│       └── services/
│           └── api.js            # API client
│
├── uploads/                      # Uploaded files (gitignored)
├── results/                      # Evaluation results
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## 📊 Scoring Algorithm

### Formula

```
Final_Score = (Semantic × W₁) + (Keyword × W₂) + (Diagram × W₃) - Length_Penalty
```

### Dynamic Weights by Question Type

| Question Type | Semantic (W₁) | Keyword (W₂) | Diagram (W₃) |
| ------------- | ------------- | ------------ | ------------ |
| Factual       | 0.50          | 0.40         | 0.10         |
| Descriptive   | 0.60          | 0.30         | 0.10         |
| Diagram       | 0.30          | 0.20         | 0.50         |
| Mixed         | 0.45          | 0.25         | 0.30         |

### Score Components

1. **Semantic Score** (0-1): Cosine similarity of Sentence-BERT embeddings
2. **Keyword Score** (0-1): Percentage of important keywords matched
3. **Diagram Score** (0-1): SSIM + ORB feature matching
4. **Length Penalty** (0-0.1): Deduction for too short/long answers

### Grading Scale

| Grade     | Percentage Range |
| --------- | ---------------- |
| Excellent | ≥ 85%            |
| Good      | 70% - 84%        |
| Average   | 50% - 69%        |
| Poor      | < 50%            |

---

## 📸 Screenshots

### Dashboard

_Modern dashboard with statistics and quick actions_

### Evaluation

_Step-by-step evaluation wizard with file upload_

### Results

_Detailed results with animated score visualization_

---

## 👥 Contributors

| Name        | Role      | Contact             |
| ----------- | --------- | ------------------- |
| [Kunal Ekare] | Developer | [kunalekare02@gmail.com] |
| [Soumya Dhole] | Full Stack Developer | [dholesm@rknec.edu] |
---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for OCR capabilities
- [Sentence-Transformers](https://www.sbert.net/) for semantic embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing framework
- [Material-UI](https://mui.com/) for beautiful React components

---

<div align="center">
  <p>Made with ❤️ for Academic Excellence</p>
  <p>© 2024 AssessIQ - All Rights Reserved</p>
</div>
