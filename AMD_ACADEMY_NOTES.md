# AMD AI Academy — Comprehensive Course Notes & Technical Reference

**Team**: ROMA (Jordi Albarracin i Puig)  
**Profile Rank**: BUILDER (900 Points)  
**Track**: AMD AI League & ROCm™ Certified Associate Pathway

---

## Course 1: AI Agents 101 — Building AI Agents With MCP and Open-Source Inference
- **Exam Score**: 100% (10,000 / 10,000 pts)
- **Status**: Completed

### Core Architecture & Takeaways:
1. **The ReAct Loop (Reasoning + Acting)**:
   - Base LLMs lack access to real-time or private information.
   - An AI Agent operates in an iterative loop:
     - **Thought (Reasoning)**: Decomposes the user query into sub-goals.
     - **Action (Tool Invocation)**: Calls external tools with structured JSON arguments.
     - **Observation**: Parses the tool's output back into the context window.
2. **Model Context Protocol (MCP)**:
   - An open-standard client-server specification (developed by Anthropic, adopted across open-source).
   - Eliminates bespoke, fragmented API connectors. Tools, prompt templates, and data resources are exposed over standardized JSON-RPC schemas via `stdio` or Server-Sent Events (`SSE`).
3. **Open-Source Inference Sovereignty**:
   - Running open models (e.g., Qwen 2.5, Llama 3) on AMD Instinct GPUs (MI300X, MI250) via **vLLM** and **SGLang**.
   - Removes vendor lock-in, proprietary API price per token, and enterprise data privacy risks.
4. **Structured Output Governance**:
   - Using validation libraries (e.g., **PydanticAI**) to enforce deterministic typing on model outputs, essential for zero-error web extraction.

---

## Course 2: AI on AMD — GenAI Lifecycle & Hardware Hierarchy
- **Exam Score**: 100% (10,000 / 10,000 pts)
- **Status**: Completed

### Core Architecture & Takeaways:
1. **GenAI Three-Stage Lifecycle**:
   - **Pre-Training**: Massive scale representation learning on trillions of tokens.
   - **Post-Training / Alignment**: Supervised Fine-Tuning (SFT), RLHF/DPO, and Parameter-Efficient Fine-Tuning (LoRA / QLoRA) for domain specialization.
   - **Inference & Serving**: Low-latency execution under concurrent user traffic.
2. **AMD AI Compute Spectrum**:
   - **Ryzen AI**: Dedicated XDNA Neural Processing Units (NPUs) delivering energy-efficient on-device edge inference in mobile/laptop workstations.
   - **Radeon RX / AI PRO**: RDNA architecture GPUs suited for local workstation inference, prototyping, and PEFT fine-tuning.
   - **AMD Instinct (MI300X / MI250X)**: CDNA 3 architecture datacenter compute featuring up to **192GB HBM3** memory and **5.3 TB/s** memory bandwidth, built for massive multi-billion parameter models and large batch concurrency.
3. **Conversational System Design**:
   - Role separation (`system`, `user`, `assistant`), message history serialization for multi-turn context, and temperature tuning to control deterministic vs. creative output generation.

---

## Course 3: LLM Serving Inference with vLLM and MI300X GPUs
- **Exam Score**: 87.5% (Passed & Verified)
- **Status**: Completed

### Core Architecture & Takeaways:
1. **AMD Instinct MI300X Specifications**:
   - Target architecture identifier: `gfx942`.
   - Massive 192GB HBM3 memory allows loading 70B+ models in full precision or serving extreme context lengths without offloading.
2. **ROCm Acceleration Flags**:
   - `VLLM_ROCM_USE_AITER=1`: Activates AMD's optimized AI Tensor Engine (AITER) kernels for custom matrix math.
   - `VLLM_USE_AITER_UNIFIED_ATTENTION=1`: Hardware-accelerated unified attention implementation for ROCm.
3. **Latency Mitigation**:
   - **ROCm / CUDA Graph Capture (`full_cuda_graph`)**: Eliminates CPU-to-GPU kernel dispatch overhead by pre-compiling static execution graphs.
   - Tensor parallelism (`--tensor-parallel`) splits model layers across multiple MI300X GPUs over ultra-fast Infinity Fabric interconnects.
4. **Key Serving Metrics**:
   - **TTFT (Time To First Token)**: Latency from query arrival to first decoded token (dominated by prefill phase).
   - **TPOT (Time Per Output Token)**: Average time per subsequent token (dominated by memory bandwidth decode phase).
   - **ITL (Inter-Token Latency)**: Smoothness of output streaming.
   - **E2EL (End-to-End Latency)**: Total time from request submission to completion.

---

## Course 4: Introduction to Quantization
- **Exam Score**: 100% (10,000 / 10,000 pts)
- **Status**: Completed

### Core Architecture & Takeaways:
1. **The Quantization Advantage**:
   - Drastically compresses memory footprint (e.g. 4x reduction from FP32 280GB to INT8 70GB on a 70B model).
   - Converts memory-bandwidth bound decode operations into high-throughput tensor operations.
2. **Mathematical Formulation (Uniform Affine Quantization)**:
   $$q = \text{clamp}\left(\text{round}\left(\frac{r}{s}\right) + z\right)$$
   Where:
   - $r$ is the continuous real value (e.g., in FP32/FP16).
   - $s = \frac{\text{range}(r)}{\text{range}(q)}$ is the scaling factor.
   - $z = \text{round}\left(-\frac{r_{\min}}{s}\right) + q_{\min}$ is the zero-point integer offset.
   - **Dequantization**:
     $$\hat{r} = s \cdot (q - z)$$
3. **Quantization Granularities**:
   - **Weight-Only**: Quantizes static model weights (e.g., AWQ, GPTQ); activations remain FP16. Ideal for memory savings with minimal accuracy loss.
   - **Weight-Activation (W8A8 / W4A4)**: Quantizes both weights and activations; requires calibration across activation distributions.
4. **PTQ vs. QAT**:
   - **PTQ (Post-Training Quantization)**: Fast conversion of trained weights using a representative calibration dataset.
   - **QAT (Quantization-Aware Training)**: Inserts fake quantization operators during training to allow weights to adapt to rounding errors, preserving superior accuracy.

---

## Course 5: AI Agents 201 — Design to Deployment: Multi-Agent Systems
- **Exam Score**: 100% (10,000 / 10,000 pts)
- **Status**: Completed

### Core Architecture & Takeaways:
1. **CrewAI Structural Blueprint**:
   - Execution pipeline: `Agent` (Role, Goal, Backstory) $\rightarrow$ `Task` (Description, Expected Output, Tools) $\rightarrow$ `Crew` (Process: Sequential or Hierarchical) $\rightarrow$ `Output`.
2. **Agent-to-Agent (A2A) Protocol**:
   - An open-standard protocol for autonomous inter-agent coordination.
   - Relies on **Agent Cards**: Standardized JSON manifests advertising:
     - Agent Identity & Endpoint URL.
     - Supported Input & Output JSON Schemas.
     - Available Skills, Capabilities, and SLA guarantees.
3. **The Concierge Routing Pattern**:
   - A frontline orchestrator (Concierge Agent) parses incoming requests, consults registered AgentCards, and uses dynamic dispatch (`send_task`) to delegate specialized sub-tasks to downstream worker agents.
4. **Sovereign Agent Development Kit (ADK)**:
   - Decouples agent architectures from proprietary SaaS providers.
   - By pointing the Agent Development Kit to self-hosted vLLM/Ollama endpoints running on AMD Instinct GPUs, organizations retain 100% data sovereignty, zero token egress fees, and sub-millisecond local inter-process latency.
