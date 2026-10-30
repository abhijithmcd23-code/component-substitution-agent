# Component Substitution Compatibility Agent

A small local prototype for the Agentic AI mini-project. It investigates whether a candidate electronic component may substitute for an unavailable component using a visible plan, local RAG, Python comparison tools, bounded evidence retry, traces, and a small golden evaluation set.

## Important
- All component data and datasheet labels are synthetic educational examples.
- This is not a production engineering tool and must not be used to approve real component substitutions.
- The prototype implements simplified checks only.

## Requirements
- macOS
- Python 3.10 or newer
- VS Code

## Run on Mac
1. Install Python 3.10+ from https://www.python.org/downloads/macos/ if needed.
2. Open this folder in VS Code.
3. In VS Code, choose Terminal > New Terminal.
4. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Start the app:

   ```bash
   streamlit run app.py
   ```

7. A browser tab should open at the local Streamlit address (usually http://localhost:8501). If not, Command-click or copy that URL into your browser.

## Demo script
1. Select `RES-A-1000` as original and `RES-B-1000` as candidate. Explain the plan, retrieved rules, Python checks, trace, and potentially compatible verdict.
2. Select `RES-C-1000`. Explain that the lower power rating and looser tolerance fail checks.
3. Select `RES-D-1000`. Explain the missing maximum-voltage value, the bounded retry, and the inconclusive verdict rather than guessing.
4. Enter feedback such as `Please verify whether the maximum voltage is documented` and run again. Show the feedback trace.
5. Click **Run evaluation** and explain the fixed golden set and exact verdict accuracy.

## Repository contents
- `app.py`: Streamlit UI
- `agent.py`: planner, local retrieval, Python comparison tool, bounded retry, verdict policy, evaluation
- `data/components.json`: synthetic component records
- `knowledge_base/*.md`: synthetic engineering rules for retrieval
- `requirements.txt`: dependencies

## Concepts demonstrated
- Tool/function use: Python comparison function
- Agentic RAG: the agent retrieves rules from local knowledge documents
- Planning: explicit plan logged in each run
- Adaptation: one bounded retry when evidence is missing
- Observability: step-by-step JSON trace visible in UI and downloadable
- Evaluation: small fixed golden set with exact verdict accuracy
- Human-in-the-loop: reviewer feedback is logged; it cannot override failed checks

## Suggested team split
- Member 1: agent orchestration and planning
- Member 2: component dataset and knowledge base
- Member 3: Streamlit interface and demo
- Member 4 (if applicable): evaluation, test cases, README/report
Everyone should understand the whole system before the viva.
