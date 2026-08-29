"""Learned-policy adapter seam + Exp-4 simulation benchmark harness.

NVIDIA research §24 Exp 4 ("Isaac Lab transfer") Mac-feasible half: run the
same skill through simulation and measure success rate, robustness under
randomization, and failure classes. The seam (``LearnedPolicy`` /
``PolicySkillAdapter``) is where an Isaac-trained or GR00T policy plugs in
behind the same ``SkillContract`` the deterministic/mock skills use — the
contract is implementation-independent (research §4 boundary).

Backends:
- ``DeterministicPolicyBackend`` — the existing mock behavior as a policy
  (moves toward the target). Fully Mac-runnable, used for the benchmark.
- ``IsaacPolicyBackend`` — placeholder that fails loudly on the Mac
  (no GPU/Isaac); proves the seam is gated and testable at the boundary.

The benchmark runs bounded episodes over a randomized simulated world
(``SimBody``/``SimWorld``) and reports:
- success rate;
- robustness under randomization (per-config success rates);
- failure classes (timeout_exceeded / obstacle_blocking / localization_lost /
  object_lost).

Simulation association is never a causal claim (research §18/19): every
benchmark result is tagged SIMULATED.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from novi.brain.memory_hardening import SIMULATED
from novi.brain.skill_contract import SkillContract
from novi.brain.virtual_skills import SimBody, SimWorld

# Evidence class for every benchmark result: simulated episodes never silently
# become facts (research §18). Imported from the shared vocabulary
# (memory_hardening) to avoid drift.

# Failure classes (aligned with skill_contract failure criteria vocabulary).
TIMEOUT_EXCEEDED = "timeout_exceeded"
OBSTACLE_BLOCKING = "obstacle_blocking"
LOCALIZATION_LOST = "localization_lost"
OBJECT_LOST = "object_lost"


# ---------------------------------------------------------------------------
# Policy seam
# ---------------------------------------------------------------------------


class LearnedPolicy(Protocol):
    """A learned policy: observation -> action. Implementation-agnostic."""

    name: str
    policy_version: str

    def predict(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Return the action for one observation."""
        ...


@dataclass(frozen=True)
class PolicyExecution:
    """Outcome of one policy-driven skill attempt."""

    status: str  # SUCCESS / FAILURE / TIMEOUT / RUNNING (open-loop only)
    action: dict[str, Any]
    failure_class: str | None
    iterations: int
    error: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "action": dict(self.action),
            "failure_class": self.failure_class,
            "iterations": self.iterations,
            "error": self.error,
        }


class DeterministicPolicyBackend:
    """Deterministic mock policy: move toward the target pose.

    ``prediction_noise_std`` injects Gaussian noise into the chosen action to
    exercise the robustness measurement (Exp 4: robustness under randomization).
    """

    name = "deterministic_policy"
    policy_version = "0.1.0"

    def __init__(self, *, prediction_noise_std: float = 0.0, move_distance: float = 0.5) -> None:
        import random

        self._rng = random.Random(2026)
        self.prediction_noise_std = prediction_noise_std
        self.move_distance = move_distance

    def predict(self, observation: dict[str, Any]) -> dict[str, Any]:
        tx, ty = observation["target"]
        x, y = observation["pose_x"], observation["pose_y"]
        distance = math.hypot(tx - x, ty - y)
        if distance <= 0.5:
            return {"action": "arrive", "target": [tx, ty]}
        step = self.move_distance
        if self.prediction_noise_std > 0:
            step = max(0.0, step + self._rng.gauss(0.0, self.prediction_noise_std))
        dx, dy = (tx - x) / distance, (ty - y) / distance
        return {"action": "move", "dx": dx * step, "dy": dy * step}


class IsaacPolicyBackend:
    """Placeholder for an Isaac-trained policy.

    On the Mac (no Isaac Lab/GPU) any invocation fails loudly with a clear
    error, proving the seam is gated. The hardware phase injects a real
    policy function behind the same interface.
    """

    name = "isaac_lab_policy"
    policy_version = "deferred"

    def __init__(self, policy_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        self._policy_fn = policy_fn

    def predict(self, observation: dict[str, Any]) -> dict[str, Any]:
        if self._policy_fn is None:
            raise RuntimeError(
                "IsaacPolicyBackend requires an Isaac-trained policy, which is "
                "only available in the Jetson/GPU phase (research §24 Exp 4). "
                "The Mac seam is testable with DeterministicPolicyBackend."
            )
        return self._policy_fn(observation)


class PolicySkillAdapter:
    """Bridges a ``SkillContract`` to a ``LearnedPolicy``.

    The policy produces raw actions; the adapter applies the skill contract's
    success/failure criteria and iteration budget (timeout), so cognition
    decides *whether/when/why* a skill runs and the policy only executes it
    (research §2 / §4 boundary).
    """

    def __init__(self, policy: LearnedPolicy, contract: SkillContract, *, max_iterations: int = 100) -> None:
        self.policy = policy
        self.contract = contract
        self.max_iterations = max_iterations

    def invoke(
        self,
        observation: dict[str, Any],
        *,
        body: SimBody | None = None,
        world: SimWorld | None = None,
    ) -> PolicyExecution:
        """Run the policy against the observation until success/failure/budget.

        ``body``/``world`` are optional simulators that the deterministic
        backend mutates to close the loop; they must be provided together.
        When both are absent, the policy is evaluated open-loop against the
        observation only (single iteration, status ``RUNNING``).
        """
        if (body is None) != (world is None):
            raise ValueError("body and world must be provided together (or both omitted)")
        iterations = 0
        obs = dict(observation)
        while iterations < self.max_iterations:
            iterations += 1
            try:
                action = self.policy.predict(obs)
            except RuntimeError as exc:  # gated backend (e.g. Isaac placeholder)
                return PolicyExecution(
                    status="FAILURE", action={}, failure_class=None, iterations=iterations, error=str(exc)
                )

            if action.get("action") == "arrive":
                return PolicyExecution(status="SUCCESS", action=action, failure_class=None, iterations=iterations)

            if body is not None and world is not None:
                if self._would_block(body, world, action):
                    return PolicyExecution(
                        status="FAILURE", action=action, failure_class=OBSTACLE_BLOCKING, iterations=iterations
                    )
                self._apply(body, world, action)
                if not body.localized:
                    return PolicyExecution(
                        status="FAILURE", action=action, failure_class=LOCALIZATION_LOST, iterations=iterations
                    )
                obs = self._observation(body, obs)
            else:
                return PolicyExecution(status="RUNNING", action=action, failure_class=None, iterations=iterations)
        return PolicyExecution(
            status="TIMEOUT",
            action={},
            failure_class=TIMEOUT_EXCEEDED,
            iterations=iterations,
            error=f"budget:{self.max_iterations}",
        )

    # -- simulation application helpers --------------------------------------

    @staticmethod
    def _observation(body: SimBody, obs: dict[str, Any]) -> dict[str, Any]:
        obs["pose_x"], obs["pose_y"] = body.x_m, body.y_m
        obs["heading_deg"] = body.heading_deg
        return obs

    @staticmethod
    def _apply(body: SimBody, world: SimWorld, action: dict[str, Any]) -> None:
        if action.get("action") != "move":
            return
        nx = body.x_m + float(action.get("dx", 0.0))
        ny = body.y_m + float(action.get("dy", 0.0))
        body.x_m, body.y_m = nx, ny

    @staticmethod
    def _would_block(body: SimBody, world: SimWorld, action: dict[str, Any]) -> bool:
        """True when this move action would enter a forbidden region."""
        if action.get("action") != "move":
            return False
        nx = body.x_m + float(action.get("dx", 0.0))
        ny = body.y_m + float(action.get("dy", 0.0))
        return world.route_blocked(body.x_m, body.y_m, nx, ny)


# ---------------------------------------------------------------------------
# Exp-4 benchmark harness
# ---------------------------------------------------------------------------


@dataclass
class RandomizationConfig:
    """One randomization setting for Exp-4 robustness measurement."""

    name: str
    start_jitter_m: float = 0.0
    target_jitter_m: float = 0.0
    obstacle: tuple[float, float, float, float] | None = None  # AABB (x1,y1,x2,y2)
    prediction_noise_std: float = 0.0


@dataclass
class BenchmarkRun:
    """Result of one randomized episode."""

    episode_index: int
    randomization: str
    status: str
    failure_class: str | None
    iterations: int
    success: bool

    def snapshot(self) -> dict[str, Any]:
        return {
            "episode_index": self.episode_index,
            "randomization": self.randomization,
            "status": self.status,
            "failure_class": self.failure_class,
            "iterations": self.iterations,
            "success": self.success,
        }


@dataclass
class BenchmarkResult:
    """Aggregate Exp-4 result: success rate, robustness, failure classes."""

    skill_id: str
    evidence_class: str = SIMULATED
    runs: list[BenchmarkRun] = field(default_factory=list)
    config_metrics: dict[str, dict[str, float]] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if not self.runs:
            return 0.0
        return sum(1 for r in self.runs if r.success) / len(self.runs)

    @property
    def robustness(self) -> float:
        """Robustness = mean per-config success rate.

        A policy that succeeds at the same rate across every randomization
        config has robustness equal to that rate; configs that diverge pull
        the mean down. Variance is reported per config via ``config_metrics``.
        """
        rates = [m["success_rate"] for m in self.config_metrics.values()]
        if not rates:
            return 0.0
        return sum(rates) / len(rates)

    def failure_classes(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for run in self.runs:
            if run.failure_class is not None:
                out[run.failure_class] = out.get(run.failure_class, 0) + 1
        return out

    def snapshot(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "evidence_class": self.evidence_class,
            "episode_count": len(self.runs),
            "success_rate": round(self.success_rate, 4),
            "robustness": round(self.robustness, 4),
            "failure_classes": self.failure_classes(),
            "per_config": self.config_metrics,
            "runs": [r.snapshot() for r in self.runs],
        }


def run_policy_benchmark(
    *,
    skill_id: str = "navigate",
    configs: list[RandomizationConfig] | None = None,
    episodes_per_config: int = 5,
    max_iterations: int = 100,
    seed: int = 2026,
) -> BenchmarkResult:
    """Exp 4 harness: run the skill through simulation under randomization.

    Deterministic, bounded, fully Mac-runnable. Each episode starts a fresh
    ``SimBody``/``SimWorld`` from a start pose to a target pose; the policy
    closes the loop through the simulated body. All results are SIMULATED.
    """
    import random

    rng = random.Random(seed)
    if configs is None:
        configs = [
            RandomizationConfig(name="nominal"),
            RandomizationConfig(name="start_jitter", start_jitter_m=0.3),
            RandomizationConfig(name="target_jitter", target_jitter_m=0.3),
            RandomizationConfig(name="sensor_noise", prediction_noise_std=0.05),
            RandomizationConfig(name="obstacle", obstacle=(2.0, -1.5, 2.4, 1.5)),
        ]

    from novi.brain.skill_contract import NAVIGATE_SKILL

    result = BenchmarkResult(skill_id=skill_id)
    episode_index = 0

    for config in configs:
        config_runs: list[BenchmarkRun] = []
        for _ in range(episodes_per_config):
            start_x = rng.uniform(-0.5, 0.5) + config.start_jitter_m * rng.uniform(-1.0, 1.0)
            start_y = rng.uniform(-0.5, 0.5) + config.start_jitter_m * rng.uniform(-1.0, 1.0)
            target_x = 5.0 + config.target_jitter_m * rng.uniform(-1.0, 1.0)
            target_y = 1.0 + config.target_jitter_m * rng.uniform(-1.0, 1.0)

            world = SimWorld(
                object_locations={},
                forbidden_regions=[config.obstacle] if config.obstacle else [],
            )
            body = SimBody(x_m=start_x, y_m=start_y, heading_deg=0.0, localized=True)
            policy = DeterministicPolicyBackend(prediction_noise_std=config.prediction_noise_std)
            adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL, max_iterations=max_iterations)

            execution = adapter.invoke(
                {"pose_x": start_x, "pose_y": start_y, "heading_deg": 0.0, "target": (target_x, target_y)},
                body=body,
                world=world,
            )
            success = execution.status == "SUCCESS" and math.hypot(body.x_m - target_x, body.y_m - target_y) <= 0.75
            run = BenchmarkRun(
                episode_index=episode_index,
                randomization=config.name,
                status=execution.status,
                failure_class=execution.failure_class,
                iterations=execution.iterations,
                success=success,
            )
            result.runs.append(run)
            config_runs.append(run)
            episode_index += 1

        successes = sum(1 for r in config_runs if r.success)
        result.config_metrics[config.name] = {
            "success_rate": round(successes / len(config_runs), 4) if config_runs else 0.0,
            "episodes": len(config_runs),
        }

    return result
