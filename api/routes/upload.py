"""
Upload Routes
==============
Handles file upload operations for student answers and model answer keys.
Supports PDF and image files with validation and preprocessing.
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import aiofiles

from config.settings import settings

router = APIRouter()


# ========== Pydantic Models ==========
class UploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    message: str
    data: Optional[dict] = None


class FileInfo(BaseModel):
    """Information about an uploaded file."""
    file_id: str
    original_name: str
    saved_path: str
    file_type: str
    file_size: int
    upload_time: str


# ========== Helper Functions ==========
def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """Check if file size is within limits."""
    return file_size <= settings.MAX_FILE_SIZE


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent overwrites."""
    ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = Path(original_filename).stem[:20]  # Limit name length
    return f"{safe_name}_{timestamp}_{unique_id}{ext}"


async def save_upload_file(upload_file: UploadFile, destination: str) -> int:
    """
    Save uploaded file to destination asynchronously.
    Returns the file size in bytes.
    """
    file_size = 0
    async with aiofiles.open(destination, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # Read 1MB chunks
            file_size += len(content)
            if file_size > settings.MAX_FILE_SIZE:
                # Clean up partial file
                await out_file.close()
                os.remove(destination)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
            await out_file.write(content)
    return file_size


# ========== API Endpoints ==========
@router.post("/", response_model=UploadResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    model_answer: UploadFile = File(..., description="Model answer key (image/PDF)"),
    student_answer: Optional[UploadFile] = File(None, description="Student answer sheet (image/PDF)"),
    student_text: Optional[str] = Form(None, description="Student answer as text (alternative to image)"),
    question_type: str = Form("descriptive", description="Type of question: factual, descriptive, diagram"),
    subject: Optional[str] = Form(None, description="Subject/Topic of the question"),
    max_marks: int = Form(10, description="Maximum marks for this question")
):
    """
    Upload model answer and student answer for evaluation.
    
    **Workflow:**
    1. Upload model answer key (required) - Image or PDF
    2. Upload student answer (optional) - Image or PDF  
    3. OR provide student answer as text
    4. Files are validated and saved
    5. Returns file IDs for evaluation
    
    **Supported formats:** PDF, PNG, JPG, JPEG, TIFF, BMP
    """
    
    # Validate at least one student answer is provided
    if student_answer is None and student_text is None:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a student answer file or text"
        )
    
    # Validate model answer file
    if not validate_file_extension(model_answer.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type for model answer. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate student answer file if provided
    if student_answer and not validate_file_extension(student_answer.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type for student answer. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    try:
        # Generate unique evaluation ID
        evaluation_id = str(uuid.uuid4())
        
        # Create evaluation directory
        eval_dir = os.path.join(settings.UPLOAD_DIR, "evaluations", evaluation_id)
        os.makedirs(eval_dir, exist_ok=True)
        
        # Save model answer
        model_filename = generate_unique_filename(model_answer.filename)
        model_path = os.path.join(eval_dir, f"model_{model_filename}")
        model_size = await save_upload_file(model_answer, model_path)
        
        # Save student answer if file provided
        student_path = None
        student_size = 0
        if student_answer:
            student_filename = generate_unique_filename(student_answer.filename)
            student_path = os.path.join(eval_dir, f"student_{student_filename}")
            student_size = await save_upload_file(student_answer, student_path)
        
        # Save student text if provided
        if student_text:
            text_path = os.path.join(eval_dir, "student_answer.txt")
            async with aiofiles.open(text_path, 'w', encoding='utf-8') as f:
                await f.write(student_text)
            student_path = text_path
            student_size = len(student_text.encode('utf-8'))
        
        # Prepare response data
        response_data = {
            "evaluation_id": evaluation_id,
            "model_answer": {
                "filename": model_answer.filename,
                "saved_path": model_path,
                "size_bytes": model_size
            },
            "student_answer": {
                "type": "text" if student_text else "file",
                "filename": student_answer.filename if student_answer else "student_answer.txt",
                "saved_path": student_path,
                "size_bytes": student_size
            },
            "metadata": {
                "question_type": question_type,
                "subject": subject,
                "max_marks": max_marks,
                "upload_time": datetime.now().isoformat()
            }
        }
        
        return UploadResponse(
            success=True,
            message="Files uploaded successfully. Ready for evaluation.",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload files: {str(e)}"
        )


@router.post("/model-answer", response_model=UploadResponse)
async def upload_model_answer(
    file: UploadFile = File(..., description="Model answer key (image/PDF)"),
    subject: Optional[str] = Form(None),
    question_number: Optional[str] = Form(None),
    max_marks: int = Form(10)
):
    """
    Upload only the model answer key for storage.
    This can be reused for multiple student evaluations.
    """
    
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    try:
        # Generate unique ID
        file_id = str(uuid.uuid4())
        
        # Save to model answers directory
        save_dir = os.path.join(settings.UPLOAD_DIR, "model_answers")
        os.makedirs(save_dir, exist_ok=True)
        
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(save_dir, f"{file_id}_{filename}")
        file_size = await save_upload_file(file, file_path)
        
        return UploadResponse(
            success=True,
            message="Model answer uploaded successfully",
            data={
                "file_id": file_id,
                "filename": filename,
                "path": file_path,
                "size_bytes": file_size,
                "subject": subject,
                "question_number": question_number,
                "max_marks": max_marks
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload model answer: {str(e)}"
        )


@router.post("/student-answer", response_model=UploadResponse)
async def upload_student_answer(
    file: UploadFile = File(..., description="Student answer sheet (image/PDF)"),
    student_id: Optional[str] = Form(None),
    student_name: Optional[str] = Form(None)
):
    """
    Upload only the student answer for storage.
    """
    
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    try:
        # Generate unique ID
        file_id = str(uuid.uuid4())
        
        # Save to student answers directory
        save_dir = os.path.join(settings.UPLOAD_DIR, "student_answers")
        os.makedirs(save_dir, exist_ok=True)
        
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(save_dir, f"{file_id}_{filename}")
        file_size = await save_upload_file(file, file_path)
        
        return UploadResponse(
            success=True,
            message="Student answer uploaded successfully",
            data={
                "file_id": file_id,
                "filename": filename,
                "path": file_path,
                "size_bytes": file_size,
                "student_id": student_id,
                "student_name": student_name
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload student answer: {str(e)}"
        )


@router.delete("/{evaluation_id}")
async def delete_evaluation_files(evaluation_id: str):
    """
    Delete all files associated with an evaluation.
    """
    eval_dir = os.path.join(settings.UPLOAD_DIR, "evaluations", evaluation_id)
    
    if not os.path.exists(eval_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation {evaluation_id} not found"
        )
    
    try:
        shutil.rmtree(eval_dir)
        return {
            "success": True,
            "message": f"Evaluation {evaluation_id} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete evaluation: {str(e)}"
        )


@router.get("/{evaluation_id}/extract-text")
async def extract_text_from_upload(evaluation_id: str):
    """
    Extract and return OCR text from uploaded files.
    This allows users to preview what text was extracted before evaluation.
    """
    eval_dir = os.path.join(settings.UPLOAD_DIR, "evaluations", evaluation_id)
    
    if not os.path.exists(eval_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation {evaluation_id} not found"
        )
    
    try:
        from api.services.ocr_service import OCRService
        
        # Initialize OCR service
        ocr = OCRService()
        
        # Find files
        files = os.listdir(eval_dir)
        model_file = next((f for f in files if f.startswith("model_")), None)
        student_file = next((f for f in files if f.startswith("student_") or f == "student_answer.txt"), None)
        
        result = {
            "evaluation_id": evaluation_id,
            "model_answer": None,
            "student_answer": None
        }
        
        # Extract model answer text
        if model_file:
            model_path = os.path.join(eval_dir, model_file)
            try:
                model_text = ocr.extract_text(model_path)
                result["model_answer"] = {
                    "filename": model_file,
                    "text": model_text,
                    "char_count": len(model_text),
                    "word_count": len(model_text.split())
                }
            except Exception as e:
                result["model_answer"] = {
                    "filename": model_file,
                    "error": str(e)
                }
        
        # Extract student answer text
        if student_file:
            student_path = os.path.join(eval_dir, student_file)
            try:
                if student_file.endswith('.txt'):
                    with open(student_path, 'r', encoding='utf-8') as f:
                        student_text = f.read()
                else:
                    student_text = ocr.extract_text(student_path)
                
                result["student_answer"] = {
                    "filename": student_file,
                    "text": student_text,
                    "char_count": len(student_text),
                    "word_count": len(student_text.split())
                }
            except Exception as e:
                result["student_answer"] = {
                    "filename": student_file,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract text: {str(e)}"
        )
