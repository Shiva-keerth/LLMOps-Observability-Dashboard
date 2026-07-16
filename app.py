import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="LLMOps Dashboard | Jobline Pipeline", layout="wide")

# Determine which DB to use. We prefer demo_telemetry for safety, but fallback if needed.
# Since this is deployed publicly, we will explicitly point it to demo_telemetry.db
db_path = os.path.join(os.path.dirname(__file__), "demo_telemetry.db")

@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(db_path):
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM evaluator_telemetry", conn)
    conn.close()
    return df

st.title("📊 LLMOps Observability Dashboard")
st.markdown("Real-time telemetry and funnel analytics for the autonomous **Jobline Pipeline** LLM Evaluator.")

df = load_data()

if df.empty:
    st.warning("No telemetry data found. Run the pipeline and export the demo DB first.")
    st.stop()

# --- KPIs ---
total_jobs = len(df)
llm_evals = df[df["eval_type"] == "LLM"]
errors = df[df["eval_type"] == "ERROR"]

total_tokens = llm_evals["prompt_tokens"].sum() + llm_evals["completion_tokens"].sum()
avg_latency = llm_evals["latency_ms"].mean() if not llm_evals.empty else 0
fallback_rate = (llm_evals["is_fallback"].sum() / len(llm_evals) * 100) if not llm_evals.empty else 0
error_rate = (len(errors) / total_jobs * 100) if total_jobs > 0 else 0

# Groq Llama-3 70B pricing is approx $0.70 per 1M tokens
estimated_cost = (total_tokens / 1_000_000) * 0.70

st.subheader("Performance KPIs")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Jobs Evaluated", f"{total_jobs}")
c2.metric("API Latency (avg)", f"{avg_latency/1000:.2f}s" if avg_latency else "0s")
c3.metric("Tokens Consumed", f"{total_tokens:,}")
c4.metric("Fallback Rate", f"{fallback_rate:.1f}%")
c5.metric("Est. Cost (Paid Tier)", f"${estimated_cost:.4f}")

if error_rate > 0:
    st.error(f"⚠️ Model Error Rate: {error_rate:.1f}%")

st.divider()

# --- Funnel Analytics ---
st.subheader("Evaluation Funnel")

blacklisted = len(df[df["eval_type"] == "BLACKLIST"])
pre_filtered = len(df[df["eval_type"] == "PRE_FILTER"])
llm_rejected = len(llm_evals[llm_evals["verdict"].isin(["DISQUALIFIED", "Poor Fit", "Partial Fit", "UNKNOWN"])])
llm_accepted = len(llm_evals[llm_evals["verdict"].isin(["Good Fit", "Strong Match"])])

col1, col2 = st.columns([1, 1])

with col1:
    funnel_data = {
        "Stage": ["1. Scraped", "2. Passed Blacklist", "3. Passed Pre-filter", "4. LLM Accepted"],
        "Count": [
            total_jobs, 
            total_jobs - blacklisted, 
            total_jobs - blacklisted - pre_filtered, 
            llm_accepted
        ]
    }
    st.bar_chart(pd.DataFrame(funnel_data).set_index("Stage"))

with col2:
    st.markdown("**Drop-off Analysis**")
    st.markdown(f"- **{blacklisted}** jobs killed by recruiter Blacklist / Aggregator Signals.")
    st.markdown(f"- **{pre_filtered}** jobs killed by strict Experience Regex (Saved LLM tokens!).")
    st.markdown(f"- **{llm_rejected}** jobs rejected by LLM reasoning (Poor Fit).")
    st.markdown(f"- **{llm_accepted}** jobs survived the gauntlet (High Match).")

st.divider()

# --- Rejection Diagnostics ---
st.subheader("Diagnostics: Why are jobs failing?")

col3, col4 = st.columns(2)

with col3:
    st.markdown("**Top Regex Disqualifications (Experience Gate)**")
    regex_fails = df[df["eval_type"] == "PRE_FILTER"]
    if not regex_fails.empty:
        # Extract the exact string matched
        top_reasons = regex_fails["reason"].value_counts().reset_index()
        top_reasons.columns = ["Matched String", "Count"]
        st.dataframe(top_reasons, hide_index=True)
    else:
        st.info("No regex failures logged yet.")

with col4:
    st.markdown("**Model Fallback & Error Logs**")
    fallback_df = df[(df["is_fallback"] == True) | (df["eval_type"] == "ERROR")][["company", "eval_type", "model_used", "reason"]]
    if not fallback_df.empty:
        st.dataframe(fallback_df, hide_index=True)
    else:
        st.success("100% Primary Model Uptime. No fallbacks or errors.")

st.divider()

st.subheader("Raw Telemetry Feed (Anonymized)")
st.dataframe(df.sort_values(by="timestamp", ascending=False).head(50), hide_index=True)
