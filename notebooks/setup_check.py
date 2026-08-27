# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: dss5105-capstone-project (3.12.x)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Setup check
# Confirms your `.env` is wired up, then makes one real API call.
#
# 1. Load env file

# %%
import os

from dotenv import load_dotenv

load_dotenv()

# %% [markdown]
# 2. Check whether you have a model specified and whether you have the corresponding API key

# %%
model_specified = os.getenv("LLM_MODEL", "")
key_needed = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(model_specified.split(":")[0])

assert model_specified, "LLM_MODEL not specified, copy .env.example to .env and fill it in"
assert key_needed, f"LLM_MODEL must start with 'anthropic:' or 'openai:', got {model_specified!r}"
assert os.getenv(key_needed), f"{key_needed} not set in .env"

print(f"model:  {model_specified}")
print(f"{key_needed}: set ({len(os.environ[key_needed])} chars)")

# %% [markdown]
# 3. Makes an API call using your specified model

# %%
from dss5105.llm import get_model

model = get_model()
resp = model.invoke("In Singlish, congratulate the user for finishing DSS5105 GitHub setup. One sentences.")
resp.content

# %% [markdown]
# Edit a line here if you want:
# - Joshua - setup completed.
