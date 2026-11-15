# %% [markdown]
# # Lab 1.1 · One model, three API shapes
#
# Day 1 · Session 1 · 25 min. Three request shapes carry almost every model call you will meet: **Chat
# Completions**, **Responses** and **Messages**. In this lab you send the same question about Marsa's berth hire
# to one free open-weight model through all three, and read what each returns: where the text is, why the model
# stopped, and what it cost.
#
# **Reference state.** Nothing to build on: a key in `labs/.env` (or Colab secrets) and the circulars in
# `data/circulars/`.
#
# **Tasks**
# - [ ] 1 · Chat Completions: one call, read every field (6')
# - [ ] 2 · Responses: the same question as items (5')
# - [ ] 3 · Messages: the same question as content blocks (5')
# - [ ] 4 · One table: text, stop reason, tokens per shape (5')
# - [ ] 5 · The Arabic token tax on one circular (4')
# - [ ] ✱ Stretch · Cut the answer short and read each shape's stop reason

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-302.git"
    if not Path("/content/agentic-ai").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/agentic-ai"], check=True)
    os.chdir("/content/agentic-ai/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("agentkit.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import agentkit as K
print("provider:", K.PROVIDER, "| model:", K.MODEL)

# %%
import pandas as pd

import port

TC07 = port.Port().get_circular("TC-07")["text"]
SYSTEM = "You answer shipping agents' questions for Marsa Ports Authority. Use only the circular given. Two sentences at most."
QUESTION = f"Circular:\n{TC07}\n\nQuestion: what is the berth hire for a 41,000 GT vessel for 2 days?"

# %% [markdown]
# ## 1 · Chat Completions (6')
#
# A list of messages with roles in; one `choices[0].message` out. `finish_reason` says why the model stopped
# (`stop`, `length`, `tool_calls`); `usage` counts tokens in and out.
#
# ✏️ **Exercise** · Call `K.client().chat.completions.create(...)` with `model=K.MODEL`, the system and user
# messages and `temperature=0`. Keep the response in `chat`.

# %%
# BEGIN SOLUTION
chat = K.client().chat.completions.create(
    model=K.MODEL, temperature=0,
    messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": QUESTION}])
# END SOLUTION
print(chat.model, "|", chat.choices[0].finish_reason, "|", chat.usage.prompt_tokens, "in,", chat.usage.completion_tokens, "out")
print(chat.choices[0].message.content)
K.check("8,200" in chat.choices[0].message.content.replace("8200", "8,200"), "Chat Completions: SAR 8,200")

# %% [markdown]
# ## 2 · Responses (5')
#
# `instructions` plus `input` in; a list of **output items** out (a `message` item, and on other turns
# `function_call` or `reasoning` items). `output_text` joins the text for you. Most gateways do not keep server
# state, so send `store=False` and replay the history yourself.
#
# ✏️ **Exercise** · Same question with `K.client().responses.create(...)`. Keep it in `resp`.

# %%
# BEGIN SOLUTION
resp = K.client().responses.create(model=K.MODEL, instructions=SYSTEM, input=QUESTION, temperature=0, store=False)
# END SOLUTION
print(resp.status, "|", [item.type for item in resp.output], "|", resp.usage.input_tokens, "in,", resp.usage.output_tokens, "out")
print(resp.output_text)

# %% [markdown]
# ## 3 · Messages (5')
#
# `system` as a separate field, `max_tokens` required; a list of **content blocks** out (`text`, `tool_use`,
# `thinking`) with a `stop_reason` (`end_turn`, `max_tokens`, `tool_use`). OpenRouter serves this shape at its
# Anthropic-compatible endpoint, so the same open-weight model answers.
#
# ✏️ **Exercise** · Same question with `K.anthropic_client().messages.create(...)` and `max_tokens=300`. Keep it
# in `msg`.

# %%
# BEGIN SOLUTION
msg = K.anthropic_client().messages.create(model=K.MODEL, max_tokens=300, temperature=0, system=SYSTEM,
                                           messages=[{"role": "user", "content": QUESTION}])
# END SOLUTION
print(msg.stop_reason, "|", [b.type for b in msg.content], "|", msg.usage.input_tokens, "in,", msg.usage.output_tokens, "out")
print("".join(b.text for b in msg.content if b.type == "text"))

# %% [markdown]
# ## 4 · One table (5')
#
# ✏️ **Exercise** · Fill `rows` with one dict per shape: `shape`, `text` (first 70 characters), `stop` (the
# shape's own stop field), `input_tokens`, `output_tokens`. Same model, same words: do the input tokens agree?

# %%
# BEGIN SOLUTION
rows = [
    {"shape": "chat", "text": chat.choices[0].message.content[:70], "stop": chat.choices[0].finish_reason,
     "input_tokens": chat.usage.prompt_tokens, "output_tokens": chat.usage.completion_tokens},
    {"shape": "responses", "text": resp.output_text[:70], "stop": resp.status,
     "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens},
    {"shape": "messages", "text": "".join(b.text for b in msg.content if b.type == "text")[:70], "stop": msg.stop_reason,
     "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens},
]
# END SOLUTION
table = pd.DataFrame(rows)
print(table.to_string(index=False))
K.check(len(table) == 3, "three shapes in one table")

# %% [markdown]
# 🔍 The input tokens differ by a few: each shape wraps the same words in a different template before the model's
# tokenizer sees them. The answer should not differ: the model is the same.

# %% [markdown]
# ## 5 · The Arabic token tax (4')
#
# Every circular has an English half and an Arabic half. In TC-03 (berth fit) the two say the same three rules.
# `K.count_tokens` uses an open tokenizer (a few megabytes, no model weights).
#
# ✏️ **Exercise** · Split TC-03 at the Arabic heading (`"\n## "`), count the tokens of each half and compute
# `ratio` = Arabic tokens / English tokens.

# %%
# BEGIN SOLUTION
TC03 = port.Port().get_circular("TC-03")["text"]
english, arabic = TC03.split("\n## ", 1)
ratio = K.count_tokens(arabic) / K.count_tokens(english)
# END SOLUTION
print(f"English {K.count_tokens(english)} tokens, Arabic {K.count_tokens(arabic)} tokens, ratio {ratio:.2f}")
K.check(ratio > 0, "ratio computed")

# %% [markdown]
# 🔍 A ratio above 1 means the same rule costs more context, and more money, in Arabic. Keep this number: Day 2
# budgets the context window.

# %% [markdown]
# ## ✱ Stretch · Cut the answer short
#
# Send the question again to each shape with an output limit of 5 tokens (`max_tokens=5` for Chat and Messages,
# `max_output_tokens=16` for Responses, its smallest). Print each shape's stop field. Which one would your loop
# have to treat as "not finished"?

# %%
# BEGIN SOLUTION
short_chat = K.client().chat.completions.create(model=K.MODEL, max_tokens=5,
                                                messages=[{"role": "user", "content": QUESTION}])
short_resp = K.client().responses.create(model=K.MODEL, input=QUESTION, max_output_tokens=16, store=False)
short_msg = K.anthropic_client().messages.create(model=K.MODEL, max_tokens=5, messages=[{"role": "user", "content": QUESTION}])
print(short_chat.choices[0].finish_reason, short_resp.status, getattr(short_resp, "incomplete_details", None), short_msg.stop_reason)
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. In which field does each shape tell you that the model was cut off?
# 2. Why must a client of the Responses shape on a gateway replay the history itself?
# 3. Which number from this lab would you put in a budget for an Arabic-speaking agent?
