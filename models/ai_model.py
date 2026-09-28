import os
from typing import Dict, Tuple

import cv2
import numpy as np

try:
    import tensorflow as tf  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    tf = None


class ImageProcessingError(ValueError):
    """Raised when uploaded image validation fails."""


def validate_image_file(image_path: str) -> Tuple[bool, str]:
    if not image_path or not os.path.exists(image_path):
        return False, "Image not found. Please upload a valid file."

    try:
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return False, "The uploaded file is not a valid image. Please try another file."

        height, width = image.shape[:2]
        if width < 80 or height < 80:
            return False, "The image is too small for reliable AI analysis. Please upload a larger image."

        if image.size == 0:
            return False, "The selected image appears to be empty. Please choose a different file."

        return True, "Image passed validation."
    except Exception as exc:  # pragma: no cover
        return False, f"Image validation failed: {exc}"


def preprocess_image(image_path: str):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageProcessingError("Unable to read the selected image.")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)
    image = image.astype("float32") / 255.0
    return image


def _safe_demo_insight(result_label: str, concern: str) -> Dict[str, object]:
    return {
        "result": result_label,
        "concern": concern,
        "demo_label": "Demo AI Analysis",
        "note": "This is a demo analysis system designed for educational and prototype use. It is not a medical diagnosis."
    }


def _hair_diagnostics(image_array: np.ndarray) -> Dict[str, object]:
    gray = cv2.cvtColor(cv2.cvtColor(image_array.astype("uint8"), cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    contrast = gray.std()

    if brightness < 80:
        label = "Hair appears dull and may need better hydration and scalp care."
        concern = "Dryness / dullness"
    elif contrast > 60:
        label = "Hair texture looks healthy but could benefit from scalp nourishment."
        concern = "Scalp balance concern"
    else:
        label = "Hair appears generally balanced with good overall condition."
        concern = "Low visible concern"

    return {
        "result": label,
        "concern": concern,
        "hair_care": [
            "Use a gentle sulfate-free shampoo to avoid excessive scalp dryness.",
            "Apply a lightweight conditioner from mid-length to ends to reduce breakage.",
            "Trim split ends regularly and avoid excessive heat styling."
        ],
        "diet": [
            "Include protein-rich foods like eggs, lentils, beans, and yogurt for stronger hair.",
            "Add leafy greens, berries, and citrus fruits for vitamins and antioxidants.",
            "Drink adequate water daily to support scalp and hair hydration."
        ],
        "home_care": [
            "Massage scalp gently with warm oil once or twice a week for nourishment.",
            "Keep the scalp clean and avoid harsh products with strong fragrance or alcohol.",
            "Use a satin pillowcase to reduce friction and breakage overnight."
        ],
        "daily_routine": [
            "Wash hair with a mild cleanser based on your scalp condition.",
            "Protect hair with a heat protectant before styling.",
            "Follow a consistent routine with scalp care and regular hydration."
        ],
    }


def _skin_diagnostics(image_array: np.ndarray) -> Dict[str, object]:
    gray = cv2.cvtColor(cv2.cvtColor(image_array.astype("uint8"), cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    contrast = gray.std()

    if brightness < 90:
        label = "Skin tone appears dull and may benefit from gentle hydration and brightness care."
        concern = "Dullness / dehydration"
    elif contrast > 55:
        label = "Skin appears active and balanced, though a mild hydration routine may help."
        concern = "Visible dryness or sensitivity"
    else:
        label = "Skin appears generally balanced and healthy in this demo review."
        concern = "Low visible concern"

    return {
        "result": label,
        "concern": concern,
        "skin_care": [
            "Use a gentle cleanser that does not strip natural hydration from the skin.",
            "Apply a moisturizer suited to your skin type to support a smooth skin barrier.",
            "Use sunscreen daily to protect skin from harmful UV exposure."
        ],
        "diet": [
            "Eat colorful fruits and vegetables rich in antioxidants and vitamins.",
            "Include nuts, seeds, and omega-3 sources such as flaxseeds and walnuts.",
            "Drink plenty of clean water to support skin elasticity and hydration."
        ],
        "home_care": [
            "Avoid harsh scrubs and over-cleansing that can trigger irritation.",
            "Sleep adequately and reduce stress to support skin recovery and tone.",
            "Keep towels, pillowcases, and skincare tools clean to reduce irritation."
        ],
        "daily_routine": [
            "Cleanse gently in the morning and night with a non-stripping formula.",
            "Apply moisturizer and sunscreen in the morning for daily barrier support.",
            "Night care should focus on hydration and recovery before bed."
        ],
    }


def analyze_image_for_type(analysis_type: str, image_path: str) -> Dict[str, object]:
    valid, message = validate_image_file(image_path)
    if not valid:
        raise ImageProcessingError(message)

    processed = preprocess_image(image_path)

    if tf is not None:
        try:
            image_tensor = tf.convert_to_tensor(processed[None, ...], dtype=tf.float32)
            model = None
            # This placeholder keeps the code structure ready for a real TensorFlow model.
            if model is not None:
                prediction = model.predict(image_tensor, verbose=0)
                # This branch is intentionally left for future real model integration.
                if analysis_type.lower() == "hair":
                    return {**_safe_demo_insight("Demo AI Analysis: TensorFlow model output is pending integration.", "Prototype assessment"), **_hair_diagnostics(processed)}
                return {**_safe_demo_insight("Demo AI Analysis: TensorFlow model output is pending integration.", "Prototype assessment"), **_skin_diagnostics(processed)}
        except Exception:
            pass

    if analysis_type.lower() == "hair":
        hair_result = _hair_diagnostics(processed)
        return {
            **_safe_demo_insight("Demo AI Analysis: Hair condition overview", hair_result["concern"]),
            **hair_result,
        }

    skin_result = _skin_diagnostics(processed)
    return {
        **_safe_demo_insight("Demo AI Analysis: Skin condition overview", skin_result["concern"]),
        **skin_result,
    }
