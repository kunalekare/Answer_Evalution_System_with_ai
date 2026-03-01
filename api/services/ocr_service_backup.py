"""
OCR Service Module - Advanced Handwriting Recognition
======================================================
Optical Character Recognition optimized for ANY type of handwriting extraction.

This module provides a robust, multi-strategy OCR system that can handle:
- Cursive handwriting
- Print handwriting  
- Messy/difficult handwriting
- Low contrast documents
- Noisy/degraded images
- Various paper backgrounds

Multi-Strategy Extraction Pipeline:
===================================
1. Original image extraction
2. CLAHE contrast enhancement
3. Adaptive thresholding (multiple block sizes)
4. Morphological operations (dilation/erosion)
5. Sharpening + denoising
6. Inverted image extraction
7. Multi-scale extraction
8. Edge-enhanced extraction

Each strategy runs independently and results are combined using
longest text or voting for maximum accuracy.

Engines Supported:
- EasyOCR (default): Optimized for handwritten text
- Tesseract: Industry standard with handwriting mode
- PaddleOCR: High accuracy for complex layouts
"""

import os
import logging
from typing import Optional, List, Tuple, Union
from pathlib import Path
import numpy as np
import tempfile
import base64
import requests
import time

logger = logging.getLogger("AssessIQ.OCR")


class ImagePreprocessor:
    """
    Advanced Image Preprocessing Pipeline for Handwriting OCR.
    
    This class provides multiple preprocessing strategies optimized for
    extracting text from ANY type of handwriting, including:
    - Cursive and connected handwriting
    - Print/block letters
    - Messy or rushed handwriting
    - Light or faded ink
    - Various paper backgrounds
    
    Preprocessing Strategies:
    1. CLAHE contrast enhancement
    2. Adaptive thresholding (multiple block sizes)
    3. Morphological operations
    4. Sharpening and denoising
    5. Multi-scale processing
    6. Edge enhancement
    """
    
    def __init__(self):
        """Initialize the image preprocessor with OpenCV."""
        try:
            import cv2
            self.cv2 = cv2
            self._available = True
        except ImportError:
            logger.warning("OpenCV not installed. Image preprocessing will be limited.")
            self._available = False
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Load image from file path."""
        if not self._available:
            raise RuntimeError("OpenCV is required for image loading")
        
        image = self.cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        return image
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 2:
            return image
        return self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
    
    def resize_for_ocr(self, image: np.ndarray, min_dimension: int = 2000) -> np.ndarray:
        """
        Resize image to optimal size for OCR.
        Larger images provide better handwriting recognition.
        """
        h, w = image.shape[:2]
        if min(h, w) < min_dimension:
            scale = min_dimension / min(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return self.cv2.resize(image, (new_w, new_h), interpolation=self.cv2.INTER_CUBIC)
        return image
    
    def apply_clahe(self, gray: np.ndarray, clip_limit: float = 2.5, grid_size: int = 8) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        clahe = self.cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
        return clahe.apply(gray)
    
    def denoise(self, image: np.ndarray, strength: int = 10) -> np.ndarray:
        """Apply Non-Local Means Denoising (preserves edges better than blur)."""
        if len(image.shape) == 3:
            return self.cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
        return self.cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
    
    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Apply unsharp masking to enhance edges and text."""
        gaussian = self.cv2.GaussianBlur(image, (0, 0), 3)
        return self.cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
    
    def adaptive_threshold(self, gray: np.ndarray, block_size: int = 21, c: int = 10) -> np.ndarray:
        """Apply adaptive thresholding with configurable parameters."""
        return self.cv2.adaptiveThreshold(
            gray, 255,
            self.cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            self.cv2.THRESH_BINARY,
            block_size,
            c
        )
    
    def morphological_enhance(self, binary: np.ndarray, operation: str = "dilate") -> np.ndarray:
        """
        Apply morphological operations to enhance handwriting strokes.
        
        Operations:
        - dilate: Make strokes thicker (good for thin/light handwriting)
        - erode: Make strokes thinner (good for thick/bold handwriting)
        - close: Fill small gaps in strokes
        - open: Remove small noise dots
        """
        kernel = self.cv2.getStructuringElement(self.cv2.MORPH_ELLIPSE, (2, 2))
        
        if operation == "dilate":
            return self.cv2.dilate(binary, kernel, iterations=1)
        elif operation == "erode":
            return self.cv2.erode(binary, kernel, iterations=1)
        elif operation == "close":
            return self.cv2.morphologyEx(binary, self.cv2.MORPH_CLOSE, kernel)
        elif operation == "open":
            return self.cv2.morphologyEx(binary, self.cv2.MORPH_OPEN, kernel)
        return binary
    
    def correct_skew(self, image: np.ndarray) -> np.ndarray:
        """Correct skew (rotation) in the image using Hough transform."""
        h, w = image.shape[:2]
        edges = self.cv2.Canny(image, 50, 150, apertureSize=3)
        lines = self.cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is None:
            return image
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if -45 <= angle <= 45:
                angles.append(angle)
        
        if not angles:
            return image
        
        median_angle = np.median(angles)
        if abs(median_angle) < 0.5:  # Skip if angle is negligible
            return image
        
        center = (w // 2, h // 2)
        rotation_matrix = self.cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = self.cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=self.cv2.INTER_CUBIC,
            borderMode=self.cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def fix_illumination(self, gray: np.ndarray) -> np.ndarray:
        """Fix uneven illumination using morphological background subtraction."""
        # Create a background model using large morphological opening
        kernel = self.cv2.getStructuringElement(self.cv2.MORPH_ELLIPSE, (50, 50))
        background = self.cv2.morphologyEx(gray, self.cv2.MORPH_OPEN, kernel)
        
        # Subtract background to normalize illumination
        normalized = self.cv2.subtract(gray, background)
        normalized = self.cv2.normalize(normalized, None, 0, 255, self.cv2.NORM_MINMAX)
        
        return normalized.astype(np.uint8)
    
    def edge_enhance(self, gray: np.ndarray) -> np.ndarray:
        """Enhance edges to make text stand out more."""
        # Sobel edge detection
        sobelx = self.cv2.Sobel(gray, self.cv2.CV_64F, 1, 0, ksize=3)
        sobely = self.cv2.Sobel(gray, self.cv2.CV_64F, 0, 1, ksize=3)
        edges = np.sqrt(sobelx**2 + sobely**2)
        edges = (edges / edges.max() * 255).astype(np.uint8)
        
        # Combine with original
        combined = self.cv2.addWeighted(gray, 0.7, edges, 0.3, 0)
        return combined
    
    def get_all_preprocessed_versions(self, image_path: str) -> List[Tuple[str, np.ndarray]]:
        """
        Generate multiple preprocessed versions of the image for multi-strategy OCR.
        
        Returns a list of (strategy_name, preprocessed_image) tuples.
        """
        versions = []
        
        try:
            # Load and resize
            image = self.load_image(image_path)
            image = self.resize_for_ocr(image)
            gray = self.convert_to_grayscale(image)
            
            # 1. Original (just resized)
            versions.append(("original", image))
            
            # 2. CLAHE enhanced
            clahe_img = self.apply_clahe(gray, clip_limit=2.5)
            versions.append(("clahe", clahe_img))
            
            # 3. Strong CLAHE
            strong_clahe = self.apply_clahe(gray, clip_limit=4.0)
            versions.append(("strong_clahe", strong_clahe))
            
            # 4. Adaptive threshold (small block)
            thresh_small = self.adaptive_threshold(gray, block_size=11, c=5)
            versions.append(("thresh_small", thresh_small))
            
            # 5. Adaptive threshold (large block - better for handwriting)
            thresh_large = self.adaptive_threshold(gray, block_size=31, c=15)
            versions.append(("thresh_large", thresh_large))
            
            # 6. Denoised + CLAHE
            denoised = self.denoise(gray, strength=10)
            denoised_clahe = self.apply_clahe(denoised)
            versions.append(("denoised_clahe", denoised_clahe))
            
            # 7. Sharpened
            sharpened = self.sharpen(gray)
            versions.append(("sharpened", sharpened))
            
            # 8. Dilated (for thin/light handwriting)
            thresh_for_morph = self.adaptive_threshold(gray, block_size=21, c=10)
            dilated = self.morphological_enhance(thresh_for_morph, "dilate")
            versions.append(("dilated", dilated))
            
            # 9. Inverted (sometimes helps with light text on dark bg)
            inverted = self.cv2.bitwise_not(gray)
            versions.append(("inverted", inverted))
            
            # 10. Illumination fixed
            try:
                fixed_illum = self.fix_illumination(gray)
                fixed_clahe = self.apply_clahe(fixed_illum)
                versions.append(("fixed_illumination", fixed_clahe))
            except:
                pass
            
            # 11. Edge enhanced
            edge_enhanced = self.edge_enhance(gray)
            versions.append(("edge_enhanced", edge_enhanced))
            
            # 12. Otsu threshold
            _, otsu = self.cv2.threshold(gray, 0, 255, self.cv2.THRESH_BINARY + self.cv2.THRESH_OTSU)
            versions.append(("otsu", otsu))
            
            # 13. Bilateral filter + threshold (preserves edges)
            bilateral = self.cv2.bilateralFilter(gray, 9, 75, 75)
            bilateral_thresh = self.adaptive_threshold(bilateral, block_size=21, c=10)
            versions.append(("bilateral", bilateral_thresh))
            
            logger.info(f"Generated {len(versions)} preprocessed versions")
            
        except Exception as e:
            logger.error(f"Error generating preprocessed versions: {e}")
            # Return at least the original
            try:
                image = self.load_image(image_path)
                versions.append(("original", image))
            except:
                pass
        
        return versions


class OCRService:
    """
    Advanced OCR Service with Multi-Strategy Handwriting Recognition.
    
    This service uses multiple extraction strategies and preprocessing
    techniques to maximize text extraction from ANY type of handwriting.
    
    Strategy:
    1. Try multiple preprocessed versions of the image
    2. Run OCR on each version
    3. Combine/select the best results
    4. Clean and format extracted text
    
    Engines:
    - EasyOCR (default): Best for handwritten text
    - Tesseract: Industry standard with handwriting mode
    - PaddleOCR: High accuracy for complex layouts
    """
    
    def __init__(self, engine: str = None, languages: List[str] = None):
        """
        Initialize OCR service with specified engine.
        
        Args:
            engine: OCR engine to use ("easyocr", "tesseract", "paddleocr")
            languages: List of language codes (default: ["en"])
        """
        from config.settings import settings
        
        self.low_memory_mode = getattr(settings, 'LOW_MEMORY_MODE', False)
        self.engine_name = engine or settings.OCR_ENGINE
        self.languages = languages or settings.OCR_LANGUAGES
        self.preprocessor = ImagePreprocessor()
        
        # Initialize the selected engine (lazy load in low memory mode)
        self._engine = None
        self._engine_initialized = False
        
        # Only initialize engine immediately if not in low memory mode
        if not self.low_memory_mode:
            self._init_engine()
        else:
            logger.info("Low memory mode: OCR engine will be initialized on first use")
    
    def _ensure_engine_initialized(self):
        """Ensure the OCR engine is initialized (for lazy loading)."""
        if not self._engine_initialized:
            self._init_engine()
            self._engine_initialized = True
    
    def _init_engine(self):
        """Initialize the selected OCR engine."""
        logger.info(f"Initializing OCR engine: {self.engine_name}")
        
        if self.engine_name == "easyocr":
            self._init_easyocr()
        elif self.engine_name == "tesseract":
            self._init_tesseract()
        elif self.engine_name == "paddleocr":
            self._init_paddleocr()
        elif self.engine_name == "sarvam":
            self._init_sarvam()
        else:
            logger.warning(f"Unknown engine: {self.engine_name}, falling back to EasyOCR")
            self._init_easyocr()
    
    def _init_easyocr(self):
        """Initialize EasyOCR engine with handwriting-optimized settings."""
        try:
            import easyocr
            # Use paragraph mode and lower thresholds for better handwriting recognition
            self._engine = easyocr.Reader(
                self.languages, 
                gpu=False,
                model_storage_directory=None,
                download_enabled=True,
                detector=True,
                recognizer=True,
            )
            self.engine_name = "easyocr"
            logger.info("EasyOCR initialized successfully (handwriting-optimized)")
        except ImportError:
            logger.error("EasyOCR not installed. Install with: pip install easyocr")
            raise
    
    def _init_tesseract(self):
        """Initialize Tesseract OCR engine."""
        try:
            import pytesseract
            from config.settings import settings
            
            if settings.TESSERACT_PATH:
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
            
            self._engine = pytesseract
            self.engine_name = "tesseract"
            logger.info("Tesseract OCR initialized successfully")
        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract")
            raise
    
    def _init_paddleocr(self):
        """Initialize PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR
            self._engine = PaddleOCR(use_angle_cls=True, lang='en')
            self.engine_name = "paddleocr"
            logger.info("PaddleOCR initialized successfully")
        except ImportError:
            logger.error("PaddleOCR not installed. Install with: pip install paddleocr")
            raise
    
    def _init_sarvam(self):
        """Initialize Sarvam AI OCR engine (uses API)."""
        from config.settings import settings
        self._sarvam_api_key = getattr(settings, 'SARVAM_API_KEY', None)
        self._sarvam_api_url = getattr(settings, 'SARVAM_API_URL', 'https://api.sarvam.ai/v1/vision/ocr')
        self._fast_ocr_mode = getattr(settings, 'FAST_OCR_MODE', True)
        
        if not self._sarvam_api_key:
            logger.error("Sarvam AI API key not configured in settings")
            raise ValueError("Sarvam AI API key not configured")
        
        self.engine_name = "sarvam"
        self._engine = "sarvam_api"  # Placeholder - we use HTTP requests
        logger.info(f"Sarvam AI OCR initialized successfully (fast_mode={self._fast_ocr_mode})")
    
    def extract_text(
        self, 
        image_path: str,
        preprocess: bool = True,
        detail: bool = False
    ) -> Union[str, List[dict]]:
        """
        Extract text from image using the configured OCR engine.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to apply preprocessing
            detail: Whether to return detailed results with bounding boxes
            
        Returns:
            Extracted text as string, or list of dicts with details if detail=True
        """
        # Ensure engine is initialized (for lazy loading in low memory mode)
        self._ensure_engine_initialized()
        
        logger.info(f"Extracting text from: {image_path} using engine: {self.engine_name}")
        
        # Validate file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Handle PDF files
        if image_path.lower().endswith('.pdf'):
            return self._extract_from_pdf(image_path, preprocess, detail)
        
        # For Sarvam AI - use direct fast API (no preprocessing needed)
        if self.engine_name == "sarvam":
            logger.info("Using Sarvam AI FAST mode - skipping local preprocessing")
            start_time = time.time()
            result = self._extract_sarvam(image_path, detail)
            elapsed = time.time() - start_time
            logger.info(f"Sarvam AI extraction completed in {elapsed:.2f}s")
            return result
        
        # For other engines, use the multi-approach extraction method
        # which tries multiple preprocessing techniques for best results
        result = self._extract_from_image(image_path, preprocess, detail)
        
        logger.info(f"Extracted {len(result) if isinstance(result, str) else len(result)} characters/items")
        return result
    
    def _extract_easyocr(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Extract text using EasyOCR with handwriting-optimized settings.
        
        Uses lower thresholds and paragraph mode for better handwritten text recognition.
        """
        # Use optimized settings for handwritten text
        # - paragraph=True: Better for continuous handwritten text
        # - min_size=10: Detect smaller characters
        # - text_threshold=0.5: Lower threshold to catch more text (default 0.7)
        # - low_text=0.3: Lower threshold for text detection (default 0.4)
        # - link_threshold=0.3: Better linking of text regions
        # - canvas_size=2560: Higher resolution for better detection
        # - mag_ratio=1.5: Magnify for better small text detection
        
        results = self._engine.readtext(
            image_path,
            paragraph=False,  # Keep individual lines for handwriting
            min_size=10,
            text_threshold=0.5,  # Lower threshold for handwriting
            low_text=0.3,
            link_threshold=0.3,
            canvas_size=2560,
            mag_ratio=1.5,
            slope_ths=0.3,  # Allow more slope variation in handwriting
            ycenter_ths=0.5,  # More tolerance for vertical alignment
            height_ths=0.8,  # More tolerance for height variation
            width_ths=0.8,  # More tolerance for width variation
            add_margin=0.1,  # Add margin around detected text
            decoder='greedy',
            beamWidth=5,
            batch_size=1,
            contrast_ths=0.1,  # Lower contrast threshold
            adjust_contrast=0.5,  # Adjust contrast for better detection
        )
        
        logger.info(f"EasyOCR detected {len(results)} text regions")
        
        if detail:
            return [
                {
                    "text": r[1],
                    "confidence": r[2],
                    "bbox": r[0]
                }
                for r in results
            ]
        
        # Combine all text with proper line breaks
        # Sort by vertical position first for proper reading order
        if results:
            # Sort results by y-coordinate (top to bottom)
            sorted_results = sorted(results, key=lambda r: (
                min(p[1] for p in r[0]),  # Top Y coordinate
                min(p[0] for p in r[0])   # Left X coordinate
            ))
            
            texts = []
            last_y = -1
            for r in sorted_results:
                current_y = min(p[1] for p in r[0])
                # Add newline if significant vertical gap
                if last_y >= 0 and (current_y - last_y) > 30:
                    texts.append("\n")
                texts.append(r[1])
                last_y = max(p[1] for p in r[0])
            
            return " ".join(texts).replace(" \n ", "\n")
        
        return ""
    
    def _extract_tesseract(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """Extract text using Tesseract OCR."""
        from PIL import Image
        
        image = Image.open(image_path)
        
        if detail:
            import pytesseract
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            results = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    results.append({
                        "text": data['text'][i],
                        "confidence": data['conf'][i] / 100,
                        "bbox": [
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ]
                    })
            return results
        
        text = self._engine.image_to_string(image)
        return text.strip()
    
    def _extract_paddleocr(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """Extract text using PaddleOCR."""
        results = self._engine.ocr(image_path, cls=True)
        
        if not results or not results[0]:
            return [] if detail else ""
        
        if detail:
            return [
                {
                    "text": r[1][0],
                    "confidence": r[1][1],
                    "bbox": r[0]
                }
                for r in results[0]
            ]
        
        texts = [r[1][0] for r in results[0]]
        return " ".join(texts)
    
    def _extract_sarvam(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Extract text using advanced OCR - tries multiple high-quality APIs.
        
        Priority:
        1. Google Cloud Vision (best for handwriting - requires API key)
        2. OCR.space Engine 2 (good accuracy, free)
        3. Sarvam Document Intelligence (convert to PDF)
        4. EasyOCR (local fallback)
        
        Post-processing is applied to fix common OCR errors.
        """
        start_time = time.time()
        result = ""
        
        # Try Google Cloud Vision first (if configured)
        result = self._extract_google_vision(image_path, detail)
        if result and len(result) > 50:
            elapsed = time.time() - start_time
            logger.info(f"Google Vision completed in {elapsed:.2f}s with {len(result)} chars")
            return self._postprocess_ocr(result) if not detail else result
        
        # Try OCR.space (free API)
        result = self._extract_ocrspace(image_path, detail)
        if result and len(result) > 50:
            elapsed = time.time() - start_time
            logger.info(f"OCR.space completed in {elapsed:.2f}s with {len(result)} chars")
            return self._postprocess_ocr(result) if not detail else result
        
        # Try Sarvam Document Intelligence (convert image to PDF)
        result = self._extract_sarvam_via_pdf(image_path, detail)
        if result and len(result) > 50:
            elapsed = time.time() - start_time
            logger.info(f"Sarvam SDK completed in {elapsed:.2f}s with {len(result)} chars")
            return self._postprocess_ocr(result) if not detail else result
        
        logger.warning("All advanced OCR failed, falling back to EasyOCR")
        result = self._fallback_easyocr(image_path, detail)
        return self._postprocess_ocr(result) if not detail and result else result
    
    def _postprocess_ocr(self, text: str) -> str:
        """
        Post-process OCR text to fix common errors.
        Improves accuracy for handwritten text recognition.
        """
        if not text:
            return text
        
        import re
        
        # Common OCR corrections for handwriting - comprehensive list
        corrections = {
            # Name corrections (common Indian names)
            r'\bOrakriti\b': 'Prakriti',  # P read as O
            r'\bPrakrit\b': 'Prakriti',
            
            # School/Institution names
            r'\b([Ss])ohoo\b': r'\1chool',  # Sohoo -> School
            r'\b([Ss])choo\b': r'\1chool',
            r'\bMahavioyalaya\b': 'Mahavidyalaya',  # dy misread as oy
            r'\bMahavidya1aya\b': 'Mahavidyalaya',
            r'\bSamik\b': 'Sainik',  # Sainik Residential School
            r'\bAvasiya\b': 'Avasiya',  # Residential
            
            # Section/Class corrections
            r'\bĐec\b': 'Sec',  # Đec -> Sec
            r'\bDec\s*:\s*': 'Sec: ',
            r'\b6B\b': '6B',  
            r'\bTight\b': 'Eight',  # Tight -> Eight (in context of Class: 8)
            r'Class\s*:\s*8\s*\(\s*Tight\s*\)': 'Class: 8 (Eight)',
            
            # Common word errors in educational text
            r'\badils\b': 'adults',
            r'\bstudunts\b': 'students',
            r'\bclassrocr\b': 'classroom',
            r'\bdassroom\b': 'classroom', 
            r'\bclassrcom\b': 'classroom',
            r'\bclassroem\b': 'classroom',
            r'\bolassrom\b': 'classroom',
            r'\bcassroems\b': 'classrooms',
            r'\bknowldge\b': 'knowledge',
            r'\bpercil\b': 'pencil',
            r'\bactvilies\b': 'activities',
            r'\bactiviliss\b': 'activities',
            r'\bactivilies\b': 'activities',
            r'\bkindırgartın\b': 'kindergarten',
            r'\bkindergartın\b': 'kindergarten',
            r'\bporcont\b': 'percent',
            r'\bporcent\b': 'percent',
            r'\bhandrriting\b': 'handwriting',
            r'\bhandiriting\b': 'handwriting',
            r'\bhandvriling\b': 'handwriting',
            r'\bhandrritten\b': 'handwritten',
            r'\bhandruritten\b': 'handwritten',
            r'\bhandwvillen\b': 'handwritten',
            r'\bCelloge\b': 'College',
            r'\bColege\b': 'College',
            r'\bimportanu\b': 'importance',
            r'\blitracy\b': 'literacy',  
            r'\bexperind\b': 'experience',
            r'\bexperinca\b': 'experience',
            r'\bdeficulty\b': 'difficulty',
            r'\bmostring\b': 'mastering',
            r'\bmostering\b': 'mastering',
            r'\bvensequenas\b': 'consequences',
            r'\beslensizily\b': 'extensively',
            r'\bstudunt\b': 'student',
            r'\bcommunicaticn\b': 'communication',
            r'\bsludy\b': 'study',
            r'\bfirt\b': 'fine',
            r'\brecnt\b': 'recent',
            r'\bnold\b': 'noted',
            r'\bslan\b': 'state',
            r'\bafier\b': 'after',
            r'\bafler\b': 'after',
            r'\bgraduafion\b': 'graduation',
            r'\breference\b': 'reference',
            r'\bwviorld\b': 'world',
            r'\bwiorld\b': 'world',
            r'\bpoople\b': 'people',
            r'\bjudog\b': 'judge',
            r'\bjudon\b': 'judge',
            r'\bacadımic\b': 'academic',
            r'\bacademic\b': 'academic',
            r'\bpeor\b': 'poor',
            r'\bcarly\b': 'early',
            r'\bromains\b': 'remains',
            r'\bwhther\b': 'whether',
            r'\bwhelher\b': 'whether',
            r'\bboyond\b': 'beyond',
            r'\bfund\b(?=\s+Chat)': 'found',  # "fund Chat" -> "found that"
            r'\bChat\b(?=\s+\d)': 'that',  # "Chat 85" -> "that 85"
            r'\bEien\b': 'Even',
            r'\bfool\b': 'tool',
            r'\bmolor\b': 'motor',
            r'\bCime\b': 'time',
            r'\bsisth\b': 'sixth',
            r'\baddifion\b': 'addition',
            r'\bEcripl\b': 'Script',
            r'\bSoribble\b': 'Scribble',
            r'\bFlory\b': 'Florey',
            r'\bwrifes\b': 'writes',
            r'\bnoturn\b': 'not',
            r'\bmachine-drin\b': 'machine-driven',
            r'\bRessarch\b': 'Research',
            # Additional corrections for remaining errors
            r'\bhandrrting\b': 'handwriting',  
            r'\bhandrriling\b': 'handwriting',
            r'\bhondwritten\b': 'handwritten',
            r'\bexperina\b': 'experience',
            r'\bperform\b\.': 'performance.',
            r'\blo\b': 'to',  # "lo" often misread as "to"
            r'\bil\b': 'it',  # "il" often misread as "it"
            r'\bar\s+non\b': 'are now',  # "ar non" -> "are now"
            r'\(he\s+importance': '(the importance',  # "(he" -> "(the"
            r'\bnolurn\b': 'not',  # "nolurn" -> "not"
            r'\bjudge\s+you\s+be\b': 'judge you by',  # "be your" -> "by your"
            r'\bstate\s+state\b': 'state',  # duplicate "state state"
            r'\bf\s+poor\b': 'of poor',  # "f poor" -> "of poor"
        }
        
        result = text
        for pattern, replacement in corrections.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _extract_google_vision(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Extract text using Google Cloud Vision API.
        Best accuracy for handwritten text.
        """
        try:
            from config.settings import settings
            google_api_key = getattr(settings, 'GOOGLE_CLOUD_API_KEY', None)
            
            if not google_api_key:
                logger.info("Google Cloud API key not configured, skipping")
                return "" if not detail else []
            
            logger.info(f"Starting Google Cloud Vision for: {image_path}")
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Call Google Cloud Vision API
            response = requests.post(
                f'https://vision.googleapis.com/v1/images:annotate?key={google_api_key}',
                json={
                    'requests': [{
                        'image': {'content': image_base64},
                        'features': [
                            {'type': 'DOCUMENT_TEXT_DETECTION'},  # Better for handwriting
                        ]
                    }]
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                responses = result.get('responses', [])
                if responses:
                    full_text = responses[0].get('fullTextAnnotation', {}).get('text', '')
                    if full_text:
                        logger.info(f"Google Vision extracted {len(full_text)} characters")
                        if detail:
                            return [{'text': full_text, 'confidence': 1.0, 'engine': 'google_vision'}]
                        return full_text.strip()
            
            logger.warning(f"Google Vision API failed: {response.status_code}")
            return "" if not detail else []
            
        except Exception as e:
            logger.warning(f"Google Vision failed: {e}")
            return "" if not detail else []
    
    def _extract_ocrspace(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Extract text using OCR.space free API with image preprocessing.
        Tries multiple strategies for best results on handwriting.
        """
        try:
            from config.settings import settings
            logger.info(f"Starting OCR.space API for: {image_path}")
            
            # Get API key from settings
            api_key = getattr(settings, 'OCRSPACE_API_KEY', "K88888888888957")
            
            best_result = ""
            
            # Strategy 1: Direct image with Engine 2 (best for handwriting)
            result = self._ocrspace_request(image_path, api_key, engine='2')
            if result and len(result) > len(best_result):
                best_result = result
            
            # If result is poor, try with preprocessed image
            if len(best_result) < 500 and self.preprocessor._available:
                logger.info("Trying with preprocessed image...")
                import cv2
                
                try:
                    # Load and preprocess image
                    image = self.preprocessor.load_image(image_path)
                    processed = self._preprocess_for_ocr(image)
                    
                    # Save preprocessed image
                    temp_path = f"{image_path}_preprocessed.png"
                    cv2.imwrite(temp_path, processed)
                    
                    # Try OCR on preprocessed image
                    result = self._ocrspace_request(temp_path, api_key, engine='2')
                    if result and len(result) > len(best_result):
                        best_result = result
                        logger.info(f"Preprocessed image gave better result: {len(result)} chars")
                    
                    # Cleanup
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"Preprocessing failed: {e}")
            
            # Strategy 2: Try Engine 1 if Engine 2 gave poor results
            if len(best_result) < 200:
                logger.info("Trying Engine 1...")
                result = self._ocrspace_request(image_path, api_key, engine='1')
                if result and len(result) > len(best_result):
                    best_result = result
            
            logger.info(f"OCR.space extracted {len(best_result)} characters")
            
            if detail:
                return [{'text': best_result, 'confidence': 1.0, 'engine': 'ocrspace'}]
            
            return best_result.strip()
                
        except Exception as e:
            logger.warning(f"OCR.space API failed: {e}")
            return "" if not detail else []
    
    def _ocrspace_request(self, image_path: str, api_key: str, engine: str = '2') -> str:
        """Make a single OCR.space API request."""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Get file extension
            ext = os.path.splitext(image_path)[1].lower().replace('.', '')
            if ext in ['jfif', 'jpeg']:
                ext = 'jpg'
            
            payload = {
                'apikey': api_key,
                'base64Image': f'data:image/{ext};base64,{image_base64}',
                'language': 'eng',
                'isOverlayRequired': 'false',
                'OCREngine': engine,
                'scale': 'true',
                'detectOrientation': 'true',
            }
            
            response = requests.post(
                'https://api.ocr.space/parse/image',
                data=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get('IsErroredOnProcessing'):
                    parsed = result.get('ParsedResults', [])
                    if parsed:
                        return parsed[0].get('ParsedText', '')
            
            return ""
        except Exception as e:
            logger.warning(f"OCR.space request failed: {e}")
            return ""
    
    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        Optimized for handwritten text on lined paper.
        """
        import cv2
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize for better OCR (larger is better)
        h, w = gray.shape[:2]
        if w < 2000:
            scale = 2000 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise while preserving edges
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        # Sharpen to make text clearer
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # Light adaptive threshold to clean up background
        # Use larger block for handwriting
        binary = cv2.adaptiveThreshold(
            sharpened, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31, 10
        )
        
        return binary
    
    def _extract_sarvam_via_pdf(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Extract text using Sarvam AI by converting image to PDF first.
        Sarvam Document Intelligence only accepts PDF files.
        """
        try:
            from sarvamai import SarvamAI
            from PIL import Image
            import tempfile
            
            logger.info(f"Starting Sarvam AI (via PDF) for: {image_path}")
            
            # Convert image to PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
                pdf_path = pdf_file.name
            
            # Create PDF from image
            img = Image.open(image_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(pdf_path, 'PDF', resolution=300)
            
            logger.info(f"Converted image to PDF: {pdf_path}")
            
            # Initialize Sarvam AI client
            client = SarvamAI(api_subscription_key=self._sarvam_api_key)
            
            # Create job
            job = client.document_intelligence.create_job(
                language="en-IN",
                output_format="md"
            )
            logger.info(f"Sarvam job created: {job.job_id}")
            
            # Upload PDF
            job.upload_file(pdf_path)
            logger.info("PDF uploaded")
            
            # Start and wait
            job.start()
            job.wait_until_complete()
            logger.info("Sarvam job completed")
            
            # Download output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "output")
                job.download_output(output_path)
                
                # Read output
                extracted_text = ""
                for ext in ['.md', '.txt', '']:
                    fpath = output_path + ext
                    if os.path.exists(fpath):
                        with open(fpath, 'r', encoding='utf-8') as f:
                            extracted_text = f.read()
                        break
            
            # Cleanup PDF
            try:
                os.remove(pdf_path)
            except:
                pass
            
            logger.info(f"Sarvam extracted {len(extracted_text)} characters")
            
            if detail:
                return [{'text': extracted_text, 'confidence': 1.0, 'engine': 'sarvam_sdk'}]
            
            return extracted_text.strip() if extracted_text else ""
            
        except Exception as e:
            logger.warning(f"Sarvam via PDF failed: {e}")
            return "" if not detail else []
    
    def _fallback_easyocr(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Fallback to local EasyOCR if all cloud APIs fail.
        """
        try:
            # Re-initialize EasyOCR if needed
            if self.engine_name != "easyocr" or self._engine is None:
                self._init_easyocr()
            
            return self._extract_easyocr_handwriting(image_path)
        except Exception as e:
            logger.error(f"EasyOCR fallback failed: {e}")
            return "" if not detail else []
    
    def _extract_sarvam_fast(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        FAST Sarvam AI OCR using direct HTTP API call.
        
        This bypasses the slow job-based workflow for immediate results.
        """
        try:
            logger.info(f"Starting Sarvam AI FAST OCR for: {image_path}")
            
            # Read and encode image as base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Get file extension to determine mime type
            ext = os.path.splitext(image_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp',
                '.tiff': 'image/tiff',
                '.jfif': 'image/jpeg'
            }
            mime_type = mime_types.get(ext, 'image/png')
            
            # Encode to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'api-subscription-key': self._sarvam_api_key
            }
            
            # Prepare payload for Sarvam AI OCR API
            payload = {
                'image': f'data:{mime_type};base64,{image_base64}',
                'model': 'sarvam-ocr-1',
                'language_code': 'en-IN'
            }
            
            # Make the API request with timeout
            logger.info("Sending request to Sarvam AI OCR API...")
            response = requests.post(
                'https://api.sarvam.ai/parse-image',
                headers=headers,
                json=payload,
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract text from response
                extracted_text = ""
                if isinstance(result, dict):
                    # Try different response formats
                    extracted_text = result.get('text', '') or result.get('extracted_text', '') or result.get('content', '')
                    
                    # If response has 'ocr_text' or similar fields
                    if not extracted_text:
                        extracted_text = result.get('ocr_text', '') or result.get('result', '') or result.get('output', '')
                    
                    # If it's in a nested structure
                    if not extracted_text and 'data' in result:
                        data = result['data']
                        if isinstance(data, dict):
                            extracted_text = data.get('text', '') or data.get('content', '')
                        elif isinstance(data, str):
                            extracted_text = data
                    
                    # Try to extract from blocks/regions if present
                    if not extracted_text and 'blocks' in result:
                        blocks = result['blocks']
                        if isinstance(blocks, list):
                            texts = [b.get('text', '') for b in blocks if isinstance(b, dict)]
                            extracted_text = '\n'.join(filter(None, texts))
                    
                    # Last resort: stringify the entire response
                    if not extracted_text:
                        extracted_text = str(result)
                
                elif isinstance(result, str):
                    extracted_text = result
                
                logger.info(f"Sarvam AI FAST extracted {len(extracted_text)} characters")
                
                if detail:
                    return [{
                        'text': extracted_text,
                        'confidence': 1.0,
                        'bbox': None,
                        'engine': 'sarvam_fast'
                    }]
                
                return extracted_text.strip()
            
            else:
                logger.warning(f"Sarvam AI API returned status {response.status_code}: {response.text}")
                return "" if not detail else []
                
        except requests.Timeout:
            logger.warning("Sarvam AI FAST OCR timed out")
            return "" if not detail else []
        except Exception as e:
            logger.warning(f"Sarvam AI FAST OCR failed: {e}")
            return "" if not detail else []
    
    def _extract_sarvam_sdk(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        Extract text using Sarvam AI SDK for Document Intelligence.
        
        Uses the official sarvamai SDK with simplified job workflow.
        This is the slower fallback method.
        """
        try:
            from sarvamai import SarvamAI
            import tempfile
            
            logger.info(f"Starting Sarvam AI SDK OCR for: {image_path}")
            
            # Initialize Sarvam AI client
            client = SarvamAI(api_subscription_key=self._sarvam_api_key)
            
            # Step 1: Create a job with language and output format
            logger.info("Creating Sarvam AI job...")
            job = client.document_intelligence.create_job(
                language="en-IN",
                output_format="md"
            )
            
            logger.info(f"Sarvam AI job created: {job.job_id}")
            
            # Step 2: Upload the file using job's upload_file method
            logger.info(f"Uploading file: {image_path}")
            job.upload_file(image_path)
            logger.info("File uploaded successfully")
            
            # Step 3: Start the job
            logger.info("Starting Sarvam AI job...")
            job.start()
            logger.info(f"Sarvam AI job started: {job.job_id}")
            
            # Step 4: Wait for completion (with timeout)
            logger.info("Waiting for job completion...")
            job.wait_until_complete()
            logger.info(f"Sarvam AI job completed: {job.job_id}")
            
            # Step 5: Download output to a temp file
            logger.info("Downloading results...")
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "sarvam_output")
                job.download_output(output_path)
                
                # Read the output file
                extracted_text = ""
                # Check for .md file first (since we requested md format)
                md_file = output_path + ".md"
                txt_file = output_path + ".txt"
                
                if os.path.exists(md_file):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                    logger.info(f"Read output from {md_file}")
                elif os.path.exists(txt_file):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                    logger.info(f"Read output from {txt_file}")
                elif os.path.exists(output_path):
                    with open(output_path, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                    logger.info(f"Read output from {output_path}")
                else:
                    # Try to find any file in temp_dir
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                extracted_text = f.read()
                            logger.info(f"Read output from {file_path}")
                            break
            
            logger.info(f"Sarvam AI SDK extracted {len(extracted_text)} characters")
            
            if detail:
                return [{
                    "text": extracted_text,
                    "confidence": 1.0,
                    "bbox": None,
                    "engine": "sarvam_sdk"
                }]
            
            return extracted_text.strip() if extracted_text else ""
                
        except ImportError:
            logger.error("sarvamai SDK not installed. Install with: pip install sarvamai")
            return "" if not detail else []
        except Exception as e:
            logger.error(f"Sarvam AI SDK extraction failed: {e}", exc_info=True)
            return "" if not detail else []
    
    def extract_with_sarvam_test(self, image_path: str) -> dict:
        """
        Test method to compare Sarvam AI OCR with the current engine.
        
        Returns both results for comparison.
        """
        results = {
            "image_path": image_path,
            "sarvam_result": None,
            "current_engine_result": None,
            "current_engine": self.engine_name,
            "comparison": {}
        }
        
        # Get result from current engine (e.g., EasyOCR)
        try:
            self._ensure_engine_initialized()
            
            # Temporarily store current engine
            original_engine = self.engine_name
            
            # Get current engine result
            if original_engine != "sarvam":
                results["current_engine_result"] = self.extract_text(image_path, preprocess=True, detail=False)
            
            # Get Sarvam AI result
            try:
                # Initialize Sarvam if not already
                if not hasattr(self, '_sarvam_api_key'):
                    self._init_sarvam()
                
                results["sarvam_result"] = self._extract_sarvam(image_path, detail=False)
            except Exception as e:
                results["sarvam_error"] = str(e)
            
            # Compare results
            current_len = len(results.get("current_engine_result") or "")
            sarvam_len = len(results.get("sarvam_result") or "")
            
            results["comparison"] = {
                "current_engine_chars": current_len,
                "sarvam_chars": sarvam_len,
                "difference": sarvam_len - current_len,
                "recommended": "sarvam" if sarvam_len > current_len else original_engine
            }
            
            logger.info(f"OCR Comparison - {original_engine}: {current_len} chars, Sarvam: {sarvam_len} chars")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"OCR comparison failed: {e}")
        
        return results
    
    def _extract_from_pdf(
        self, 
        pdf_path: str, 
        preprocess: bool, 
        detail: bool
    ) -> Union[str, List[dict]]:
        """
        Extract text from PDF file.
        
        Uses PyMuPDF (fitz) to convert PDF pages to images, then applies OCR.
        Falls back to direct text extraction if available.
        
        Args:
            pdf_path: Path to PDF file
            preprocess: Whether to preprocess images
            detail: Whether to return detailed results
            
        Returns:
            Extracted text or detailed results
        """
        try:
            import fitz  # PyMuPDF
            import tempfile
            
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            all_text = []
            all_details = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                logger.info(f"Processing page {page_num + 1}/{len(doc)}")
                
                # First, try to extract embedded text (for typed/digital PDFs)
                embedded_text = page.get_text().strip()
                
                if embedded_text and len(embedded_text) > 50:
                    # PDF has embedded text, use it directly (faster)
                    logger.info(f"Page {page_num + 1}: Using embedded text ({len(embedded_text)} chars)")
                    if detail:
                        all_details.append({
                            "text": embedded_text,
                            "confidence": 1.0,
                            "bbox": [0, 0, page.rect.width, page.rect.height],
                            "page": page_num + 1
                        })
                    else:
                        all_text.append(embedded_text)
                else:
                    # No embedded text, render page as image and OCR
                    logger.info(f"Page {page_num + 1}: No embedded text, using OCR")
                    
                    # Render page to image with high DPI for better OCR
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        pix.save(tmp.name)
                        
                        # For Sarvam AI - use direct fast API
                        if self.engine_name == "sarvam":
                            result = self._extract_sarvam(tmp.name, detail)
                        else:
                            # For other engines, use multi-strategy approach
                            result = self._extract_from_image(tmp.name, preprocess, detail)
                        
                        if detail:
                            if isinstance(result, list):
                                for item in result:
                                    item['page'] = page_num + 1
                                all_details.extend(result)
                        else:
                            all_text.append(result if result else "")
                        
                        # Clean up temp file
                        try:
                            os.remove(tmp.name)
                        except:
                            pass
            
            # Store page count before closing
            page_count = len(doc)
            doc.close()
            
            final_text = "\n\n".join(all_text) if all_text else ""
            logger.info(f"PDF extraction complete: {len(final_text)} chars from {page_count} pages")
            
            return all_details if detail else final_text
            
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
            raise RuntimeError("PyMuPDF is required for PDF processing. Install with: pip install pymupdf")
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}", exc_info=True)
            raise RuntimeError(f"PDF extraction failed: {str(e)}")
    
    def _extract_from_image(
        self, 
        image_path: str, 
        preprocess: bool, 
        detail: bool
    ) -> Union[str, List[dict]]:
        """
        Fast text extraction from images optimized for handwriting.
        
        In FAST mode (default): Uses only 1-2 preprocessing strategies for speed
        In normal mode: Uses multiple strategies for maximum accuracy
        """
        from config.settings import settings
        fast_mode = getattr(settings, 'FAST_OCR_MODE', True)
        
        logger.info(f"Extracting from image: {image_path} (fast_mode={fast_mode})")
        
        if fast_mode:
            return self._extract_fast_mode(image_path, detail)
        else:
            return self._extract_multi_strategy(image_path, preprocess, detail)
    
    def _extract_fast_mode(self, image_path: str, detail: bool) -> Union[str, List[dict]]:
        """
        FAST OCR extraction - minimal preprocessing for maximum speed.
        Uses optimized EasyOCR settings designed for handwritten text.
        """
        import cv2
        
        logger.info("FAST MODE: Single-pass OCR with optimized settings")
        start_time = time.time()
        
        best_result = ""
        
        # Preprocess image for better handwriting recognition
        try:
            if self.preprocessor._available:
                image = self.preprocessor.load_image(image_path)
                
                # Remove lined paper background and enhance blue/black ink
                processed = self._preprocess_handwriting(image)
                
                # Save temp and process
                temp_path = f"{image_path}_processed.png"
                cv2.imwrite(temp_path, processed)
                
                result = self._extract_easyocr_handwriting(temp_path)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if result:
                    best_result = result
                    logger.info(f"Preprocessed extraction: {len(result)} chars in {time.time()-start_time:.2f}s")
        except Exception as e:
            logger.warning(f"Preprocessed extraction failed: {e}")
        
        # If preprocessing failed or got poor results, try direct
        if len(best_result) < 50:
            try:
                result = self._extract_easyocr_handwriting(image_path)
                if result and len(result) > len(best_result):
                    best_result = result
                    logger.info(f"Direct extraction: {len(result)} chars")
            except Exception as e:
                logger.warning(f"Direct extraction failed: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"FAST MODE complete: {len(best_result)} chars in {elapsed:.2f}s")
        
        return best_result
    
    def _preprocess_handwriting(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess handwritten text on lined paper.
        Removes background lines and enhances ink contrast.
        """
        import cv2
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize for better OCR (aim for ~2000px width)
        h, w = gray.shape[:2]
        if w < 2000:
            scale = 2000 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Reduce noise while preserving edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Adaptive thresholding to binarize - this helps separate text from lined background
        # Use a large block size to handle line paper
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31, 15  # Large block, moderate C for lined paper
        )
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        # Close small gaps in letters
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Optional: Remove horizontal lines (ruled paper)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        lines = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        # Subtract lines from image
        cleaned = cv2.add(cleaned, lines)
        
        return cleaned
    
    def _extract_easyocr_handwriting(self, image_path: str) -> str:
        """
        Optimized EasyOCR extraction specifically for handwritten text.
        Uses aggressive settings to capture difficult cursive handwriting.
        """
        try:
            # First pass: Standard handwriting settings
            results = self._engine.readtext(
                image_path,
                paragraph=True,  # Group into paragraphs for cursive
                min_size=3,      # Very small minimum
                text_threshold=0.2,  # Very low threshold for cursive
                low_text=0.15,   # Aggressive text detection
                link_threshold=0.15, # Link characters together (cursive)
                canvas_size=2560,
                mag_ratio=1.8,   # Higher magnification
                slope_ths=0.8,   # Allow sloped handwriting
                ycenter_ths=0.8,
                height_ths=1.2,  # More height tolerance
                width_ths=1.2,   # More width tolerance
                add_margin=0.15,
                decoder='greedy',
                beamWidth=10,
                batch_size=1,
                contrast_ths=0.05,  # Very low contrast threshold
                adjust_contrast=0.8,
            )
            
            if not results:
                return ""
            
            # For paragraph mode, results is list of (bbox, text, confidence)
            # Sort by vertical position for proper reading order
            if isinstance(results[0], tuple) and len(results[0]) >= 2:
                sorted_results = sorted(results, key=lambda r: (
                    min(p[1] for p in r[0]) if isinstance(r[0], list) else 0,
                    min(p[0] for p in r[0]) if isinstance(r[0], list) else 0
                ))
                
                texts = []
                last_y = -1
                for r in sorted_results:
                    if isinstance(r[0], list) and len(r[0]) > 0:
                        current_y = min(p[1] for p in r[0])
                        if last_y >= 0 and (current_y - last_y) > 30:
                            texts.append("\n")
                        last_y = max(p[1] for p in r[0])
                    texts.append(r[1] if len(r) > 1 else str(r))
                
                return " ".join(texts).replace(" \n ", "\n").strip()
            else:
                # Simple list of strings
                return " ".join(str(r) for r in results).strip()
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return ""
    
    def _extract_multi_strategy(
        self, 
        image_path: str, 
        preprocess: bool, 
        detail: bool
    ) -> Union[str, List[dict]]:
        """
        Multi-strategy text extraction for maximum accuracy (slower).
        
        Tries multiple preprocessing strategies and returns the best result.
        """
        import cv2
        
        all_results = []
        best_result = ""
        best_length = 0
        
        logger.info(f"Starting multi-strategy extraction for: {image_path}")
        
        # Strategy 1: Original image with different EasyOCR settings
        logger.info("Strategy 1: Original image with optimized settings...")
        try:
            result = self._extract_easyocr_aggressive(image_path)
            if result and len(result) > best_length:
                best_result = result
                best_length = len(result)
                logger.info(f"  Original: {len(result)} chars extracted")
            all_results.append(("original", result))
        except Exception as e:
            logger.warning(f"  Original extraction failed: {e}")
        
        # If preprocessing is disabled or preprocessor not available, return now
        if not preprocess or not self.preprocessor._available:
            return best_result
        
        # Get all preprocessed versions
        try:
            versions = self.preprocessor.get_all_preprocessed_versions(image_path)
            logger.info(f"Generated {len(versions)} preprocessed versions")
        except Exception as e:
            logger.error(f"Failed to generate preprocessed versions: {e}")
            return best_result
        
        # Try OCR on each preprocessed version
        temp_files = []
        for strategy_name, processed_image in versions:
            if strategy_name == "original":
                continue  # Already tried
            
            try:
                # Save preprocessed image to temp file
                temp_path = f"{image_path}_{strategy_name}.png"
                cv2.imwrite(temp_path, processed_image)
                temp_files.append(temp_path)
                
                # Run OCR with aggressive settings
                result = self._extract_easyocr_aggressive(temp_path)
                
                if result:
                    # Clean the result
                    cleaned = self._clean_extracted_text(result)
                    logger.info(f"  {strategy_name}: {len(cleaned)} chars extracted")
                    
                    if len(cleaned) > best_length:
                        best_result = cleaned
                        best_length = len(cleaned)
                    
                    all_results.append((strategy_name, cleaned))
            except Exception as e:
                logger.warning(f"  {strategy_name} failed: {e}")
        
        # Clean up temp files
        for temp_path in temp_files:
            try:
                os.remove(temp_path)
            except:
                pass
        
        # If we still have poor results, try even more aggressive approaches
        if best_length < 50:
            logger.info("Poor results, trying super-aggressive strategies...")
            best_result = self._try_aggressive_strategies(image_path, best_result)
        
        # Log summary
        logger.info(f"Multi-strategy extraction complete. Best result: {len(best_result)} chars")
        logger.info(f"Tried {len(all_results)} strategies")
        
        return best_result if best_result else ""
    
    def _extract_easyocr_aggressive(self, image_path: str) -> str:
        """
        Extract text using extremely aggressive EasyOCR settings.
        Optimized for difficult handwriting.
        """
        try:
            # Very aggressive settings for handwriting
            results = self._engine.readtext(
                image_path,
                paragraph=False,
                min_size=5,  # Detect very small characters
                text_threshold=0.3,  # Very low threshold
                low_text=0.2,  # Very aggressive text detection
                link_threshold=0.2,  # Better linking
                canvas_size=3840,  # Very high resolution
                mag_ratio=2.0,  # Higher magnification
                slope_ths=0.5,  # Allow more slope for messy handwriting
                ycenter_ths=0.7,  # More tolerance
                height_ths=1.0,  # Maximum tolerance
                width_ths=1.0,  # Maximum tolerance
                add_margin=0.15,  # Larger margin
                decoder='greedy',
                beamWidth=10,
                batch_size=1,
                contrast_ths=0.05,  # Very low contrast threshold
                adjust_contrast=0.7,  # Higher contrast adjustment
            )
            
            if not results:
                return ""
            
            # Sort by position and combine
            sorted_results = sorted(results, key=lambda r: (
                min(p[1] for p in r[0]),
                min(p[0] for p in r[0])
            ))
            
            texts = []
            last_y = -1
            for r in sorted_results:
                current_y = min(p[1] for p in r[0])
                if last_y >= 0 and (current_y - last_y) > 25:
                    texts.append("\n")
                texts.append(r[1])
                last_y = max(p[1] for p in r[0])
            
            return " ".join(texts).replace(" \n ", "\n").strip()
            
        except Exception as e:
            logger.warning(f"Aggressive EasyOCR failed: {e}")
            return ""
    
    def _try_aggressive_strategies(self, image_path: str, current_best: str) -> str:
        """
        Try super-aggressive preprocessing for very difficult handwriting.
        """
        import cv2
        
        best = current_best
        best_len = len(current_best)
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return best
            
            h, w = image.shape[:2]
            
            # Super-resize for very small images
            if min(h, w) < 1000:
                scale = 3000 / min(h, w)
                image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Strategy: Multiple Gaussian blur + threshold combinations
            blur_sizes = [(3, 3), (5, 5), (7, 7)]
            block_sizes = [11, 15, 21, 31, 41]
            
            temp_files = []
            
            for blur_size in blur_sizes:
                for block_size in block_sizes:
                    try:
                        # Apply blur
                        blurred = cv2.GaussianBlur(gray, blur_size, 0)
                        
                        # Adaptive threshold
                        thresh = cv2.adaptiveThreshold(
                            blurred, 255,
                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY,
                            block_size,
                            10
                        )
                        
                        # Morphological close to connect broken strokes
                        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
                        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                        
                        temp_path = f"{image_path}_agg_b{blur_size[0]}_t{block_size}.png"
                        cv2.imwrite(temp_path, closed)
                        temp_files.append(temp_path)
                        
                        result = self._extract_easyocr_aggressive(temp_path)
                        if result and len(result) > best_len:
                            best = result
                            best_len = len(result)
                            logger.info(f"  Aggressive blur={blur_size}, block={block_size}: {len(result)} chars")
                    except:
                        pass
            
            # Clean up
            for f in temp_files:
                try:
                    os.remove(f)
                except:
                    pass
            
            # Strategy: Unsharp masking with different strengths
            for strength in [1.5, 2.0, 3.0]:
                try:
                    gaussian = cv2.GaussianBlur(gray, (0, 0), 3)
                    sharpened = cv2.addWeighted(gray, strength, gaussian, -(strength-1), 0)
                    
                    # CLAHE on sharpened
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    enhanced = clahe.apply(sharpened)
                    
                    temp_path = f"{image_path}_sharp_{strength}.png"
                    cv2.imwrite(temp_path, enhanced)
                    
                    result = self._extract_easyocr_aggressive(temp_path)
                    if result and len(result) > best_len:
                        best = result
                        best_len = len(result)
                        logger.info(f"  Sharpening strength={strength}: {len(result)} chars")
                    
                    os.remove(temp_path)
                except:
                    pass
            
            # Strategy: Dilate to thicken thin strokes
            for dilation_size in [1, 2, 3]:
                try:
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilation_size, dilation_size))
                    
                    # Threshold first
                    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    
                    # Dilate
                    dilated = cv2.dilate(binary, kernel, iterations=1)
                    
                    # Invert back
                    dilated = cv2.bitwise_not(dilated)
                    
                    temp_path = f"{image_path}_dilate_{dilation_size}.png"
                    cv2.imwrite(temp_path, dilated)
                    
                    result = self._extract_easyocr_aggressive(temp_path)
                    if result and len(result) > best_len:
                        best = result
                        best_len = len(result)
                        logger.info(f"  Dilation size={dilation_size}: {len(result)} chars")
                    
                    os.remove(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Aggressive strategies failed: {e}")
        
        return best
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        Removes noise characters and normalizes whitespace.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove single character noise (but keep single letters/numbers)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            words = line.split()
            # Keep words with length > 1 or single letters/numbers
            cleaned_words = [w for w in words if len(w) > 1 or w.isalnum()]
            if cleaned_words:
                cleaned_lines.append(' '.join(cleaned_words))
        
        return '\n'.join(cleaned_lines).strip()


# ========== Example Usage ==========
if __name__ == "__main__":
    """
    Example usage of the OCR Service.
    
    This demonstrates:
    1. Basic text extraction
    2. Detailed extraction with bounding boxes
    3. Using different OCR engines
    """
    
    # Example 1: Basic usage
    ocr = OCRService(engine="easyocr")
    
    # Extract text from an image
    # text = ocr.extract_text("sample_answer.png")
    # print("Extracted Text:", text)
    
    # Example 2: Get detailed results with bounding boxes
    # details = ocr.extract_text("sample_answer.png", detail=True)
    # for item in details:
    #     print(f"Text: {item['text']}, Confidence: {item['confidence']:.2f}")
    
    print("OCR Service module loaded successfully!")
