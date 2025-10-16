#!/bin/bash
cd /Users/keithelliott/repos/SaasLiteLLM
export PYTHONPATH=/Users/keithelliott/repos/SaasLiteLLM
python3 -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003
