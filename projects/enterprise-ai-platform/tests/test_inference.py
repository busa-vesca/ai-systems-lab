from typing import Any

from enterprise_ai_platform.inference import HuggingFaceIncidentClassifier


class FakePipeline:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _text: str, **_kwargs: Any) -> dict[str, object]:
        self.calls += 1
        return {
            "labels": ["database failure", "network failure"],
            "scores": [0.91, 0.09],
        }


def test_classifier_maps_model_prompt_to_canonical_label() -> None:
    classifier = HuggingFaceIncidentClassifier()
    fake_pipeline = FakePipeline()
    classifier._pipeline = fake_pipeline

    result = classifier.classify("PostgreSQL connection timeout")

    assert result.label == "database"
    assert result.score == 0.91
    assert fake_pipeline.calls == 1
