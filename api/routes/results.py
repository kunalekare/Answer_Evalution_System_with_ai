"""
Results Routes
===============
Handles retrieval and management of evaluation results.
Provides endpoints for viewing, searching, and exporting results.
"""

import os
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.settings import settings

router = APIRouter()


# ========== Pydantic Models ==========
class ResultSummary(BaseModel):
    """Summary of an evaluation result."""
    evaluation_id: str
    final_score: float
    max_marks: int
    obtained_marks: float
    grade: str
    timestamp: str


class ResultsListResponse(BaseModel):
    """Response for listing multiple results."""
    success: bool
    count: int
    results: List[ResultSummary]


class ExportFormat(BaseModel):
    """Export format options."""
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")


# ========== In-Memory Storage (for demo) ==========
# In production, use a proper database
evaluation_results_store = {}


# ========== Helper Functions ==========
def save_result(evaluation_id: str, result: dict):
    """Save evaluation result to storage."""
    evaluation_results_store[evaluation_id] = {
        **result,
        "saved_at": datetime.now().isoformat()
    }
    
    # Also save to file for persistence
    results_dir = Path(settings.UPLOAD_DIR) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = results_dir / f"{evaluation_id}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results_store[evaluation_id], f, indent=2)


def load_result(evaluation_id: str) -> Optional[dict]:
    """Load evaluation result from storage."""
    # Try memory first
    if evaluation_id in evaluation_results_store:
        return evaluation_results_store[evaluation_id]
    
    # Try file storage
    result_file = Path(settings.UPLOAD_DIR) / "results" / f"{evaluation_id}.json"
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
            evaluation_results_store[evaluation_id] = result
            return result
    
    return None


def load_all_results() -> List[dict]:
    """Load all evaluation results."""
    results = []
    results_dir = Path(settings.UPLOAD_DIR) / "results"
    
    if results_dir.exists():
        for result_file in results_dir.glob("*.json"):
            with open(result_file, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
    
    return results


# ========== API Endpoints ==========
@router.get("/", response_model=ResultsListResponse)
async def list_results(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    max_score: Optional[float] = Query(default=None, ge=0, le=100),
    grade: Optional[str] = Query(default=None)
):
    """
    List all evaluation results with optional filtering.
    
    **Filters:**
    - limit: Maximum number of results to return
    - offset: Number of results to skip
    - min_score: Minimum score filter
    - max_score: Maximum score filter
    - grade: Filter by grade (excellent, good, average, poor)
    """
    
    all_results = load_all_results()
    
    # Apply filters
    filtered_results = all_results
    
    if min_score is not None:
        filtered_results = [r for r in filtered_results if r.get("final_score", 0) >= min_score]
    
    if max_score is not None:
        filtered_results = [r for r in filtered_results if r.get("final_score", 0) <= max_score]
    
    if grade:
        filtered_results = [r for r in filtered_results if r.get("grade", "").lower() == grade.lower()]
    
    # Sort by timestamp (newest first)
    filtered_results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Apply pagination
    paginated_results = filtered_results[offset:offset + limit]
    
    # Convert to summaries
    summaries = [
        ResultSummary(
            evaluation_id=r.get("evaluation_id", ""),
            final_score=r.get("final_score", 0),
            max_marks=r.get("max_marks", 10),
            obtained_marks=r.get("obtained_marks", 0),
            grade=r.get("grade", "unknown"),
            timestamp=r.get("timestamp", "")
        )
        for r in paginated_results
    ]
    
    return ResultsListResponse(
        success=True,
        count=len(filtered_results),
        results=summaries
    )


@router.get("/{evaluation_id}")
async def get_result(evaluation_id: str):
    """
    Get detailed result for a specific evaluation.
    """
    result = load_result(evaluation_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Result for evaluation {evaluation_id} not found"
        )
    
    return {
        "success": True,
        "data": result
    }


@router.post("/{evaluation_id}/save")
async def save_evaluation_result(evaluation_id: str, result: dict):
    """
    Save an evaluation result for later retrieval.
    """
    save_result(evaluation_id, result)
    
    return {
        "success": True,
        "message": f"Result for evaluation {evaluation_id} saved successfully"
    }


@router.delete("/{evaluation_id}")
async def delete_result(evaluation_id: str):
    """
    Delete an evaluation result.
    """
    # Remove from memory
    if evaluation_id in evaluation_results_store:
        del evaluation_results_store[evaluation_id]
    
    # Remove from file storage
    result_file = Path(settings.UPLOAD_DIR) / "results" / f"{evaluation_id}.json"
    if result_file.exists():
        os.remove(result_file)
        return {
            "success": True,
            "message": f"Result {evaluation_id} deleted successfully"
        }
    
    raise HTTPException(
        status_code=404,
        detail=f"Result {evaluation_id} not found"
    )


@router.get("/{evaluation_id}/export")
async def export_result(
    evaluation_id: str,
    format: str = Query(default="json", pattern="^(json|csv)$")
):
    """
    Export evaluation result in specified format.
    
    **Formats:**
    - json: JSON format (default)
    - csv: CSV format
    """
    result = load_result(evaluation_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Result for evaluation {evaluation_id} not found"
        )
    
    if format == "csv":
        # Convert to CSV format
        headers = ["evaluation_id", "final_score", "max_marks", "obtained_marks", "grade", "timestamp"]
        values = [
            result.get("evaluation_id", ""),
            str(result.get("final_score", 0)),
            str(result.get("max_marks", 10)),
            str(result.get("obtained_marks", 0)),
            result.get("grade", ""),
            result.get("timestamp", "")
        ]
        
        csv_content = ",".join(headers) + "\n" + ",".join(values)
        
        return {
            "success": True,
            "format": "csv",
            "content": csv_content
        }
    
    return {
        "success": True,
        "format": "json",
        "content": result
    }


@router.get("/stats/summary")
async def get_statistics():
    """
    Get summary statistics for all evaluations.
    """
    all_results = load_all_results()
    
    if not all_results:
        return {
            "success": True,
            "data": {
                "total_evaluations": 0,
                "average_score": 0,
                "grade_distribution": {},
                "message": "No evaluations found"
            }
        }
    
    # Calculate statistics
    total = len(all_results)
    scores = [r.get("final_score", 0) for r in all_results]
    average_score = sum(scores) / total if total > 0 else 0
    
    # Grade distribution
    grades = {}
    for r in all_results:
        grade = r.get("grade", "unknown")
        grades[grade] = grades.get(grade, 0) + 1
    
    return {
        "success": True,
        "data": {
            "total_evaluations": total,
            "average_score": round(average_score, 2),
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "grade_distribution": grades
        }
    }
