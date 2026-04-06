# rd-agent-mcp

Research Agent MCP Server with LangGraph/LangChain/LangSmith orchestration.

## Features

- **Intelligent Agent Routing**: Automatically selects between rd-agent and adk-ralph based on task type
- **Local LLM Support**: Uses LM Studio for local inference
- **ChromaDB Embeddings**: Persistent vector storage for research documents
- **SQLite Database**: Stores agent results and experiment configurations
- **LangGraph Orchestration**: Sequential phases with parallel agent execution
- **Cloud Fallback**: Supports OpenAI, Anthropic, and Google APIs

## Installation

```bash
pip install rd-agent-mcp
```

## Configuration

Create a `config.json` file:

```json
{
  "chat_model": "ibm/granite-4-h-tiny",
  "embedding_model": "text-embedding-nomic-embed-text-v1.5",
  "base_url": "http://192.168.0.13:1234/v1",
  "chroma_path": "./chroma_data",
  "sqlite_path": "./research.db"
}
```

Or use environment variables:

```bash
export CHAT_MODEL=ibm/granite-4-h-tiny
export EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
export LM_STUDIO_BASE_URL=http://192.168.0.13:1234/v1
export RD_AGENT_PATH=./agents/rd-agent
export ADK_RALPH_PATH=./agents/adk-ralph
# Set to true only in trusted environments to spawn real agent subprocesses:
export RD_AGENT_MCP_EXEC_AGENTS=false
```

## Usage

### MCP Server

```bash
rd-agent-mcp serve
```

### CLI Commands

```bash
# Initialize in a directory
rd-agent-mcp init

# Run a specific phase
rd-agent-mcp run-phase questions
rd-agent-mcp run-phase experiment
rd-agent-mcp run-phase agent
rd-agent-mcp run-phase results

# Full LangGraph pipeline
rd-agent-mcp research-phase --topic "Your Topic" --homework-pdf ./homework-assignment.pdf

# Validate template test_cases YAML tree
rd-agent-mcp validate-tests --test-dir ./test_cases
python -m rd_agent_mcp.test_runner --test-dir ./test_cases --question q1
```

### MCP Tools

- `research_phase` - Run full research pipeline
- `extract_questions` - Extract questions from sources
- `design_experiments` - Design experiments for questions
- `create_embeddings` - Generate embeddings
- `search_embeddings` - Search embeddings by similarity
- `run_agent_pipeline` - Run rd-agent or adk-ralph
- `answer_question` - Answer research questions
- `generate_test_cases` - Generate test cases
- `compile_results` - Compile results

#### Per-section LaTeX critique (coursework / rd-ralph-template layout)

All of these take **`project_root`**: an absolute path to the repo that contains `output/results/latex-sections*.json`, coursework summaries, and critique artifacts.

- `latex_section_critique_list_sections` - List section JSON files and their keys; reports default critique/numeric paths if present.
- `latex_section_critique_index_ground_truth` - Chunk and embed `q1`/`q2`/`q3` JSON into a dedicated Chroma collection (default persist dir: `<project_root>/.chromadb_latex_critique`). Returns `chunks_written` / `chunks_skipped` (skips unchanged files unless `force_reindex` is true).
- `latex_section_critique_retrieve_ground_truth` - Per-source vector search over that index (no chat model); returns ranked chunks for prompt assembly.
- `latex_section_critique_get_bundle` - One section’s LaTeX fragment, optional critique + numeric-consistency slices, and ground truth. **`ground_truth_mode`**: `"truncate"` (default, same idea as `run_latex_sections_critique_lmstudio.py`) or `"rag"` (hybrid: **TOC** per file + retrieved chunks). For `"rag"`, run `index_ground_truth` first.
- `latex_section_critique_build_prompt` - Full user message for a single-section review; pass `task_text` **or** `agent_yaml_path` (relative to `project_root`) to supply the long critique instructions.
- `latex_section_critique_run_section_review` - Same inputs as `build_prompt`, then calls LM Studio chat and returns parsed JSON (`section_critique`).
- `latex_section_critique_merge_partial` - Merge one section dict into `sections_by_file`; optional `write_path` to save JSON under `project_root`.
- `latex_section_critique_run_cross_cutting` - Smaller LM call to refresh only `cross_cutting` using abstract/results/discussion/conclusion excerpts.

## Architecture

### Phases

1. **Questions** - Extract questions from homework PDF and papers
2. **Experiment** - Design experiments for questions
3. **Embeddings** - Generate ChromaDB embeddings
4. **Agent** - Run agents (parallel execution)
5. **Results** - Compile results to JSON and LaTeX

### Agent Routing

| Task Type | Primary Agent | Secondary Agent |
|-----------|---------------|-----------------|
| Data Analysis | rd-agent | adk-ralph |
| Literature Review | rd-agent | adk-ralph |
| Code Generation | adk-ralph | rd-agent |
| Experiment Design | Both | - |
| Results Compilation | rd-agent | adk-ralph |

## License

MIT
