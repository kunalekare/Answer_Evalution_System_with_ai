"""
Text Cleaning & Normalization Service
=======================================
Advanced OCR text post-processing to remove artifacts, fix common errors,
and normalize text for better question-wise evaluation.

Features:
  • Remove OCR artifacts and noise
  • Fix common OCR misrecognitions
  • Normalize whitespace and punctuation
  • Preserve question structure
  • Clean repeated characters and lines
  • Fix spacing issues around punctuation
"""

import re
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger("AssessIQ.TextCleaning")


class TextCleaningService:
    """Service for cleaning and normalizing extracted OCR text."""
    
    # Common OCR misrecognitions
    COMMON_REPLACEMENTS = {
        'rn': 'm',      # 'rn' often confused with 'm'
        '0': 'O',       # Zero vs letter O in context
        '|': 'I',       # Pipe vs letter I
        '1': 'l',       # 1 vs lowercase l
        '8': 'B',       # 8 vs B in context (context-dependent)
        'fi': 'fi',     # fi ligature
        'fl': 'fl',     # fl ligature
    }
    
    # OCR noise patterns
    NOISE_PATTERNS = [
        r'~+',           # Multiple tildes
        r'`+',           # Multiple backticks
        r'\*{2,}',       # Multiple asterisks
        r'_{3,}',        # Three or more underscores
        r'\-{3,}',       # Three or more hyphens
        r'\.{4,}',       # Four or more dots (ellipsis)
        r'\s{2,}',       # Multiple spaces (except newlines)
    ]
    
    # Common OCR errors
    OCR_ERRORS = {
        r'\bl\b': 'I',        # Standalone 'l' → 'I'
        r'\bO\b': 'O',        # Standalone 'O' (context)
        r'[|1]nclude': 'Include',
        r'[|1]nformation': 'Information',
        r'[|1]ntroduction': 'Introduction',
        r'([^a-z])[o0]([^a-z])': r'\1o\2',  # o vs 0
        r'vvord': 'word',
        r'vvor': 'wor',
        r'tlie': 'the',
        r'tliat': 'that',
        r'wliich': 'which',
        r'liave': 'have',
        r'liis': 'his',
        r'sliould': 'should',
        r'conimon': 'common',
        r'scliool': 'school',
        r'teaelier': 'teacher',
    }
    
    @staticmethod
    def clean_text(text: str, aggressive: bool = False) -> str:
        """
        Clean extracted OCR text comprehensively.
        
        Args:
            text: Raw OCR extracted text
            aggressive: If True, apply more aggressive cleaning
        
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        original_len = len(text)
        
        # 1. Remove null bytes and invalid characters
        text = text.replace('\x00', '')
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t\r')
        
        # 2. Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 3. Fix common OCR misrecognitions (word-level)
        text = TextCleaningService._fix_ocr_errors(text)
        
        # 4. Remove excessive whitespace (preserve paragraph structure)
        text = TextCleaningService._normalize_whitespace(text)
        
        # 5. Fix spacing around punctuation
        text = TextCleaningService._fix_punctuation_spacing(text)
        
        # 6. Clean noise artifacts
        text = TextCleaningService._remove_noise(text)
        
        # 7. Remove repeated characters
        if aggressive:
            text = TextCleaningService._remove_repetitive_chars(text)
        
        # 8. Fix broken words at line boundaries
        text = TextCleaningService._fix_broken_words(text)
        
        # 9. Standardize question markers
        text = TextCleaningService._standardize_question_markers(text)
        
        # 10. Final cleanup
        text = text.strip()
        
        logger.info(f"Text cleaning: {original_len} chars -> {len(text)} chars")
        return text
    
    @staticmethod
    def _fix_ocr_errors(text: str) -> str:
        """Fix common OCR misrecognitions."""
        for pattern, replacement in TextCleaningService.OCR_ERRORS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize excessive whitespace while preserving structure."""
        # Replace tabs with spaces
        text = text.replace('\t', '    ')
        
        # Reduce multiple spaces to single space (but preserve new lines)
        lines = text.split('\n')
        lines = [re.sub(r' {2,}', ' ', line.strip()) for line in lines]
        
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in lines]
        
        # Remove empty lines but preserve blank lines for structure (max 2 consecutive)
        cleaned_lines = []
        empty_count = 0
        for line in lines:
            if not line.strip():
                empty_count += 1
                if empty_count <= 2:
                    cleaned_lines.append('')
            else:
                empty_count = 0
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def _fix_punctuation_spacing(text: str) -> str:
        """Fix spacing issues around punctuation."""
        # Add space before punctuation at line start (fixing OCR errors)
        text = re.sub(r'^\s*([.,!?;:])', r'\1', text, flags=re.MULTILINE)
        
        # Fix multiple punctuation marks
        text = re.sub(r'([.,!?]){2,}', r'\1', text)
        
        # Fix spacing around common punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # No space before
        text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)  # Single space after
        
        # Fix spacing around parentheses
        text = re.sub(r'\s+\(', ' (', text)
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        text = re.sub(r'\)\s+', ') ', text)
        
        # Fix colon spacing (especially in "Q1 :" → "Q1:")
        text = re.sub(r':\s+', ': ', text)
        
        return text
    
    @staticmethod
    def _remove_noise(text: str) -> str:
        """Remove OCR noise patterns."""
        for pattern in TextCleaningService.NOISE_PATTERNS:
            if pattern == r'\s{2,}':
                # Keep moderate spacing
                text = re.sub(pattern, ' ', text)
            elif pattern == r'\.{4,}':
                # Replace 4+ dots with 3-dot ellipsis
                text = re.sub(pattern, '...', text)
            else:
                # Remove noise
                text = re.sub(pattern, '', text)
        
        return text
    
    @staticmethod
    def _remove_repetitive_chars(text: str) -> str:
        """Remove excessively repeated characters (OCR artifact)."""
        # Remove more than 3 repeated characters
        text = re.sub(r'([a-z])\1{3,}', r'\1\1', text, flags=re.IGNORECASE)
        return text
    
    @staticmethod
    def _fix_broken_words(text: str) -> str:
        """Fix words broken across lines."""
        lines = text.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                # Check if current line ends with partial word (no space, no punctuation)
                if line and not line[-1] in ' .!?;:,-()':
                    next_line = lines[i + 1].lstrip()
                    # Try to join if next line starts with lowercase
                    if next_line and next_line[0].islower():
                        line = line + next_line
                        lines[i + 1] = ''  # Mark as consumed
            
            if line:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    @staticmethod
    def _standardize_question_markers(text: str) -> str:
        """Standardize question numbering patterns."""
        # Normalize question patterns
        # "Q 1." → "Q1."
        text = re.sub(r'\bQ\s+(\d+)', r'Q\1', text, flags=re.IGNORECASE)
        
        # "Question 1 :" → "Question 1:"
        text = re.sub(r'([Qq]uestion\s+\d+)\s+:', r'\1:', text)
        
        # Fix "1 . " → "1."
        text = re.sub(r'(\d+)\s+\.\s+', r'\1. ', text)
        
        # Ensure space after question marker
        text = re.sub(r'(?<=[Q\d])\.\s*(?=[A-Z])', '. ', text)
        
        return text
    
    @staticmethod
    def clean_for_question_segmentation(text: str) -> str:
        """
        Clean text specifically for question segmentation.
        Preserves question structure while removing noise.
        """
        if not text or not isinstance(text, str):
            return ""
        
        # First do standard cleaning
        text = TextCleaningService.clean_text(text, aggressive=False)
        
        # Additional cleaning for segmentation
        # Remove page numbers and headers
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip common non-content lines
            if TextCleaningService._is_noise_line(stripped):
                continue
            
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        logger.info(f"Question segmentation text cleaned: {len(result)} chars")
        return result
    
    @staticmethod
    def _is_noise_line(line: str) -> bool:
        """Check if a line is likely noise/header/footer."""
        if not line:
            return True
        
        # Page numbers (just numbers)
        if line.isdigit() and len(line) <= 3:
            return True
        
        # Extra spaces/dashes (likely underline)
        if re.match(r'^[-_\s]{3,}$', line):
            return True
        
        # Repeated characters
        if len(set(line)) <= 2:  # Only 1-2 unique chars
            return True
        
        # URLs and email addresses
        if re.match(r'https?://|@', line):
            return True
        
        return False
    
    @staticmethod
    def extract_clean_questions(text: str) -> List[str]:
        """
        Extract and return cleaned question segments from text.
        Used for preview and segmentation.
        """
        clean_text = TextCleaningService.clean_for_question_segmentation(text)
        
        # Split by common question markers
        questions = re.split(
            r'(?=^(?:Q|Question|Ques|Ans)\.?\s*\d+|^\d+[\.\):\-])',
            clean_text,
            flags=re.MULTILINE
        )
        
        return [q.strip() for q in questions if q.strip()]
    
    @staticmethod
    def get_quality_score(text: str) -> float:
        """
        Score text quality (0-1) based on cleaning effectiveness.
        Used to detect if text was extracted properly.
        """
        if not text:
            return 0.0
        
        score = 1.0
        
        # Check for excessive noise characters
        noise_chars = len(re.findall(r'[^\w\s\.\,\!\?\;\:\-\(\)]', text))
        if noise_chars > len(text) * 0.1:
            score -= 0.2
        
        # Check for repetitive characters (OCR artifact)
        repetitive = len(re.findall(r'([a-z])\1{3,}', text, flags=re.IGNORECASE))
        if repetitive > 5:
            score -= 0.15
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]', text)
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        if avg_sentence_len < 3 or avg_sentence_len > 50:
            score -= 0.1
        
        # Check for proper line structure (should have newlines for questions)
        lines = text.split('\n')
        if len(lines) < 2:
            score -= 0.05
        
        return max(0.0, min(1.0, score))


# Convenience function
def clean_extracted_text(text: str, aggressive: bool = False) -> str:
    """
    Quick function to clean extracted OCR text.
    
    Usage:
        cleaned = clean_extracted_text(ocr_text)
    """
    return TextCleaningService.clean_text(text, aggressive=aggressive)
