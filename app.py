import json
import streamlit as st
import pandas as pd
from agent import load_components, investigate, evaluate_examples

st.set_page_config(page_title="Component Substitution Agent", page_icon="🔌", layout="wide")
st.title("🔌 Component Substitution Compatibility Agent")
st.caption("Evidence-grounded agentic AI prototype · synthetic educational dataset · not engineering approval")

components = load_components()
by_id = {c["part_number"]: c for c in components}
left, right = st.columns(2)
with left:
    original_id = st.selectbox("Unavailable / original component", [c["part_number"] for c in components], index=0)
with right:
    options = [c["part_number"] for c in components if c["part_number"] != original_id]
    candidate_id = st.selectbox("Proposed substitute", options, index=0)

st.info("Demo tip: choose RES-A-1000 → RES-B-1000 for a pass, RES-C-1000 for a failure, or RES-D-1000 for missing evidence.")
feedback = st.text_input("Optional reviewer feedback", placeholder="Example: Please verify whether the maximum voltage is documented")
if st.button("Investigate substitution", type="primary"):
    result = investigate(original_id, candidate_id, feedback)
    st.session_state["last_result"] = result

result = st.session_state.get("last_result")
if result:
    st.divider()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Agent verdict")
        if result["verdict"] == "POTENTIALLY COMPATIBLE":
            st.success(result["verdict"])
        elif result["verdict"] == "NOT COMPATIBLE":
            st.error(result["verdict"])
        else:
            st.warning(result["verdict"])
        st.write(result["summary"])
    with col2:
        st.subheader("Specification checks (Python tool output)")
        if result["checks"]:
            st.dataframe(pd.DataFrame(result["checks"]), use_container_width=True, hide_index=True)

    st.subheader("Retrieved evidence (RAG)")
    for rule in result["rules"]:
        st.markdown(f"- {rule}")

    st.subheader("Run trace / observability")
    st.caption("Each row records an actual step from this run, including retrieval, tool use, retry and final decision.")
    st.dataframe(pd.DataFrame(result["trace"]), use_container_width=True, hide_index=True)
    st.download_button("Download this run's trace (JSON)", json.dumps(result["trace"], indent=2), file_name="agent_trace.json", mime="application/json")

st.divider()
st.header("Evaluation on the golden test set")
if st.button("Run evaluation"):
    rows, accuracy = evaluate_examples()
    st.session_state["eval_rows"] = rows
    st.session_state["eval_accuracy"] = accuracy
if "eval_rows" in st.session_state:
    st.metric("Exact verdict accuracy", f"{st.session_state['eval_accuracy']:.0%}")
    st.dataframe(pd.DataFrame(st.session_state["eval_rows"]), use_container_width=True, hide_index=True)

with st.expander("Dataset and safety notes"):
    st.write("All component records and datasheets in this project are synthetic. Rules are simplified and do not cover all real-world engineering constraints such as lifecycle status, manufacturer qualifications, PCB footprint variants, ESR, ripple current, derating, or circuit-specific behaviour.")
    st.write("A verdict of POTENTIALLY COMPATIBLE means only that the implemented checks passed. Human engineering approval is required before any real substitution.")
