"""Optional LocateAnything runtime boundary (plan Step 3.2/3.3, Phase 4, §19 step 7).

This module is the ONLY place where heavy dependencies (torch, transformers)
may be imported — and they are imported strictly inside functions, never at
module scope. `import novi.perception.locate_anything_runtime` is always safe.

Responsibilities:
- capability probing: map the real environment to the seven BackendStates
  (plan Step 0.3): available | loading | unavailable | unsupported |
  dependency_missing | model_missing | failed;
- load lifecycle with an injectable loader (tests use fake bundles; the
  default loader builds the real transformers bundle for the Mac experiment);
- `infer(image, prompt, mode) -> (raw_text, latency_ms)` — raw model output
  only; parsing/provenance stay in the Novi adapter (locate_anything.py).

The loader contract is duck-typed: any object with
`generate(image, prompt, mode) -> (raw_text, latency_ms)` works, so tests
never touch a real model and the boundary is trivially faked for CI.
"""

from __future__ import annotations

import importlib.util
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    BackendState,
    SpatialBackendCapabilities,
    SpatialInferenceMode,
)

MODEL_ID = "nvidia/LocateAnything-3B"
MODEL_REVISION = "c32291ca5e996f5a7a485845b4f57a233936bba0"
MAX_NEW_TOKENS = 8192  # NVIDIA model card recommendation


@dataclass(frozen=True)
class ProbeEnvironment:
    """Snapshot of the runtime environment used for capability decisions."""

    torch: object | None
    transformers: object | None
    model_dir_present: bool
    model_revision: str
    device: str | None
    mem_gb: float | None = None
    detail_notes: tuple[str, ...] = ()


def _total_memory_gb() -> float | None:
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
        return pages * size / (1024**3)
    except (AttributeError, OSError, ValueError):
        return None


def _snapshot(cache_dir: str | None = None) -> ProbeEnvironment:
    """Inspect the real environment without importing anything heavy eagerly."""
    notes: list[str] = []
    torch_mod = None
    if importlib.util.find_spec("torch"):
        try:
            torch_mod = importlib.import_module("torch")
        except Exception as exc:  # broken install degrades to a note, never a crash
            notes.append(f"torch import failed: {exc}")
    transformers_mod = None
    if importlib.util.find_spec("transformers"):
        try:
            transformers_mod = importlib.import_module("transformers")
        except Exception as exc:
            notes.append(f"transformers import failed: {exc}")

    device: str | None = None
    if torch_mod is not None:
        try:
            if torch_mod.cuda.is_available():
                device = "cuda"
            elif getattr(torch_mod.backends, "mps", None) is not None and torch_mod.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        except Exception as exc:  # broken torch must degrade, not crash Novi
            notes.append(f"device probe failed: {exc}")

    hf_home = (
        cache_dir
        or os.environ.get("HF_HOME")
        or str(Path.home() / ".cache" / "huggingface")
    )
    snapshot_dir = (
        Path(hf_home) / "hub" / "models--nvidia--LocateAnything-3B" / "snapshots" / MODEL_REVISION
    )
    return ProbeEnvironment(
        torch=torch_mod,
        transformers=transformers_mod,
        model_dir_present=snapshot_dir.is_dir(),
        model_revision=MODEL_REVISION,
        device=device,
        mem_gb=_total_memory_gb(),
        detail_notes=tuple(notes),
    )


def probe_capabilities(
    env: ProbeEnvironment | None = None, *, cache_dir: str | None = None
) -> SpatialBackendCapabilities:
    """Map an environment snapshot to the seven-state capability report."""
    if env is None:
        env = _snapshot(cache_dir=cache_dir)

    details: list[tuple[str, str]] = [
        ("model_id", MODEL_ID),
        ("model_revision", env.model_revision),
    ]
    details.extend(("note", note) for note in env.detail_notes)

    def report(state: BackendState, device: str | None = None, **extra: tuple[tuple[str, str], ...]) -> SpatialBackendCapabilities:
        return SpatialBackendCapabilities(
            state=state,
            model_id=MODEL_ID,
            model_revision=env.model_revision,
            device=device,
            modes=(SpatialInferenceMode.FAST, SpatialInferenceMode.SLOW, SpatialInferenceMode.HYBRID),
            details=tuple(details) + extra.get("details", ()),
        )

    if env.torch is None:
        return report(BackendState.DEPENDENCY_MISSING, details=(("missing", "torch"),))
    try:
        getattr(env.torch, "version", "?")
    except Exception as exc:
        return report(BackendState.FAILED, details=(("error", str(exc)),))
    if env.transformers is None:
        return report(BackendState.DEPENDENCY_MISSING, details=(("missing", "transformers"),))
    if not env.model_dir_present:
        return report(BackendState.MODEL_MISSING, device=env.device)
    if env.device is None:
        return report(BackendState.UNAVAILABLE)
    return report(BackendState.AVAILABLE, device=env.device)


class LocateAnythingRuntime:
    """Load lifecycle + inference orchestration; model specifics stay in the bundle.

    The loader (injected in tests, default = real transformers bundle) must
    return an object with `generate(image, prompt, mode) -> (raw, latency_ms)`.
    """

    def __init__(
        self,
        *,
        loader: Callable[[], object] | None = None,
        env_builder: Callable[[], ProbeEnvironment] | None = None,
        cache_dir: str | None = None,
    ) -> None:
        self._loader = loader
        self._env_builder = env_builder
        self._cache_dir = cache_dir
        self._bundle: object | None = None

    def probe(self) -> SpatialBackendCapabilities:
        env = self._env_builder() if self._env_builder is not None else _snapshot(cache_dir=self._cache_dir)
        return probe_capabilities(env)

    def load(self) -> None:
        """Load the model bundle, or raise a capability-tagged RuntimeError.

        Raising is intentional: the Novi adapter catches it and produces a
        fail-closed GroundingResult — a missing LocateAnything never crashes
        normal Novi startup.
        """
        caps = self.probe()
        if not caps.usable:
            raise RuntimeError(f"locate_anything runtime not loadable: {caps.state.value}")
        if self._bundle is not None:
            return
        try:
            if self._loader is not None:
                loader = self._loader
            else:
                cache_dir = self._cache_dir
                loader = lambda: _default_loader(cache_dir)  # noqa: E731
            self._bundle = loader()
        except RuntimeError as exc:
            if "model_missing" in str(exc):
                raise RuntimeError(f"model_missing: {exc}") from exc
            raise RuntimeError(f"failed: {exc}") from exc

    def unload(self) -> None:
        self._bundle = None

    def infer(self, image: CameraFrame, prompt: str, mode: SpatialInferenceMode) -> tuple[str, float]:
        """Run one grounding generation. Raises capability-tagged errors."""
        self.load()
        assert self._bundle is not None
        return self._bundle.generate(image, prompt, mode)  # type: ignore[no-any-return]


class _RealLocateAnythingBundle:
    """The real transformers bundle (used only after the Mac experiment approves it).

    Construction imports transformers inside the method — never at module
    scope. The inference call follows the upstream `LocateAnythingWorker`
    reference (NVlabs/Eagle @ 783f656d) exactly: chat-template messages with
    an image part, `py_apply_chat_template`, `process_vision_info`, and the
    remote `model.generate(..., generation_mode=...)` signature. This shape
    is validated by the Phase 4 Mac feasibility experiment.
    """

    def __init__(
        self,
        *,
        cache_dir: str | None = None,
        device: str | None = None,
        dtype: object | None = None,
    ) -> None:
        import torch  # noqa: PLC0415 — heavy import, isolated here
        import transformers  # noqa: PLC0415 — heavy import, isolated here

        self._torch = torch
        hf_kwargs = dict(cache_dir=cache_dir, revision=MODEL_REVISION, trust_remote_code=True)
        self._tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_ID, **hf_kwargs)
        self._processor = transformers.AutoProcessor.from_pretrained(MODEL_ID, **hf_kwargs)
        self._dtype = dtype if dtype is not None else torch.bfloat16
        self._device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        started = time.perf_counter()
        self._model = (
            transformers.AutoModel.from_pretrained(MODEL_ID, torch_dtype=self._dtype, **hf_kwargs)
            .to(self._device)
            .eval()
        )
        self._load_seconds = time.perf_counter() - started

    def generate(self, image: CameraFrame, prompt: str, mode: SpatialInferenceMode) -> tuple[str, float]:
        import gc
        import io

        from PIL import Image  # noqa: PLC0415

        pil_image = Image.open(io.BytesIO(image.payload)).convert("RGB")
        messages = [
            {
                "role": "system",
                "content": "Answer using grounding tokens only.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        text = self._processor.py_apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        images, videos = self._processor.process_vision_info(messages)
        inputs = self._processor(text=[text], images=images, videos=videos, return_tensors="pt").to(self._device)
        pixel_values = inputs["pixel_values"].to(self._dtype)
        started = time.perf_counter()
        with self._torch.no_grad():
            response = self._model.generate(
                pixel_values=pixel_values,
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                image_grid_hws=inputs.get("image_grid_hws", None),
                tokenizer=self._tokenizer,
                max_new_tokens=MAX_NEW_TOKENS,
                use_cache=True,
                generation_mode=mode.value,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                top_k=None,
                repetition_penalty=1.1,
                verbose=False,
            )
        raw = response[0] if isinstance(response, tuple) else response
        # The remote generate already returns the decoded answer text
        # (upstream worker: `{"answer": response[0] if isinstance(response, tuple) else response}`)
        # — do NOT decode again. Strip chat-template framing tokens: they are
        # generation scaffolding, not model output content, and the strict
        # parser must not see them.
        text_out = str(raw).replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
        latency_ms = (time.perf_counter() - started) * 1000.0
        # MPS experiment mitigation: the MPS caching allocator retains freed
        # blocks, and macOS jetsam SIGKILLs the process once RSS balloons
        # (observed after ~4 generations). Release cache + collect so long
        # experiment batteries stay alive.
        if self._device == "mps":
            self._torch.mps.empty_cache()
        gc.collect()
        return text_out, latency_ms


def _default_loader(cache_dir: str | None = None) -> object:
    return _RealLocateAnythingBundle(cache_dir=cache_dir)
