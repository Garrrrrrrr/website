from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist


@dataclass(slots=True)
class RunningStats:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def add(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)

    @property
    def variance(self) -> float:
        return self.m2 / (self.count - 1) if self.count > 1 else 0.0

    @property
    def standard_error(self) -> float:
        return sqrt(self.variance / self.count) if self.count else float("inf")

    def interval(self, confidence: float = 0.999) -> tuple[float, float]:
        z = NormalDist().inv_cdf((1 + confidence) / 2)
        half = z * self.standard_error
        return self.mean - half, self.mean + half

    def to_dict(self, confidence: float = 0.999) -> dict[str, object]:
        low, high = self.interval(confidence)
        return {"count": self.count, "mean": self.mean, "variance": self.variance,
                "standard_error": self.standard_error, "confidence": confidence,
                "confidence_interval": [low, high], "half_width": (high - low) / 2}


def recommendation_status(delta: RunningStats, precision: float = 0.001, confidence: float = 0.999) -> str:
    low, high = delta.interval(confidence)
    if delta.count < 2 or (high - low) / 2 > precision or low <= 0 <= high:
        return "INCONCLUSIVE — MORE COMPUTATION REQUIRED"
    return "CONFIRMED"
