def calculate_score(
    answer_score: float,
    confidence: float,
    attention: float,
    emotion: str
):

    emotion_bonus = {
        "happy": 5,
        "neutral": 3,
        "surprise": 2,
        "fear": -3,
        "sad": -4,
        "angry": -5,
        "disgust": -5
    }

    bonus = emotion_bonus.get(emotion.lower(), 0)

    overall = (
        answer_score * 0.60 +
        confidence * 0.20 +
        attention * 0.20 +
        bonus
    )

    overall = max(0, min(overall, 100))

    if overall >= 85:
        recommendation = "Strong Hire"
    elif overall >= 70:
        recommendation = "Hire"
    elif overall >= 55:
        recommendation = "Consider"
    else:
        recommendation = "Needs Improvement"

    return {
        "overall_score": round(overall, 2),
        "recommendation": recommendation
    }