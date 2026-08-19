# B2 Neural Architecture — Source Register

This document records the primary sources used for the B2 model-selection decision on 2026-08-19. Product/version facts must be revalidated at implementation time.

## NVIDIA primary sources

1. **Nemotron model catalog** — current NVIDIA model-family catalog, including Nemotron 3 Nano Omni 30B-A3B and Nemotron 3 Super 120B-A12B.
   https://developer.nvidia.com/topics/ai/nemotron

2. **Nemotron 3 Nano Omni technical article** — multimodal video/audio/image/text architecture, 30B-A3B MoE, multimodal reasoning, local/deployment characteristics.
   https://developer.nvidia.com/blog/nvidia-nemotron-3-nano-omni-powers-multimodal-agent-reasoning-in-a-single-efficient-open-model

3. **Cosmos Reason2 documentation** — physical AI/robotics VLM, spatial-temporal reasoning, localization, long context and model capabilities.
   https://docs.nvidia.com/cosmos/latest/reason2/index.html

4. **Cosmos prerequisites** — current tested GPU architectures and memory requirements for Reason2-2B and Reason2-8B, including Jetson AGX Thor.
   https://docs.nvidia.com/cosmos/latest/prerequisites.html

5. **TensorRT Edge-LLM physical AI article** — edge support for Cosmos Reason2 and Nemotron-family inference on Jetson/DRIVE Thor.
   https://developer.nvidia.com/blog/build-next-gen-physical-ai-with-edge-first-llms-for-autonomous-vehicles-and-robotics/

6. **Isaac GR00T N1.7** — VLA architecture, training data scale, Cosmos Reason2-2B VLM backbone, ONNX/TensorRT export and 3B base checkpoint.
   https://developer.nvidia.com/blog/develop-humanoid-robot-policies-end-to-end-with-nvidia-isaac-gr00t/

7. **Jetson Thor** — current Thor/T2000/T3000 edge platform direction and Cosmos 3 Edge.
   https://blogs.nvidia.com/blog/jetson-thor-robotics-edge-ai-agent/

8. **Cosmos 3 Edge** — 4B edge physical-AI/world-action model direction for Jetson Thor.
   https://nvidianews.nvidia.com/news/japans-robotics-and-manufacturing-leaders-build-on-nvidia-cosmos-to-advance-physical-ai-frontier

## Novi Library research inputs

9. **NVIDIA_Novi_Comprehensive_Research.md** — broad NVIDIA physical-AI architecture research completed 2026-08-17.

10. **NVIDIA_Novi_Physical_AI_Research_2026.md** — physical-AI architecture, stable Novi capability interfaces, small-robot progression and anti-lock-in principles.

## Source-quality rule

NVIDIA primary documentation and technical material is preferred for NVIDIA product claims. Novi architectural decisions must remain capability-first and must not become dependent on a product name or release. Model version, artifact digest, runtime, hardware, quantization and benchmark configuration must be captured when an actual model artifact is admitted.
