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


def analyze_palm(image_bytes: bytes) -> Tuple[Dict[str, str], str, int]:
    """
    Analyze palm lines using OpenCV Canny Edges and Scikit-Image Meijering filter.
    Returns (analysis_dict, overall_summary, confidence_score).
    """
    img = _bytes_to_cv2_image(image_bytes)
    if img is None:
        raise ValueError("Invalid image data")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    with mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.5
    ) as hands:
        results = hands.process(img_rgb)
        
        if not results.multi_hand_landmarks:
            # Fallback if no hand detected
            return (
                {
                    "life_line": "Unclear. Ensure the palm is flat and well-lit.",
                    "head_line": "Awaiting a sharper image.",
                    "heart_line": "Obscured by shadows or angle.",
                    "fate_line": "Difficult to read."
                },
                "I couldn't clearly detect your palm structure. Please try again with a flat palm and good lighting.",
                35
            )

        # We found a hand! Let's crop the palm region.
        landmarks = results.multi_hand_landmarks[0].landmark
        h, w, _ = img.shape
        
        # Get bounding box for the palm (roughly wrist 0 to index mcp 5, pinky mcp 17)
        x_coords = [lm.x * w for lm in landmarks[0:21]]
        y_coords = [lm.y * h for lm in landmarks[0:21]]
        
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        
        # Add padding to get the whole palm
        pad = 20
        x_min, x_max = max(0, x_min - pad), min(w, x_max + pad)
        y_min, y_max = max(0, y_min - pad), min(h, y_max + pad)
        
        palm_crop = img[y_min:y_max, x_min:x_max]
        
        # 1. Convert to grayscale
        gray = cv2.cvtColor(palm_crop, cv2.COLOR_BGR2GRAY)
        
        # 2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance lines
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 3. Detect edges using Canny
        edges = cv2.Canny(enhanced, 50, 150)
        
        # Calculate edge density (total edge pixels / total pixels)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_pixels = np.count_nonzero(edges)
        edge_density = edge_pixels / (total_pixels + 1)
        
        # 4. Use scikit-image Meijering neurite filter for deep line detection
        # This highlights long, continuous structures (like palm lines)
        meijering_result = filters.meijering(enhanced)
        line_intensity = np.mean(meijering_result)
        
        # Map structural data to Traits
        # Life Line (Vitality) - related to deep continuous ridges (line_intensity)
        if line_intensity > 0.05:
            life_trait = "Deep and unbroken, showing tremendous vitality, physical stamina, and a strong immune system."
        elif line_intensity > 0.03:
            life_trait = "Average depth, pointing to a balanced and stable life force."
        else:
            life_trait = "Faint and scattered, indicating a need for rest, spiritual grounding, and physical rejuvenation."

        # Head Line (Intellect) - related to overall edge density complexity
        if edge_density > 0.10:
            head_trait = "Curved and heavily etched, showing extreme creativity, a complex imagination, and deep thinking."
        elif edge_density > 0.05:
            head_trait = "Straight and clear, pointing to a very logical, practical, and analytical mindset."
        else:
            head_trait = "Lightly marked, indicating a straightforward, action-oriented approach rather than overthinking."

        # Heart Line (Emotions)
        if edge_density > 0.08 and line_intensity > 0.04:
            heart_trait = "Deep and pronounced, meaning you feel emotions intensely and love deeply."
        elif edge_density < 0.06:
            heart_trait = "Short and straight, showing emotional independence and a rational approach to love."
        else:
            heart_trait = "Wavy and complex, pointing to many diverse relationships and a free-spirited heart."

        # Fate Line (Career)
        if line_intensity > 0.06:
            fate_trait = "Visible and continuous, pointing towards steady, upward career growth and destiny."
        else:
            fate_trait = "Absent or faint, meaning you forge your own unique path outside traditional career bounds."

        analysis = {
            "life_line": life_trait,
            "head_line": head_trait,
            "heart_line": heart_trait,
            "fate_line": fate_trait
        }
        
        summary = "Based on the topographical mapping of your palm ridges, your cosmic imprint reveals a dynamic energy flow. Your lines suggest a strong period of personal revelation and career alignment in the upcoming months."

        return analysis, summary, 92
