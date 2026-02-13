"""
File Storage Service - AssessIQ
================================
Handles file uploads, storage, and database linking.

Features:
- File upload with validation
- SHA-256 checksum generation
- Database record creation
- File retrieval and deletion
"""

import os
import uuid
import hashlib
import logging
import shutil
from datetime import datetime
from typing import Optional, Tuple, List
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from database.models import (
    UploadedFile, FileType, Student, Teacher, Evaluation, ModelAnswer,
    SessionLocal
)
from config.settings import settings

logger = logging.getLogger("AssessIQ.Storage")


class FileStorageService:
    """
    File Storage Service
    ---------------------
    Handles all file operations with database integration.
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary upload directories."""
        directories = [
            self.upload_dir,
            self.upload_dir / "student_answers",
            self.upload_dir / "model_answers",
            self.upload_dir / "evaluations",
            self.upload_dir / "manual_checks",
            self.upload_dir / "profiles",
            self.upload_dir / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()
    
    def _validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check filename
        if not file.filename:
            return False, "No filename provided"
        
        # Check extension
        extension = self._get_file_extension(file.filename)
        if extension not in self.allowed_extensions:
            return False, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
        
        return True, None
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".tiff": "image/tiff",
            ".bmp": "image/bmp",
            ".jfif": "image/jpeg",
        }
        return mime_types.get(extension, "application/octet-stream")
    
    def _get_subdirectory(self, file_type: FileType) -> str:
        """Get subdirectory based on file type."""
        subdirectories = {
            FileType.STUDENT_ANSWER: "student_answers",
            FileType.MODEL_ANSWER: "model_answers",
            FileType.EVALUATION_RESULT: "evaluations",
            FileType.MANUAL_CHECK: "manual_checks",
            FileType.OTHER: "temp"
        }
        return subdirectories.get(file_type, "temp")
    
    async def save_file(
        self,
        file: UploadFile,
        file_type: FileType = FileType.OTHER,
        student_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        evaluation_id: Optional[int] = None,
        model_answer_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Tuple[Optional[UploadedFile], Optional[str]]:
        """
        Save an uploaded file and create database record.
        
        Args:
            file: The uploaded file
            file_type: Type of file (for organizing storage)
            student_id: Associated student ID
            teacher_id: Associated teacher ID
            evaluation_id: Associated evaluation ID
            model_answer_id: Associated model answer ID
            db: Database session
        
        Returns:
            Tuple of (UploadedFile record, error_message)
        """
        # Validate file
        is_valid, error = self._validate_file(file)
        if not is_valid:
            return None, error
        
        # Generate unique filename
        extension = self._get_file_extension(file.filename)
        stored_filename = f"{uuid.uuid4()}{extension}"
        
        # Determine subdirectory
        subdirectory = self._get_subdirectory(file_type)
        file_dir = self.upload_dir / subdirectory
        file_path = file_dir / stored_filename
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                
                # Check file size
                if len(content) > self.max_file_size:
                    return None, f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
                
                buffer.write(content)
            
            # Calculate checksum
            checksum = self._calculate_checksum(str(file_path))
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create database session if not provided
            close_db = False
            if db is None:
                db = SessionLocal()
                close_db = True
            
            try:
                # Create database record
                file_record = UploadedFile(
                    original_filename=file.filename,
                    stored_filename=stored_filename,
                    file_path=str(file_path),
                    file_size=file_size,
                    mime_type=self._get_mime_type(extension),
                    file_type=file_type,
                    student_id=student_id,
                    teacher_id=teacher_id,
                    evaluation_id=evaluation_id,
                    model_answer_id=model_answer_id,
                    checksum=checksum
                )
                
                db.add(file_record)
                db.commit()
                db.refresh(file_record)
                
                logger.info(f"File saved: {file_record.file_id} - {file.filename}")
                
                return file_record, None
                
            except Exception as e:
                db.rollback()
                # Clean up file if database operation fails
                if file_path.exists():
                    os.remove(file_path)
                raise e
            finally:
                if close_db:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            # Clean up on error
            if file_path.exists():
                os.remove(file_path)
            return None, str(e)
    
    def get_file(
        self,
        file_id: str,
        db: Optional[Session] = None
    ) -> Tuple[Optional[UploadedFile], Optional[str]]:
        """
        Get file record by ID.
        
        Returns:
            Tuple of (UploadedFile record, file_path)
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            file_record = db.query(UploadedFile).filter(
                UploadedFile.file_id == file_id,
                UploadedFile.is_deleted == False
            ).first()
            
            if not file_record:
                return None, None
            
            return file_record, file_record.file_path
            
        finally:
            if close_db:
                db.close()
    
    def delete_file(
        self,
        file_id: str,
        permanent: bool = False,
        db: Optional[Session] = None
    ) -> bool:
        """
        Delete a file (soft delete by default).
        
        Args:
            file_id: File ID to delete
            permanent: If True, permanently delete file from disk
            db: Database session
        
        Returns:
            True if successful
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            file_record = db.query(UploadedFile).filter(
                UploadedFile.file_id == file_id
            ).first()
            
            if not file_record:
                return False
            
            if permanent:
                # Delete file from disk
                if os.path.exists(file_record.file_path):
                    os.remove(file_record.file_path)
                
                # Delete database record
                db.delete(file_record)
            else:
                # Soft delete
                file_record.is_deleted = True
                file_record.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"File deleted: {file_id} (permanent={permanent})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting file: {e}")
            return False
        finally:
            if close_db:
                db.close()
    
    def get_files_by_type(
        self,
        file_type: FileType,
        student_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        limit: int = 50,
        db: Optional[Session] = None
    ) -> List[UploadedFile]:
        """
        Get files by type with optional filtering.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            query = db.query(UploadedFile).filter(
                UploadedFile.file_type == file_type,
                UploadedFile.is_deleted == False
            )
            
            if student_id:
                query = query.filter(UploadedFile.student_id == student_id)
            
            if teacher_id:
                query = query.filter(UploadedFile.teacher_id == teacher_id)
            
            return query.order_by(UploadedFile.created_at.desc()).limit(limit).all()
            
        finally:
            if close_db:
                db.close()
    
    def update_extracted_text(
        self,
        file_id: str,
        extracted_text: str,
        db: Optional[Session] = None
    ) -> bool:
        """
        Update the extracted text (OCR result) for a file.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            file_record = db.query(UploadedFile).filter(
                UploadedFile.file_id == file_id
            ).first()
            
            if not file_record:
                return False
            
            file_record.extracted_text = extracted_text
            file_record.is_processed = True
            file_record.updated_at = datetime.utcnow()
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating extracted text: {e}")
            return False
        finally:
            if close_db:
                db.close()
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours.
        
        Returns:
            Number of files deleted
        """
        from datetime import timedelta
        
        db = SessionLocal()
        count = 0
        
        try:
            cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            # Find old temp files
            old_files = db.query(UploadedFile).filter(
                UploadedFile.file_type == FileType.OTHER,
                UploadedFile.created_at < cutoff
            ).all()
            
            for file_record in old_files:
                if self.delete_file(file_record.file_id, permanent=True, db=db):
                    count += 1
            
            logger.info(f"Cleaned up {count} temp files")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return count
        finally:
            db.close()
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        """
        db = SessionLocal()
        
        try:
            from sqlalchemy import func
            
            total_files = db.query(func.count(UploadedFile.id)).filter(
                UploadedFile.is_deleted == False
            ).scalar() or 0
            
            total_size = db.query(func.sum(UploadedFile.file_size)).filter(
                UploadedFile.is_deleted == False
            ).scalar() or 0
            
            # By type
            type_stats = {}
            for file_type in FileType:
                count = db.query(func.count(UploadedFile.id)).filter(
                    UploadedFile.file_type == file_type,
                    UploadedFile.is_deleted == False
                ).scalar() or 0
                type_stats[file_type.value] = count
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
                "by_type": type_stats
            }
            
        finally:
            db.close()


# Create singleton instance
file_storage_service = FileStorageService()
