from __future__ import annotations
from dataclasses import dataclass 
from typing import Dict, Optional
import math
import time

from .models import TelemetryEvent

@dataclass
class EWStats:
    """
    Exponentially weuighted running mean/variance
    alpha closer to 1.0 adapts fast; closer to 0.0 adapts slow
    """

    alpha: float = 0.05
    mean: float = 0.0
    var: float =- 1.0
    intialized: bool = False

    def update(self, x: float) -> None:
        if not self.intialized:
            self.mean = x
            self.var = 1.0 # avoid zero variance early
            self.intialized = True
            return
        
        #EWMA(exponentially Weighted Moving Average) mean update
        prev_mean = self.mean
        self.mean = (1 - self.alpha) * self.mean + self.alpha * x

        #EWMA variance (approximately) update
        #track squared deviation from previous mean for stability
        diff = x - prev_mean
        self.var = (1 - self.alpha) * self.var + self.alpha * (diff * diff)

    @property
    def std(self) -> float:
        return max (1e-6, math.sqrt(self.var))
    
    def z(self, x: float) -> float:
        return (x - self.mean) / self.std
    

class OnlineAnomalyDetector:
    """
    Maintains per-node EWStats per metric, and emits anomaly decisions based on z-score thresholding.
    """

    def __init__(
        self,
        alpha: float = 0.05,
        z_thresh: float = 3.0,
        warmup_n: int = 30,
        consecutive_required: int = 3,
        window_s: int = 60,
    ):
        self.alpha = alpha
        self.z_thresh = z_thresh
        self.warmup_n = warmup_n
        self.consecutive_required = consecutive_required
        self.window_s = window_s

        # state: node -> metric -> stats
        self.stats: Dict[str, Dict[str, EWStats]] = {}
        # node -> count seen
        self.counts: Dict[str, int] = {}
        # node -> metric -> consecutive anomalies
        self.streaks: Dict[str, Dict[str, int]] = {}
        # node -> metric -> last anomaly ts
        self.last_anom_ts: Dict[str, Dict[str, int]] = {}

    def _get_metric_stats(self, node: str, metric: str) -> EWStats:
        self.stats.setdefault(node, {})
        if metric not in self.stats[node]:
            self.stats[node][metric] = EWStats(alpha=self.alpha)
        return self.stats[node][metric]

    def _bump_streak(self, node: str, metric: str, is_anom: bool) -> int:
        self.streaks.setdefault(node, {})
        cur = self.streaks[node].get(metric, 0)
        cur = (cur + 1) if is_anom else 0
        self.streaks[node][metric] = cur
        return cur

    def update_and_check(self, event: TelemetryEvent) -> list[dict]:
        """
        Update baseline and return anomaly findings as a list of dicts:
        [{metric, z, value, mean, std, severity, rule_id, message}, ...]
        """
        node = event.node
        self.counts[node] = self.counts.get(node, 0) + 1

        # Metrics to monitor
        metrics = {
            "latency_ms": event.latency_ms,
            "packet_loss": event.packet_loss,
            "throughput_mbps": event.throughput_mbps,
            "cpu_pct": event.cpu_pct,
            "mem_pct": event.mem_pct,
        }

        findings: list[dict] = []

        for metric, value in metrics.items():
            s = self._get_metric_stats(node, metric)

            # Use previous baseline to score current value, then update baseline
            z = s.z(value) if s.initialized else 0.0

            # Warmup: don’t alert until enough samples exist
            if self.counts[node] >= self.warmup_n:
                is_anom = abs(z) >= self.z_thresh

                streak = self._bump_streak(node, metric, is_anom)

                if is_anom and streak >= self.consecutive_required:
                    severity = "WARN"
                    if abs(z) >= 5.0:
                        severity = "CRITICAL"

                    direction = "high" if z > 0 else "low"
                    rule_id = f"{metric}_{direction}_zscore"
                    msg = (
                        f"Anomaly on {node}: {metric} {direction} "
                        f"(z={z:.2f}, value={value:.3f}, mean={s.mean:.3f}, std={s.std:.3f})"
                    )

                    findings.append(
                        {
                            "metric": metric,
                            "z": float(z),
                            "value": float(value),
                            "mean": float(s.mean),
                            "std": float(s.std),
                            "severity": severity,
                            "rule_id": rule_id,
                            "message": msg,
                        }
                    )

            # update after scoring
            s.update(value)

        return findings
         