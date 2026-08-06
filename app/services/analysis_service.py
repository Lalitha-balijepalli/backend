from app.services.emotion_service import detect_emotion


def analyze_candidate(image_path: str):

    emotion_result = detect_emotion(image_path)

    return {
        "emotion": emotion_result.get("dominant_emotion", "unknown"),
        "confidence": 85,
        "eye_contact": "Good",
        "head_pose": "Straight",
        "attention": "High",
        "face_detected": True
    }