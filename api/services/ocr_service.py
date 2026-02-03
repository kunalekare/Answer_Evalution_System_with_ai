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
        
        self.engine_name = engine or settings.OCR_ENGINE
        self.languages = languages or settings.OCR_LANGUAGES
        self.preprocessor = ImagePreprocessor()
        
        # Initialize the selected engine
        self._engine = None
        self._init_engine()
    
    def _init_engine(self):
        """Initialize the selected OCR engine."""
        logger.info(f"Initializing OCR engine: {self.engine_name}")
        
        if self.engine_name == "easyocr":
            self._init_easyocr()
        elif self.engine_name == "tesseract":
            self._init_tesseract()
        elif self.engine_name == "paddleocr":
            self._init_paddleocr()
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
        logger.info(f"Extracting text from: {image_path}")
        
        # Validate file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Handle PDF files
        if image_path.lower().endswith('.pdf'):
            return self._extract_from_pdf(image_path, preprocess, detail)
        
        # For image files, use the multi-approach extraction method
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
                        
                        # Extract text from this page image
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
        Advanced multi-strategy text extraction from images.
        
        This method tries MULTIPLE preprocessing strategies and combines
        results for maximum handwriting extraction accuracy.
        
        Strategies:
        1. Original image
        2. Multiple CLAHE contrast levels
        3. Various adaptive threshold block sizes
        4. Morphological operations
        5. Denoising combinations
        6. Edge enhancement
        7. Inverted images
        
        The best result (longest meaningful text) is returned.
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
