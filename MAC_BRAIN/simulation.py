"""Discrete-event simulation of the closed-loop runtime (simpy skill).

Models the MacBrain closed loop (perception -> cognition -> attention ->
situation -> reasoning -> governance -> skill -> verify -> reflection -> soul
-> social) as a SimPy process-based discrete-event model. Each sensory event is
an entity that contends for a single processing resource per stage (the runtime
is single-threaded); we measure completed-cycle throughput and latency under a
bounded horizon and entity cap.

This is a *model*, not the runtime: it estimates cycle timing under load for
closed-loop parity analysis (gap-analysis Step 6). It does not execute the real
brain, and simulation association is never a causal claim.

Methodology (simpy skill): purpose + estimands stated; conceptual model is a
single-threaded FIFO pipeline with exponential service per stage and Poisson
arrivals; execution is bounded by ``horizon`` and ``entity_cap``; arrival and
service use separate RNG streams derived from a master seed; monitoring records
completion time and latency per entity; deterministic edge cases and
conservation are tested; replications are run independently.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import simpy

# The closed-loop stages in execution order (mirrors runtime.py's loop).
STAGES: tuple[str, ...] = (
    "perception",
    "cognition",
    "attention",
    "situation",
    "reasoning",
    "governance",
    "skill",
    "verify",
    "reflection",
    "soul",
    "social",
)


@dataclass
class ClosedLoopSimulation:
    """Bounded discrete-event model of the closed-loop runtime.

    Parameters
    ----------
    horizon: simulation time units to run (half-open; events scheduled at
        exactly ``horizon`` are not processed).
    entity_cap: maximum number of sensory events to admit.
    mean_arrival: mean inter-arrival time (exponential).
    mean_service: mean service time per stage (exponential; ``<= 0`` means
        zero service time).
    seed: master seed; arrival and service streams are derived from it.
    """

    horizon: float = 480.0
    entity_cap: int = 10_000
    mean_arrival: float = 4.0
    mean_service: float = 1.0
    seed: int = 101

    def run(self) -> dict[str, float | int]:
        """Run one replication and return a summary of completed cycles."""
        arrival_rng = random.Random(self.seed)
        service_rng = random.Random(self.seed + 1)
        env = simpy.Environment()
        # One capacity-1 resource per stage (single-threaded runtime).
        resources = {stage: simpy.Resource(env, capacity=1) for stage in STAGES}
        completed: list[tuple[float, float]] = []  # (completion_time, latency)
        admitted = 0

        def cycle(_entity_id: int, arrival: float) -> None:
            for stage in STAGES:
                with resources[stage].request() as request:
                    yield request
                    if self.mean_service > 0:
                        yield env.timeout(service_rng.expovariate(1.0 / self.mean_service))
            completed.append((env.now, env.now - arrival))

        def arrivals() -> None:
            nonlocal admitted
            for _ in range(self.entity_cap):
                delay = arrival_rng.expovariate(1.0 / self.mean_arrival)
                if env.now + delay >= self.horizon:
                    return
                yield env.timeout(delay)
                admitted += 1
                env.process(cycle(admitted, env.now))

        env.process(arrivals())
        env.run(until=self.horizon)

        latencies = [lat for _, lat in completed]
        n = len(completed)
        return {
            "admitted": admitted,
            "completed": n,
            "unfinished": admitted - n,
            "mean_latency": (sum(latencies) / n) if n else 0.0,
            "max_latency": max(latencies) if n else 0.0,
            "throughput_per_time": (n / self.horizon) if self.horizon else 0.0,
        }


def replicate(
    *,
    replications: int = 5,
    horizon: float = 480.0,
    entity_cap: int = 10_000,
    mean_arrival: float = 4.0,
    mean_service: float = 1.0,
    base_seed: int = 101,
) -> dict[str, float | int]:
    """Run ``replications`` independent runs and return replication-level means.

    Intervals are computed from replication-level estimates, not from
    correlated entities within one run. Refuses a single replication (no
    meaningful spread).
    """
    if replications < 2:
        raise ValueError("replications must be >= 2 to form a replication-level estimate")
    summaries = [
        ClosedLoopSimulation(
            horizon=horizon,
            entity_cap=entity_cap,
            mean_arrival=mean_arrival,
            mean_service=mean_service,
            seed=base_seed + i,
        ).run()
        for i in range(replications)
    ]
    keys = ("admitted", "completed", "unfinished", "mean_latency", "max_latency", "throughput_per_time")
    out: dict[str, float | int] = {"replications": replications}
    for key in keys:
        values = [float(s[key]) for s in summaries]
        mean = sum(values) / len(values)
        out[f"mean_{key}"] = mean
    return out
