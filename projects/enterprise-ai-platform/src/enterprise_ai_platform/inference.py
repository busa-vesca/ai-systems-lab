import logging
import os
from dataclasses import dataclass
from threading import Lock
from time import perf_counter
from typing import Any, Protocol

from .domain import ModelInferenceError


DEFAULT_MODEL_ID = "cross-encoder/nli-MiniLM2-L6-H768"
DEFAULT_MODEL_REVISION = "b95119ce93d3e065de6214e38cd4a97b0f2f2c6d"
DEFAULT_LABEL_PROMPTS = (
    ("database", "database failure"),
    ("network", "network failure"),
    ("authentication", "authentication failure"),
    ("application", "application failure"),
    ("infrastructure", "infrastructure failure"),
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    label: str
    score: float
    model_id: str
    model_revision: str
    latency_ms: float


class IncidentClassifier(Protocol):
    def classify(self, text: str) -> ClassificationResult: ...


class HuggingFaceIncidentClassifier:
    """Lazy, single-instance zero-shot text classifier."""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        model_revision: str = DEFAULT_MODEL_REVISION,
        label_prompts: tuple[tuple[str, str], ...] = DEFAULT_LABEL_PROMPTS,
    ) -> None:
        self.model_id = model_id
        self.model_revision = model_revision
        self.label_prompts = label_prompts
        self._pipeline: Any | None = None
        self._lock = Lock()

    @classmethod
    def from_environment(cls) -> "HuggingFaceIncidentClassifier":
        return cls(
            model_id=os.getenv("HF_MODEL_ID", DEFAULT_MODEL_ID),
            model_revision=os.getenv(
                "HF_MODEL_REVISION", DEFAULT_MODEL_REVISION
            ),
        )

    def _load_pipeline(self) -> Any:
        if self._pipeline is None:
            try:
                from transformers import pipeline

                self._pipeline = pipeline(
                    task="zero-shot-classification",
                    model=self.model_id,
                    revision=self.model_revision,
                    device=-1,
                    trust_remote_code=False,
                    model_kwargs={"use_safetensors": True},
                )
            except Exception as error:
                raise ModelInferenceError(
                    f"could not load model {self.model_id}"
                ) from error
        return self._pipeline

    def classify(self, text: str) -> ClassificationResult:
        started_at = perf_counter()
        try:
            with self._lock:
                classifier = self._load_pipeline()
                output = classifier(
                    text,
                    candidate_labels=[
                        prompt for _, prompt in self.label_prompts
                    ],
                    multi_label=False,
                    hypothesis_template="This is a {}.",
                )
            winning_prompt = str(output["labels"][0])
            labels_by_prompt = {
                prompt: label for label, prompt in self.label_prompts
            }
            label = labels_by_prompt[winning_prompt]
            score = float(output["scores"][0])
        except ModelInferenceError:
            raise
        except Exception as error:
            raise ModelInferenceError("model inference failed") from error

        latency_ms = (perf_counter() - started_at) * 1_000
        logger.info(
            "incident classified",
            extra={
                "label": label,
                "score": score,
                "latency_ms": latency_ms,
                "model_id": self.model_id,
                "model_revision": self.model_revision,
            },
        )
        return ClassificationResult(
            label=label,
            score=score,
            model_id=self.model_id,
            model_revision=self.model_revision,
            latency_ms=latency_ms,
        )
