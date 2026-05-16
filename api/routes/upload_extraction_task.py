#!/usr/bin/env python3
"""
Background extraction task for upload.py
Extracts text after files are uploaded and caches it for later use
"""

# This function should be added to api/routes/upload.py

def _extract_and_cache_text(
    evaluation_id: str,
    eval_dir: str,
    model_path: str,
    student_path: str,
    student_file: str
) -> None:
    """
    Background task: Extract text from model and student answers immediately after upload.
    
    This function:
    1. Extracts text from uploaded files
    2. Caches extracted text locally
    3. Prevents redundant extraction during evaluation
    
    Args:
        evaluation_id: Unique evaluation ID
        eval_dir: Directory containing evaluation files
        model_path: Path to model answer file
        student_path: Path to student answer file
        student_file: Filename of student answer
    """
    import os
    from api.services.ocr_service import OCRService
    
    logger.info(f"[BACKGROUND] Starting post-upload text extraction for evaluation {evaluation_id}")
    
    try:
        # Create cache directory
        cache_dir = os.path.join(eval_dir, ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize OCR service with default engine
        ocr = OCRService(engine='easyocr')  # Use fast engine for background extraction
        
        # Extract model text
        try:
            logger.info(f"[BACKGROUND] Extracting model answer text...")
            model_text = ocr.extract_text(model_path, language=None)
            
            # Cache it
            model_cache = os.path.join(cache_dir, "model_extracted.txt")
            with open(model_cache, 'w', encoding='utf-8') as f:
                f.write(model_text)
            
            logger.info(f"[BACKGROUND] Model answer cached: {len(model_text)} chars")
        except Exception as e:
            logger.warning(f"[BACKGROUND] Model extraction failed: {e}")
        
        # Extract student text
        try:
            if student_file.endswith('.txt'):
                # Text input - no extraction needed
                logger.info(f"[BACKGROUND] Student answer is text input - no extraction needed")
            else:
                logger.info(f"[BACKGROUND] Extracting student answer text...")
                student_text = ocr.extract_text(student_path, language=None)
                
                # Cache it
                student_cache = os.path.join(cache_dir, "student_extracted.txt")
                with open(student_cache, 'w', encoding='utf-8') as f:
                    f.write(student_text)
                
                logger.info(f"[BACKGROUND] Student answer cached: {len(student_text)} chars")
        except Exception as e:
            logger.warning(f"[BACKGROUND] Student extraction failed: {e}")
        
        logger.info(f"[BACKGROUND] Post-upload extraction completed for {evaluation_id}")
        
    except Exception as e:
        logger.error(f"[BACKGROUND] Unexpected error during post-upload extraction: {e}")
        # Don't raise - this is background task, failure shouldn't affect user
