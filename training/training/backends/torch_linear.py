"""Tiny linear ranker backend — retrieval/policy/grounding scorers (plan §34-35).

A small, interpretable, independently trainable scorer (torch is present on
this host; no peft needed). Features are the same handcrafted signals the
deterministic brain already computes (novi/brain/retrieval_policy.py weights,
dialogue-policy state features, grounding cues), so the learned scorer is a
drop-in reranker behind deterministic guardrails — never direct control.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class LinearRanker(nn.Module):
    def __init__(self, n_features: int) -> None:
        super().__init__()
        self.linear = nn.Linear(n_features, 1, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


def train_linear_ranker(
    features: list[list[float]],
    labels: list[float],
    *,
    epochs: int = 10,
    lr: float = 1e-2,
    seed: int = 20260830,
) -> tuple[dict[str, float], list[float]]:
    """Deterministic linear ranker over feature rows -> labels in [0,1].

    Returns (trained_weights_dict, final_predictions). The weights dict
    includes a `bias` entry alongside w_0..w_n; artifact writers store the
    bias separately so feature-order consumers stay clean. Guarded: empty
    input raises; NaN features raise.
    """
    if not features or len(features) != len(labels):
        raise ValueError("features and labels must be non-empty and aligned")
    n = len(features[0])
    torch.manual_seed(seed)
    model = LinearRanker(n)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    # BCE with logits is the right loss for binary relevance labels (MSE on
    # 0/1 converges to a worse optimum on imbalanced candidate sets).
    loss_fn = nn.BCEWithLogitsLoss()
    X = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.float32)
    if torch.isnan(X).any() or torch.isnan(y).any():
        raise ValueError("features/labels contain NaN")

    for _ in range(max(1, int(epochs))):
        opt.zero_grad()
        loss = loss_fn(model(X).squeeze(-1), y)
        loss.backward()
        opt.step()

    with torch.no_grad():
        preds = torch.sigmoid(model(X)).squeeze(-1).tolist()
    w = model.linear.weight.detach()[0]
    b = model.linear.bias.detach()[0]
    weights = {f"w_{i}": round(float(v), 4) for i, v in enumerate(w)}
    weights["bias"] = round(float(b), 4)
    return weights, [round(p, 4) for p in preds]
