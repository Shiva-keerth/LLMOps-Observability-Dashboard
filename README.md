# LLMOps Observability Dashboard

A production-grade, real-time observability dashboard for monitoring autonomous LLM agents and evaluation pipelines. Built with Streamlit, this tool tracks token consumption, inference latency, model fallback rates, and deterministic pre-filter rejection funnels.

## Features
- **Cost Estimation**: Calculates real-time cost metrics based on token consumption (Llama-3 70B via Groq).
- **Funnel Analytics**: Visualizes the exact drop-off points of data passing through regex pre-filters vs. LLM reasoning blocks.
- **Model Fallback Tracking**: Monitors multi-model fallback chains (e.g., GPT OSS -> Qwen 2.5) to surface reliability metrics.
- **Total Failure Alarms**: Logs total chain exhaustion events to ensure zero silent failures in production.
- **Data Privacy**: Anonymizes real company data (mapping to "Company A", "Company B") for secure public demonstration.

## Run Locally
```bash
pip install streamlit pandas
streamlit run app.py
```
