import io
import cv2
import numpy as np
import mediapipe as mp
from skimage import filters
from typing import Dict, Any, Tuple
from PIL import Image

# Initialize MediaPipe solutions
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

def _bytes_to_cv2_image(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes to an OpenCV BGR image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def analyze_face(image_bytes: bytes) -> Tuple[Dict[str, str], str, int]:
    """
    Analyze facial features using MediaPipe Face Mesh.
    Returns (analysis_dict, overall_summary, confidence_score).
    """
    img = _bytes_to_cv2_image(image_bytes)
    if img is None:
        raise ValueError("Invalid image data")

    # MediaPipe expects RGB images
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        results = face_mesh.process(img_rgb)
        
        if not results.multi_face_landmarks:
            # Fallback if no face detected
            return (
                {
                    "forehead_structure": "Unclear due to lighting or angle.",
                    "eye_vitality": "Mysterious and hidden aura.",
                    "jawline_determination": "Adaptable but undefined presence.",
                    "aura_color": "Ethereal Grey"
                },
                "I couldn't clearly detect your facial landmarks. Try again with a clear, well-lit portrait photo.",
                40
            )

        landmarks = results.multi_face_landmarks[0].landmark
        
        # Calculate specific facial ratios
        # Forehead (width approx between temples: indices 21, 251) vs Face Height (indices 10 to 152)
        face_height = abs(landmarks[152].y - landmarks[10].y)
        forehead_width = abs(landmarks[251].x - landmarks[21].x)
        forehead_ratio = forehead_width / (face_height + 0.0001)

        # Eye distance (distance between inner corners: 133, 362) vs Eye Width
        eye_distance = abs(landmarks[362].x - landmarks[133].x)
        
        # Jawline width (indices 132 to 361 approx at jaw angles) vs Chin
        jaw_width = abs(landmarks[361].x - landmarks[132].x)
        jaw_ratio = jaw_width / (face_height + 0.0001)

        # Map Ratios to Astrological Traits
        # Forehead (Intellect / Leadership)
        if forehead_ratio > 0.65:
            forehead_trait = "Broad and high, indicating supreme intellect, wisdom, and leadership capability."
        elif forehead_ratio > 0.55:
            forehead_trait = "Rounded and balanced, showing a highly creative and artistic temperament."
        else:
            forehead_trait = "Straight and proportional, pointing to a logical, practical, and grounded nature."

        # Eyes (Perception / Empathy)
        if eye_distance > 0.25:
            eye_trait = "Wide-set, indicating profound empathy, an open heart, and high perceptual awareness."
        elif eye_distance > 0.18:
            eye_trait = "Bright and balanced, suggesting alertness, focus, and strong communicative energy."
        else:
            eye_trait = "Deep-set and close, showing intense analytical skills, focus, and a mysterious aura."

        # Jawline (Willpower / Adaptability)
        if jaw_ratio > 0.65:
            jaw_trait = "Strong and angular, showing immense willpower, determination, and resilience."
        elif jaw_ratio > 0.55:
            jaw_trait = "Soft and oval, indicating a diplomatic, adaptable, and peaceful nature."
        else:
            jaw_trait = "Tapered, pointing to high sensitivity, refined tastes, and intuitive decision-making."

        analysis = {
            "forehead_structure": forehead_trait,
            "eye_vitality": eye_trait,
            "jawline_determination": jaw_trait,
            "aura_color": "Golden Yellow" if forehead_ratio > 0.60 else "Radiant Blue"
        }
        
        summary = "Your facial geometry reflects a highly structured internal character. Your physical ratios indicate a powerful blend of intellect and intuition, ready to tackle upcoming challenges with confidence."
        
        return analysis, summary, 95


