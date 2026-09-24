"""Shared model options; importing this module does not load Paddle or NumPy."""

from typing import Any


def paddle_options(language: str = "en") -> dict[str, Any]:
    # Paddle 3 ignores `lang` when any explicit model name is supplied.
    # English selects both mobile models; other languages use Paddle resolution.
    models = (
        {
            "text_detection_model_name": "PP-OCRv5_mobile_det",
            "text_recognition_model_name": "en_PP-OCRv5_mobile_rec",
        }
        if language == "en"
        else {"lang": language, "ocr_version": "PP-OCRv5"}
    )
    return {
        **models,
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
        "device": "cpu",
        "enable_mkldnn": False,
        "cpu_threads": 4,
    }
