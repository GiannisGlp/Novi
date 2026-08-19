# Mac Neural Model Dependencies

The first real neural provider is `TorchvisionSSDLiteDetector`.

From the Novi root on Apple Silicon:

```bash
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install torch torchvision pillow
```

Verify:

```bash
./.venv/bin/python -c "import torch; print('PyTorch:', torch.__version__); print('MPS:', torch.backends.mps.is_available())"
```

The first model load downloads the pretrained SSDLite320 MobileNetV3 weights from the torchvision model source. Keep the resulting model cache local; do not commit model weights to Git.
