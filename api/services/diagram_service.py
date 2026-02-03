"""
Diagram Evaluation Service
===========================
Visual comparison of student diagrams against model diagrams.

This module provides diagram evaluation capabilities:
- Structural Similarity Index (SSIM) - pixel-wise comparison
- Feature Matching (ORB/SIFT) - structural comparison
- Contour Analysis - shape comparison

Why Diagram Evaluation is Challenging:
=====================================
1. Scale differences: Student may draw smaller/larger
2. Position differences: Drawing not in same location
3. Rotation: Slight tilts in drawing
4. Style differences: Different line thickness, handwriting

Our Approach:
=============
1. SSIM (Structural Similarity Index):
   - Compares luminance, contrast, and structure
   - Good for pixel-level similarity
   
2. Feature Matching (ORB/SIFT):
   - Detects key points (corners, edges)
   - Matches features regardless of scale/rotation
   - More robust to variations
   
3. Contour Analysis:
   - Extracts shapes from diagrams
   - Compares shape count and properties
"""

import logging
from typing import Tuple, List, Optional, Dict
import numpy as np
from pathlib import Path

logger = logging.getLogger("AssessIQ.Diagram")


class DiagramEvaluator:
    """
    Diagram Evaluation using Computer Vision techniques.
    
    This class compares student diagrams with model diagrams using:
    1. SSIM - Structural similarity
    2. ORB Feature Matching - Key point matching
    3. Contour Analysis - Shape comparison
    
    Usage:
        evaluator = DiagramEvaluator()
        score = evaluator.evaluate("model_diagram.png", "student_diagram.png")
        # Returns score from 0 to 10
    """
    
    def __init__(self):
        """Initialize diagram evaluator with OpenCV."""
        try:
            import cv2
            self.cv2 = cv2
            self._available = True
            logger.info("DiagramEvaluator initialized with OpenCV")
        except ImportError:
            logger.error("OpenCV not installed. Install with: pip install opencv-python")
            self._available = False
    
    def load_and_preprocess(
        self, 
        image_path: str,
        target_size: Tuple[int, int] = (500, 500)
    ) -> np.ndarray:
        """
        Load and preprocess image for comparison.
        
        Steps:
        1. Load image
        2. Convert to grayscale
        3. Resize to standard size
        4. Apply Gaussian blur
        5. Apply thresholding
        
        Args:
            image_path: Path to image file
            target_size: Size to resize image to (width, height)
            
        Returns:
            Preprocessed grayscale image
        """
        if not self._available:
            raise RuntimeError("OpenCV is not available")
        
        # Load image
        image = self.cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
        
        # Resize to standard size (important for fair comparison)
        gray = self.cv2.resize(gray, target_size)
        
        # Apply Gaussian blur to reduce noise
        gray = self.cv2.GaussianBlur(gray, (5, 5), 0)
        
        return gray
    
    def calculate_ssim(
        self, 
        image1: np.ndarray, 
        image2: np.ndarray
    ) -> float:
        """
        Calculate Structural Similarity Index (SSIM) between two images.
        
        SSIM compares:
        - Luminance: brightness comparison
        - Contrast: contrast comparison
        - Structure: structural pattern comparison
        
        Range: -1 to 1 (1 = identical)
        
        Args:
            image1: First grayscale image
            image2: Second grayscale image
            
        Returns:
            SSIM score between -1 and 1
        """
        try:
            from skimage.metrics import structural_similarity as ssim
            
            # Ensure images are same size
            if image1.shape != image2.shape:
                image2 = self.cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            # Calculate SSIM
            score, _ = ssim(image1, image2, full=True)
            
            logger.debug(f"SSIM Score: {score:.4f}")
            return score
            
        except ImportError:
            logger.warning("scikit-image not installed, using OpenCV method")
            return self._calculate_ssim_opencv(image1, image2)
    
    def _calculate_ssim_opencv(
        self, 
        image1: np.ndarray, 
        image2: np.ndarray
    ) -> float:
        """
        Calculate SSIM using pure OpenCV (fallback method).
        
        This is a simplified implementation of SSIM.
        """
        # Constants
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        # Convert to float
        img1 = image1.astype(np.float64)
        img2 = image2.astype(np.float64)
        
        # Calculate means
        mu1 = self.cv2.GaussianBlur(img1, (11, 11), 1.5)
        mu2 = self.cv2.GaussianBlur(img2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        # Calculate variances and covariance
        sigma1_sq = self.cv2.GaussianBlur(img1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = self.cv2.GaussianBlur(img2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = self.cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
        
        # Calculate SSIM
        numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
        denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
        
        ssim_map = numerator / denominator
        
        return float(np.mean(ssim_map))
    
    def extract_features_orb(
        self, 
        image: np.ndarray,
        n_features: int = 500
    ) -> Tuple[List, np.ndarray]:
        """
        Extract ORB (Oriented FAST and Rotated BRIEF) features.
        
        ORB is a fast and efficient feature detector that:
        - Detects corners and interesting points
        - Creates descriptors for each point
        - Is rotation and scale invariant
        
        Args:
            image: Grayscale image
            n_features: Maximum number of features to detect
            
        Returns:
            Tuple of (keypoints, descriptors)
        """
        # Create ORB detector
        orb = self.cv2.ORB_create(nfeatures=n_features)
        
        # Detect keypoints and compute descriptors
        keypoints, descriptors = orb.detectAndCompute(image, None)
        
        logger.debug(f"Detected {len(keypoints)} ORB features")
        
        return keypoints, descriptors
    
    def match_features(
        self, 
        desc1: np.ndarray, 
        desc2: np.ndarray,
        ratio_threshold: float = 0.75
    ) -> List:
        """
        Match features between two images using Brute Force matching.
        
        Uses Lowe's ratio test to filter good matches:
        - For each feature, find 2 nearest neighbors
        - Keep match only if distance ratio < threshold
        
        Args:
            desc1: Descriptors from first image
            desc2: Descriptors from second image
            ratio_threshold: Lowe's ratio threshold
            
        Returns:
            List of good matches
        """
        if desc1 is None or desc2 is None:
            return []
        
        # Create BF matcher
        bf = self.cv2.BFMatcher(self.cv2.NORM_HAMMING, crossCheck=False)
        
        try:
            # Find 2 nearest neighbors for each descriptor
            matches = bf.knnMatch(desc1, desc2, k=2)
            
            # Apply Lowe's ratio test
            good_matches = []
            for match in matches:
                if len(match) == 2:
                    m, n = match
                    if m.distance < ratio_threshold * n.distance:
                        good_matches.append(m)
            
            logger.debug(f"Found {len(good_matches)} good matches")
            return good_matches
            
        except Exception as e:
            logger.warning(f"Feature matching failed: {e}")
            return []
    
    def calculate_feature_score(
        self, 
        image1: np.ndarray, 
        image2: np.ndarray,
        min_matches: int = 10
    ) -> float:
        """
        Calculate similarity score based on feature matching.
        
        Args:
            image1: First image (model)
            image2: Second image (student)
            min_matches: Minimum matches expected for full score
            
        Returns:
            Score between 0 and 1
        """
        # Extract features
        kp1, desc1 = self.extract_features_orb(image1)
        kp2, desc2 = self.extract_features_orb(image2)
        
        if desc1 is None or desc2 is None:
            logger.warning("No features detected in one or both images")
            return 0.0
        
        # Match features
        good_matches = self.match_features(desc1, desc2)
        
        # Calculate score based on number of matches
        # More matches = higher score
        n_matches = len(good_matches)
        
        # Normalize score (cap at min_matches for full score)
        score = min(n_matches / min_matches, 1.0)
        
        logger.debug(f"Feature match score: {score:.4f} ({n_matches} matches)")
        
        return score
    
    def extract_contours(
        self, 
        image: np.ndarray
    ) -> List:
        """
        Extract contours (shapes) from image.
        
        Contours are curves joining continuous points with same intensity.
        Useful for detecting shapes in diagrams.
        
        Args:
            image: Grayscale image
            
        Returns:
            List of contours
        """
        # Apply thresholding
        _, binary = self.cv2.threshold(
            image, 0, 255, 
            self.cv2.THRESH_BINARY_INV + self.cv2.THRESH_OTSU
        )
        
        # Find contours
        contours, _ = self.cv2.findContours(
            binary, 
            self.cv2.RETR_EXTERNAL, 
            self.cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter small contours (noise)
        min_area = 100
        contours = [c for c in contours if self.cv2.contourArea(c) > min_area]
        
        logger.debug(f"Found {len(contours)} contours")
        
        return contours
    
    def calculate_contour_score(
        self, 
        image1: np.ndarray, 
        image2: np.ndarray
    ) -> float:
        """
        Calculate similarity based on contour analysis.
        
        Compares:
        - Number of shapes
        - Shape properties (area, perimeter ratios)
        
        Args:
            image1: First image (model)
            image2: Second image (student)
            
        Returns:
            Score between 0 and 1
        """
        # Extract contours
        contours1 = self.extract_contours(image1)
        contours2 = self.extract_contours(image2)
        
        n1, n2 = len(contours1), len(contours2)
        
        if n1 == 0 and n2 == 0:
            return 1.0  # Both empty
        if n1 == 0 or n2 == 0:
            return 0.0  # One empty
        
        # Compare number of shapes
        count_ratio = min(n1, n2) / max(n1, n2)
        
        # Compare total area covered by shapes
        area1 = sum(self.cv2.contourArea(c) for c in contours1)
        area2 = sum(self.cv2.contourArea(c) for c in contours2)
        
        area_ratio = min(area1, area2) / max(area1, area2) if max(area1, area2) > 0 else 0
        
        # Combined score
        score = 0.5 * count_ratio + 0.5 * area_ratio
        
        logger.debug(f"Contour score: {score:.4f} (shapes: {n1} vs {n2})")
        
        return score
    
    def evaluate(
        self, 
        model_path: str, 
        student_path: str,
        ssim_weight: float = 0.4,
        feature_weight: float = 0.4,
        contour_weight: float = 0.2
    ) -> float:
        """
        Evaluate student diagram against model diagram.
        
        Combines three methods:
        1. SSIM - Structural similarity
        2. Feature matching - Key point comparison
        3. Contour analysis - Shape comparison
        
        Args:
            model_path: Path to model diagram image
            student_path: Path to student diagram image
            ssim_weight: Weight for SSIM score
            feature_weight: Weight for feature matching score
            contour_weight: Weight for contour analysis score
            
        Returns:
            Combined score from 0 to 10
        """
        if not self._available:
            logger.error("OpenCV not available for diagram evaluation")
            return 0.0
        
        logger.info(f"Evaluating diagram: {student_path}")
        
        try:
            # Load and preprocess images
            model_img = self.load_and_preprocess(model_path)
            student_img = self.load_and_preprocess(student_path)
            
            # Calculate individual scores
            ssim_score = self.calculate_ssim(model_img, student_img)
            ssim_score = (ssim_score + 1) / 2  # Normalize to 0-1
            
            feature_score = self.calculate_feature_score(model_img, student_img)
            contour_score = self.calculate_contour_score(model_img, student_img)
            
            # Normalize weights
            total_weight = ssim_weight + feature_weight + contour_weight
            ssim_weight /= total_weight
            feature_weight /= total_weight
            contour_weight /= total_weight
            
            # Combined score
            combined = (
                ssim_score * ssim_weight +
                feature_score * feature_weight +
                contour_score * contour_weight
            )
            
            # Scale to 0-10
            final_score = combined * 10
            
            logger.info(f"Diagram evaluation complete: {final_score:.2f}/10")
            logger.debug(f"  SSIM: {ssim_score:.4f}, Features: {feature_score:.4f}, Contours: {contour_score:.4f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Diagram evaluation failed: {e}")
            return 0.0
    
    def get_detailed_analysis(
        self, 
        model_path: str, 
        student_path: str
    ) -> Dict:
        """
        Get detailed diagram analysis with component scores.
        
        Args:
            model_path: Path to model diagram
            student_path: Path to student diagram
            
        Returns:
            Dictionary with detailed analysis
        """
        if not self._available:
            return {"error": "OpenCV not available"}
        
        try:
            # Load images
            model_img = self.load_and_preprocess(model_path)
            student_img = self.load_and_preprocess(student_path)
            
            # Calculate scores
            ssim_score = self.calculate_ssim(model_img, student_img)
            ssim_normalized = (ssim_score + 1) / 2
            
            feature_score = self.calculate_feature_score(model_img, student_img)
            contour_score = self.calculate_contour_score(model_img, student_img)
            
            # Get additional info
            model_contours = self.extract_contours(model_img)
            student_contours = self.extract_contours(student_img)
            
            _, model_desc = self.extract_features_orb(model_img)
            _, student_desc = self.extract_features_orb(student_img)
            
            return {
                "scores": {
                    "ssim": round(ssim_normalized, 4),
                    "feature_matching": round(feature_score, 4),
                    "contour_analysis": round(contour_score, 4),
                    "overall": round((ssim_normalized + feature_score + contour_score) / 3, 4)
                },
                "analysis": {
                    "model_shapes": len(model_contours),
                    "student_shapes": len(student_contours),
                    "shape_match": len(model_contours) == len(student_contours),
                    "model_features": len(model_desc) if model_desc is not None else 0,
                    "student_features": len(student_desc) if student_desc is not None else 0
                },
                "feedback": self._generate_feedback(
                    ssim_normalized, feature_score, contour_score,
                    len(model_contours), len(student_contours)
                )
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_feedback(
        self,
        ssim: float,
        features: float,
        contours: float,
        model_shapes: int,
        student_shapes: int
    ) -> List[str]:
        """Generate feedback based on diagram analysis."""
        feedback = []
        
        if ssim < 0.5:
            feedback.append("The overall structure differs significantly from the model diagram.")
        elif ssim < 0.7:
            feedback.append("The diagram structure is partially similar to the model.")
        else:
            feedback.append("Good structural similarity with the model diagram.")
        
        if features < 0.3:
            feedback.append("Key elements (corners, edges) are missing or different.")
        elif features > 0.7:
            feedback.append("Most key elements are correctly represented.")
        
        if model_shapes != student_shapes:
            diff = model_shapes - student_shapes
            if diff > 0:
                feedback.append(f"Missing approximately {diff} shape(s) from the model.")
            else:
                feedback.append(f"Has {-diff} extra shape(s) compared to the model.")
        else:
            feedback.append("Correct number of shapes/components.")
        
        return feedback


# ========== Example Usage ==========
if __name__ == "__main__":
    """
    Example usage of the Diagram Evaluator.
    """
    
    print("=" * 60)
    print("Diagram Evaluation Module Demo")
    print("=" * 60)
    
    evaluator = DiagramEvaluator()
    
    if evaluator._available:
        print("\n✅ OpenCV is available")
        print("Ready to evaluate diagrams!")
        
        # Example usage (uncomment with real images):
        # score = evaluator.evaluate("model_diagram.png", "student_diagram.png")
        # print(f"Diagram Score: {score:.2f}/10")
        
        # Detailed analysis:
        # analysis = evaluator.get_detailed_analysis("model.png", "student.png")
        # print(analysis)
    else:
        print("\n❌ OpenCV is not available")
        print("Install with: pip install opencv-python")
    
    print("\nDiagram Evaluation module loaded successfully!")
