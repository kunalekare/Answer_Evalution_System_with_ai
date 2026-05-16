"""
Upload Routes
==============
Handles file upload operations for student answers and model answer keys.
Supports PDF and image files with validation and preprocessing.
"""

import os
import uuid
import shutil
import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import aiofiles

from config.settings import settings

logger = logging.getLogger("AssessIQ.Upload")

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
    model_answer: UploadFile = File(..., description="Model answer key (image/PDF)"),
    student_answer: Optional[UploadFile] = File(None, description="Student answer sheet (image/PDF)"),
    student_text: Optional[str] = Form(None, description="Student answer as text (alternative to image)"),
    question_type: str = Form("descriptive", description="Type of question: factual, descriptive, diagram"),
    subject: Optional[str] = Form(None, description="Subject/Topic of the question"),
    max_marks: int = Form(10, description="Maximum marks for this question"),
    ocr_engine: str = Form("easyocr", description="OCR engine for text extraction (easyocr, ensemble, tesseract, paddleocr, sarvam)")
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
    
    **Parameters:**
    - ocr_engine: Which OCR engine to use for text extraction (default: easyocr)
    """
    
    logger.info(f"🔍 [UPLOAD] Received ocr_engine parameter: '{ocr_engine}'")
    
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
        
        # OPTIMIZATION: Extract text NOW (synchronously before returning)
        # This GUARANTEES cache exists before evaluation starts
        try:
            from api.services.ocr_service import OCRService
            from api.services.text_cleaning_service import TextCleaningService
            
            logger.info(f"[CACHE] Starting pre-cache extraction for {evaluation_id}...")
            
            # Initialize cache directory
            os.makedirs(os.path.join(eval_dir, ".cache"), exist_ok=True)
            
            # Get engine string
            ocr_engine_str = ocr_engine.value if hasattr(ocr_engine, 'value') else str(ocr_engine)
            
            try:
                ocr = OCRService(engine=ocr_engine_str)
            except ValueError:
                logger.warning(f"[CACHE] Engine {ocr_engine_str} not available, using easyocr")
                ocr = OCRService(engine='easyocr')
                ocr_engine_str = 'easyocr'
            
            # Extract model text
            if model_path and os.path.exists(model_path):
                logger.info(f"[CACHE] Extracting model answer...")
                try:
                    model_text = ocr.extract_text(model_path, language=None)
                    model_clean = TextCleaningService.clean_for_question_segmentation(model_text)
                    with open(os.path.join(eval_dir, ".cache", "model_extracted.txt"), 'w', encoding='utf-8') as f:
                        f.write(model_clean)
                    logger.info(f"[CACHE] Model cached: {len(model_text)} -> {len(model_clean)} chars")
                except Exception as e:
                    # Check if it's a network error and engine is Sarvam
                    error_str = str(e).lower()
                    if ('connecterror' in error_str or 'getaddrinfo' in error_str or 'connection' in error_str) and ocr_engine_str == 'sarvam':
                        logger.warning(f"[CACHE] Sarvam network error, falling back to easyocr for model")
                        fallback_ocr = OCRService(engine='easyocr')
                        model_text = fallback_ocr.extract_text(model_path, language=None)
                        model_clean = TextCleaningService.clean_for_question_segmentation(model_text)
                        with open(os.path.join(eval_dir, ".cache", "model_extracted.txt"), 'w', encoding='utf-8') as f:
                            f.write(model_clean)
                        logger.info(f"[CACHE] Model cached via fallback: {len(model_text)} -> {len(model_clean)} chars")
                    else:
                        raise
            
            # Extract student text
            if student_path and os.path.exists(student_path) and not student_path.endswith('.txt'):
                logger.info(f"[CACHE] Extracting student answer...")
                try:
                    student_text = ocr.extract_text(student_path, language=None)
                    student_clean = TextCleaningService.clean_for_question_segmentation(student_text)
                    with open(os.path.join(eval_dir, ".cache", "student_extracted.txt"), 'w', encoding='utf-8') as f:
                        f.write(student_clean)
                    logger.info(f"[CACHE] Student cached: {len(student_text)} -> {len(student_clean)} chars")
                except Exception as e:
                    # Check if it's a network error and engine is Sarvam
                    error_str = str(e).lower()
                    if ('connecterror' in error_str or 'getaddrinfo' in error_str or 'connection' in error_str) and ocr_engine_str == 'sarvam':
                        logger.warning(f"[CACHE] Sarvam network error, falling back to easyocr for student")
                        fallback_ocr = OCRService(engine='easyocr')
                        student_text = fallback_ocr.extract_text(student_path, language=None)
                        student_clean = TextCleaningService.clean_for_question_segmentation(student_text)
                        with open(os.path.join(eval_dir, ".cache", "student_extracted.txt"), 'w', encoding='utf-8') as f:
                            f.write(student_clean)
                        logger.info(f"[CACHE] Student cached via fallback: {len(student_text)} -> {len(student_clean)} chars")
                    else:
                        raise
            elif student_path and student_path.endswith('.txt'):
                logger.info(f"[CACHE] Using text input, saving to cache...")
                with open(student_path, 'r', encoding='utf-8') as f:
                    student_text = f.read()
                student_clean = TextCleaningService.clean_for_question_segmentation(student_text)
                with open(os.path.join(eval_dir, ".cache", "student_extracted.txt"), 'w', encoding='utf-8') as f:
                    f.write(student_clean)
                logger.info(f"[CACHE] Text cached: {len(student_text)} -> {len(student_clean)} chars")
            
            logger.info(f"[CACHE] Pre-caching complete")
            
        except Exception as e:
            logger.warning(f"[CACHE] Pre-caching failed (will extract during eval): {e}")
        
        return UploadResponse(
            success=True,
            message="Files uploaded successfully. Ready for evaluation.",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
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
async def extract_text_from_upload(evaluation_id: str, ocr_engine: str = "easyocr"):
    """
    Load cached extracted OCR text from uploaded files.
    
    Query parameters:
    - evaluation_id: The evaluation ID
    - ocr_engine: OCR engine to use (for reference, but uses cached text from upload)
    
    This allows users to preview cached text WITHOUT re-extracting.
    OPTIMIZATION: Always load from cache created during upload phase.
    """
    # ========== DEBUG: Log the received parameters ==========
    logger.info(f"🔍 [EXTRACT-TEXT] Loading cached text for eval_id: '{evaluation_id}' (engine: {ocr_engine})")
    
    eval_dir = os.path.join(settings.UPLOAD_DIR, "evaluations", evaluation_id)
    cache_dir = os.path.join(eval_dir, ".cache")
    
    if not os.path.exists(eval_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation {evaluation_id} not found"
        )
    
    try:
        # Find files
        files = os.listdir(eval_dir)
        student_file = next((f for f in files if f.startswith("student_") or f == "student_answer.txt"), None)
        
        result = {
            "evaluation_id": evaluation_id,
            "ocr_engine_requested": ocr_engine,
            "ocr_engine_used": ocr_engine,
            "model_answer": None,
            "student_answer": None,
            "note": "✅ LOADED FROM CACHE (no re-extraction)"
        }
        
        # Load model answer text from cache
        model_cache = os.path.join(cache_dir, "model_extracted.txt")
        if os.path.exists(model_cache):
            try:
                with open(model_cache, 'r', encoding='utf-8') as f:
                    model_text = f.read()
                logger.info(f"✅ [EXTRACT-TEXT] Model text loaded from CACHE: {len(model_text)} chars (NO RE-EXTRACTION)")
                result["model_answer"] = {
                    "text": model_text,
                    "char_count": len(model_text),
                    "word_count": len(model_text.split()),
                    "source": "cache"
                }
            except Exception as e:
                logger.error(f"❌ [EXTRACT-TEXT] Failed to load model cache: {e}")
                result["model_answer"] = {
                    "error": f"Could not load cached model text: {str(e)}"
                }
        else:
            logger.warning(f"⚠️ [EXTRACT-TEXT] Model cache not found at {model_cache}")
            result["model_answer"] = {
                "error": "Model text cache not found"
            }
        
        # Load student answer text from cache
        student_cache = os.path.join(cache_dir, "student_extracted.txt")
        if os.path.exists(student_cache):
            try:
                with open(student_cache, 'r', encoding='utf-8') as f:
                    student_text = f.read()
                
                # Check if it was from text input
                if student_file and student_file.endswith('.txt'):
                    result["ocr_engine_used"] = "text_input"
                    logger.info(f"✅ [EXTRACT-TEXT] Student text loaded from cache (TEXT INPUT): {len(student_text)} chars")
                else:
                    logger.info(f"✅ [EXTRACT-TEXT] Student text loaded from CACHE: {len(student_text)} chars (NO RE-EXTRACTION)")
                
                result["student_answer"] = {
                    "text": student_text,
                    "char_count": len(student_text),
                    "word_count": len(student_text.split()),
                    "source": "cache"
                }
            except Exception as e:
                logger.error(f"❌ [EXTRACT-TEXT] Failed to load student cache: {e}")
                result["student_answer"] = {
                    "error": f"Could not load cached student text: {str(e)}"
                }
        else:
            logger.warning(f"⚠️ [EXTRACT-TEXT] Student cache not found at {student_cache}")
            result["student_answer"] = {
                "error": "Student text cache not found"
            }
        
        logger.info(f"✅ [EXTRACT-TEXT] Retrieved cached text for evaluation {evaluation_id}")
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to load cached text: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load cached text: {str(e)}"
        )

