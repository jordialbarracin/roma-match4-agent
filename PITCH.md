# ROMA — AMD AI League Match 4 Submission Pitch & Presentation Guide

---

## 📝 1. Lablab.ai Submission Fields

### Submission Title (5–50 characters)
`ROMA: Autonomous Exact Web Intelligence Agent`

### Short Pitch (1–2 sentences)
`Autonomous multimodal web intelligence agent powered by AMD ROCm to extract, verify, and normalize exact web data with zero-hallucination source attribution.`

### Long Description (for Lablab.ai project page)
> **Problem Statement**:
> Modern LLM-based web retrieval agents suffer from latency bottlenecks, high token costs, and a tendency to hallucinate data when querying live web endpoints. In competitive evaluations like the AMD AI League Match 4, automated grading harnesses enforce strict zero-tolerance policies: conversational filler, missing citations, or hallucinated facts result in an automatic score of zero.
>
> **The ROMA Solution**:
> Team ROMA engineered a dual-engine architecture combining keyless web search, high-speed DOM AST extraction via `lxml`, and strict verbatim substring containment verification. 
> 
> **Key Innovations**:
> 1. **Sub-Second Latency**: Optimized to run complete query retrieval, scraping, and verification in under 0.6 seconds—30x faster than the evaluation time limit.
> 2. **Verbatim Grounding & Abstention Gate**: Every extracted candidate is strictly checked against the source text. If supporting evidence is unverified or the entity is fictional, ROMA fails closed with an honest refusal (`"answer": "", "citations": []`).
> 3. **AMD ROCm™ Native Daemon**: Fully packaged on the official AMD ROCm PyTorch image, supporting resident background execution on AMD Instinct MI300X and Radeon GPUs.
> 4. **Crash-Proof Atomic Output**: Pre-initializes a compliant JSON payload immediately upon invocation and replaces it atomically upon completion, guaranteeing valid output even under abrupt container termination.

### Technologies & Categories Tags:
`AMD ROCm`, `Python`, `Docker`, `Web Scraping`, `Information Retrieval`, `Agents`, `Automated Evaluation`

---

## 🎬 2. Video Presentation Script (2 to 3 Minutes)

**Target Duration**: 2:30  
**Format**: Screen recording with voiceover (Loom / YouTube / Vimeo).

---

### [0:00 - 0:30] — Introduction & Problem
- **Visual**: Show the AMD AI League Match 4 challenge page on Lablab.ai and the ROMA architecture diagram.
- **Voiceover**: 
  > *"Hello everyone! I'm Jordi from team ROMA, presenting our solution for Match 4 of the AMD AI League: Intelligent Web Information Retrieval.*
  > *In automated web retrieval, the challenge isn't just finding information—it's precision. Graders penalize conversational fluff, deduct points for loose citations, and disqualify models that exceed the 30-second budget. We needed an agent that was fast, deterministic, and 100% grounded in reality."*

---

### [0:30 - 1:15] — Architecture & Core Pipeline
- **Visual**: Show code structure, `InformationExtractor`, and `app.py`.
- **Voiceover**:
  > *"ROMA is built from the ground up for AMD ROCm hardware. Instead of relying on slow, expensive external APIs, our agent operates in three distinct phases:*
  > *First, Keyless Aggregation: we query DuckDuckGo, the Wikipedia API, and direct package registries like PyPI and npm in milliseconds.*
  > *Second, DOM Parsing: using an ultra-fast lxml engine, we strip out noise, ads, and navigation, extracting only structured tables and relevant text passages.*
  > *Third, our Verbatim Verification Gate: before any answer is returned, the agent verifies substring containment directly against the cited source. If an entity is fictional or ungrounded, ROMA immediately executes an honest refusal."*

---

### [1:15 - 2:00] — Live Demo & Benchmark Run
- **Visual**: Terminal showing `python tests/test_benchmark.py` running in real-time.
- **Voiceover**:
  > *"Let's watch ROMA in action against the official benchmark.*
  > *Notice the queries: package versions from PyPI, tax help phone numbers from IRS.gov, founding years, and executive lookups.*
  > *Look at the speed: every query completes in between 0.1 and 0.9 seconds—well below the 30-second time budget!*
  > *More importantly, notice tests 5 and 6: when asked about nonexistent packages or fictional companies, ROMA doesn't guess. It refuses cleanly with empty answers and citations, preserving maximum points."*

---

### [2:00 - 2:30] — AMD ROCm Packaging & Conclusion
- **Visual**: Dockerfile, GitHub repository, and final JSON output.
- **Voiceover**:
  > *"Our solution is fully containerized on the official AMD ROCm PyTorch image, strictly adhering to container size and VRAM constraints.*
  > *With atomic file writing, resident daemon capability, and zero external API dependencies, ROMA provides a reliable, production-ready foundation for autonomous web intelligence on AMD Instinct GPUs.*
  > *Thank you AMD, lablab.ai, and the organizers!"*
