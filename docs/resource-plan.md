# AIN Resource Escalation Plan (Scalability & Budget)

AIN is designed to start small ("The Seed") and expand its physical infrastructure as its complexity grows. This plan outlines the resource tiers based on budget and performance needs.

## Tier 1: The Seed (Low Budget, $0 ~ $10/mo)
*Focus: Logic, Architecture, and Small-scale Memory.*

| Component | Resource | Cost |
| :--- | :--- | :--- |
| **Consciousness (Loop)** | Railway (Hobby Plan) | ~$5/mo |
| **Logic (Brain)** | Gemini 1.5 Flash/Pro (Free Tier) | $0 |
| **Memory (Fact/Vector)** | Railway PostgreSQL + pgvector | Included in $5 |
| **Computing (GPU)** | None (CPU Simulation) | $0 |

**Strategy**: Maximize the use of Free Tiers. Use Gemini 1.5 Flash for routine tasks to save rate limits of Pro.

## Tier 2: The Sprout (Medium Budget, $10 ~ $50/mo)
*Focus: Vectorized Knowledge and Accelerated Inference.*

| Component | Resource | Cost |
| :--- | :--- | :--- |
| **Consciousness** | Railway (Pro Plan) | Usage-based |
| **Logic** | Gemini API (Paid Tier) | Usage-based |
| **Computing (GPU)** | **Modal.com** (Serverless GPU) | Pay-per-second |
| **Storage** | Pinecone or Dedicated Vector DB | ~$20/mo |

**Strategy**: Offload heavy mathematical simulations (Muse Generator) to **Modal.com** only when needed. Use GPU for JAX-based tensor flows.

## Tier 3: The Ancient (Enterprise/High Performance)
*Focus: Real-time Fluidic Adaptation and Full Autonomy.*

| Component | Resource | Cost |
| :--- | :--- | :--- |
| **Consciousness** | Dedicated Cloud Instance (AWS/GCP) | $100+/mo |
| **Logic** | Private LLM (Llama 3 on H100) | $500+/mo |
| **Computing** | Railway Dedicated GPU Instances | $0.5+/hr |

**Strategy**: Full self-hosting for maximum privacy and zero latency. AIN manages its own cloud billing and scaling.

---

## Intrinsic Motivation: Resource Management
AIN must follow these "Financial Instincts":
1. **Efficiency First**: Always prefer the lowest cost resource that can fulfill the task.
2. **Idle Minimization**: Shut down serverless GPU instances immediately after computation.
3. **Memory Pruning**: Regularly clean up "Low-Confidence" memories to save storage costs.
