# MAGENTA: A Framework for LLM-Driven Multi-Agent Autoformalizaton
## Overview
MAGENTA provides support for designing and implementing the components that are typically involved in establishing a multi-agent autoformalization system. The components involved in the system include **Agent**, **Large Language Model (LLM)**, **Knowledge Base (KB)**, **Retriever** and **Theorem Prover (TP)**. We illustrate our system in the figure below.
![framework](/multi_agent.png)

### Preliminary Requirements
**Python Packages**: 

torch, transformers, openai, rank_bm25

**Theorem Prover**: 

[Isabelle](https://isabelle.in.tum.de/) (Note: The official Isabelle website has upgraded to a 2025 version. A 2024 version which was used in the development of this system is provided [here](https://drive.google.com/file/d/1c0dW3zLd0eUU5PC0sEorZ6V1Gec410W-/view?usp=drive_link))

The path variable "ISABELLE_DIRPATH" needs to be set for using Isabelle in our system. You can either preset the path variable, or add the following python codes to your scripts before the main content.
```
import os
os.environ['ISABELLE_DIRPATH'] = os.path.abspath('directory-of-isabelle')
```

## Implementations 
### Agent

| Type                   | Class                                                         |
|:-----------------------|:--------------------------------------------------------------|
| Autoformalization      | [AutoformalizationAgent](/agent/autoformalization.py)         |
| Critique               | [HardCritiqueAgent](/agent/hard_critique.py)                  |
|                        | [SoftCritiqueAgent](/agent/soft_critique.py)                  |
| Refinement             | [FormalRefinementAgent](/agent/formal_refinement.py)          |
|                        | [InformalRefinementAgent](/agent/informal_refinement.py)      |
| Tool                   | [ImportRetrievalAgent](/agent/import_retrieval.py)            |
|                        | [DenoisingAgent](/agent/denoising.py)                         |

### Large Language Model (LLM)

| Class                                                |
|:-----------------------------------------------------|
| [OpenAILLM](/llm/openai_llm.py)                      |
| [HuggingFaceLLM](/llm/huggingface_llm.py)            |

### Knowledge Base (KB)

| Class                                                            |
|:-----------------------------------------------------------------|
| [IsabelleHOLKnowledgeBase](/knowledge_base/isabelle_hol.py)      |

### Retriever

| Class                                                            |
|:-----------------------------------------------------------------|
| [BM25Retriever](/retriever/BM25.py)                              |

### Theorem Prover (TP)
| Class                                                            |
|:-----------------------------------------------------------------|
| [Isabelle](/theorem_prover/isabelle.py)                              |

## Demonstration Examples
We use [multi_agent.ipynb](/multi_agent.ipynb) to illustrate how to build two multi-agent pipelines, namely self-improving and iterative refinement, for obtaining formalizations for a batch of informal statements. A demonstration video associated with this notebook is also provided [here](https://drive.google.com/file/d/1Ieqbg3QVg-j5sR22Y_tOZBuuyw9IHmH-/view?usp=drive_link).

We also have an example of how to use agents for formalizing the definition of [Softmax Function](https://en.wikipedia.org/wiki/Softmax_function#Definition) in [example_paper.ipynb](/example_paper.ipynb).

## System Evaluation
To show the flexiability of our design and evaluating the effectiveness of our systems, we build and test the following multi-agent pipelines: 

1. [self-improving](/evaluation_experiments/self_improving.py)
2. [iterative hard-critique-formal-refinement](/evaluation_experiments/iterative.py)
3. [autoformalization + denoising](/evaluation_experiments/denoising.py)

All results can be found under the directory [evaluation_experiments](/evaluation_experiments).
