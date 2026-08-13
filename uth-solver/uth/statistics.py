from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from statistics import NormalDist
from typing import Protocol


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

    def merge(self, other: "RunningStats") -> None:
        if not other.count:
            return
        if not self.count:
            self.count, self.mean, self.m2 = other.count, other.mean, other.m2
            return
        combined = self.count + other.count
        delta = other.mean - self.mean
        self.m2 += other.m2 + delta * delta * self.count * other.count / combined
        self.mean += delta * other.count / combined
        self.count = combined

    @property
    def variance(self) -> float:
        return self.m2 / (self.count - 1) if self.count > 1 else 0.0

    @property
    def standard_error(self) -> float:
        return sqrt(self.variance / self.count) if self.count else float("inf")

    def standard_error_for_population(self, population: int | None = None) -> float:
        error = self.standard_error
        if population is None or self.count >= population or population <= 1:
            return 0.0 if population is not None and self.count >= population else error
        return error * sqrt((population - self.count) / (population - 1))

    def interval(self, confidence: float = 0.999, population: int | None = None) -> tuple[float, float]:
        z = NormalDist().inv_cdf((1 + confidence) / 2)
        half = z * self.standard_error_for_population(population)
        return self.mean - half, self.mean + half

    def to_dict(self, confidence: float = 0.999, population: int | None = None) -> dict[str, object]:
        low, high = self.interval(confidence, population)
        return {"count": self.count, "mean": self.mean, "variance": self.variance,
                "standard_error": self.standard_error_for_population(population), "confidence": confidence,
                "confidence_interval": [low, high], "half_width": (high - low) / 2,
                **({"population": population, "finite_population_correction": True} if population is not None else {})}


@dataclass(slots=True)
class StratifiedStats:
    """A proportionally weighted estimator for sampling strata without replacement."""

    groups: list[tuple[int, RunningStats]]

    @property
    def count(self) -> int:
        return sum(stats.count for _, stats in self.groups)

    @property
    def population(self) -> int:
        return sum(size for size, _ in self.groups)

    @property
    def mean(self) -> float:
        return sum(size / self.population * stats.mean for size, stats in self.groups)

    @property
    def standard_error(self) -> float:
        variance = 0.0
        for size, stats in self.groups:
            if stats.count >= size:
                continue
            if stats.count < 2:
                return float("inf")
            weight = size / self.population
            correction = (size - stats.count) / (size - 1)
            variance += weight * weight * stats.variance / stats.count * correction
        return sqrt(variance)

    def interval(self, confidence: float = 0.999) -> tuple[float, float]:
        half = NormalDist().inv_cdf((1 + confidence) / 2) * self.standard_error
        return self.mean - half, self.mean + half

    def to_dict(self, confidence: float = 0.999) -> dict[str, object]:
        low, high = self.interval(confidence)
        return {"count": self.count, "population": self.population, "mean": self.mean,
                "standard_error": self.standard_error, "confidence": confidence,
                "confidence_interval": [low, high], "half_width": (high - low) / 2,
                "finite_population_correction": True,
                "strata": [{"population": size, "sample_count": stats.count,
                            "sample_mean": stats.mean, "sample_variance": stats.variance}
                           for size, stats in self.groups]}


class DifferenceStats(Protocol):
    count: int
    mean: float

    def interval(self, confidence: float = 0.999) -> tuple[float, float]: ...


def recommendation_status(delta: DifferenceStats, precision: float = 0.001, confidence: float = 0.999) -> str:
    low, high = delta.interval(confidence)
    if delta.count < 2 or not isfinite(low) or not isfinite(high) or (high - low) / 2 > precision or low <= 0 <= high:
        return "INCONCLUSIVE — MORE COMPUTATION REQUIRED"
    return "CONFIRMED"
