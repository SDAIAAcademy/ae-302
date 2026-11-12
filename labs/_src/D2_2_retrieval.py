# %% [markdown]
# # Lab 2.2 · Retrieval for agents
#
# Day 2 · Session 2 · 25 min. Bosla must find the right circular in English or Arabic, and must not quote the one
# that was superseded. In this lab you score retrieval on twelve questions, build a keyword search (BM25 with
# Arabic normalisation) and a vector search, hand both to the agent as tools, and read in the trace which it picks.
#
# **Reference state.** The eight circulars in `data/circulars/`, twelve questions with the correct circular in
# `data/tasks/retrieval_eval.jsonl`. Nothing from earlier labs. No model is downloaded: the vectors here are
# character n-grams computed on your laptop.
#
# **Tasks**
# - [ ] 1 · The eval and the baseline (4')
# - [ ] 2 · BM25 with Arabic normalisation (7')
# - [ ] 3 · Vector search with character n-grams (6')
# - [ ] 4 · Both as tools: which does the agent pick? (8')
# - [ ] ✱ Stretch · When the corpus fits, skip retrieval

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/agentic-ai.git"
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
import json
import math
import re
from collections import Counter

import numpy as np
import pandas as pd

import port

CHUNKS = port.chunk_circulars()
EVAL = [json.loads(line) for line in (K.DATA / "tasks" / "retrieval_eval.jsonl").read_text(encoding="utf-8").splitlines()]
print(len(CHUNKS), "chunks (English and Arabic halves separately) |", len(EVAL), "questions")

# %% [markdown]
# ## 1 · The eval and the baseline (4')
#
# Eight circulars is a small corpus: almost anything finds the right one in the top three. What matters to an
# agent is the **top** hit, because that is what it quotes.
#
# ✏️ **Exercise** · Write `hit_at_1(search)`: the share of questions whose first result has the gold circular ID.
# `search(query, k)` returns chunks with a `circular_id`. Score `port.keyword_search`.

# %%
def hit_at_1(search) -> float:
    # BEGIN SOLUTION
    return sum(search(e["q"], 1)[:1] != [] and search(e["q"], 1)[0]["circular_id"] == e["gold"] for e in EVAL) / len(EVAL)
    # END SOLUTION


print("keyword baseline hit@1:", round(hit_at_1(port.keyword_search), 2))
for e in EVAL[:2]:
    print(e["q"], "→", [c["circular_id"] for c in port.keyword_search(e["q"], 3)])

# %% [markdown]
# 🔍 The first question asks for berth hire "now", and the baseline ranks TC-02 first: the superseded circular.

# %% [markdown]
# ## 2 · BM25 with Arabic normalisation (7')
#
# BM25 weighs a word by how rare it is across chunks and dampens repeats. Arabic needs normalising first: one
# letter has several written forms (أ إ آ ا), and diacritics and the ta marbuta vary.
#
# ✏️ **Exercise** · Complete `normalise` (strip diacritics and tatweel, unify the alef forms to ا, ة to ه, ى to ي,
# lower-case) and `bm25_search` (k1 = 1.5, b = 0.75). Then demote superseded chunks: multiply their score by 0.5.

# %%
def normalise(text: str) -> str:
    # BEGIN SOLUTION
    text = re.sub(r"[ً-ْـ]", "", text)
    text = re.sub("[أإآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")
    return text.lower()
    # END SOLUTION


def tokens(text: str) -> list[str]:
    return [w[:6] for w in re.findall(r"\w+", normalise(text)) if len(w) > 1]


DOCS = [tokens(c["text"]) for c in CHUNKS]
DF = Counter(w for d in DOCS for w in set(d))
AVG = sum(map(len, DOCS)) / len(DOCS)


def bm25_search(query: str, k: int = 3) -> list[dict]:
    # BEGIN SOLUTION
    q, n, scores = tokens(query), len(DOCS), []
    for chunk, doc in zip(CHUNKS, DOCS):
        tf, s = Counter(doc), 0.0
        for w in q:
            if w in tf:
                idf = math.log(1 + (n - DF[w] + 0.5) / (DF[w] + 0.5))
                s += idf * tf[w] * 2.5 / (tf[w] + 1.5 * (0.25 + 0.75 * len(doc) / AVG))
        if chunk["status"].startswith("superseded"):
            s *= 0.5
        scores.append(s)
    order = np.argsort(scores)[::-1][:k]
    return [CHUNKS[i] for i in order if scores[i] > 0]
    # END SOLUTION


print("BM25 hit@1:", round(hit_at_1(bm25_search), 2))
K.check(hit_at_1(bm25_search) >= hit_at_1(port.keyword_search), "BM25 is at least as good as the baseline")

# %% [markdown]
# ## 3 · Vector search with character n-grams (6')
#
# A vector search compares meanings as points in space. Learned embeddings come from a model; to keep this lab on
# your laptop with nothing downloaded, the vectors are TF-IDF weights of character 3- to 5-grams. They already
# catch shared word parts across forms (رسوم, الرسم) that whole-word matching misses.
#
# ✏️ **Exercise** · Write `vector_search(query, k)`: the cosine similarity between the query's vector and every
# chunk's (rows of `MATRIX` are already unit length), the same 0.5 demotion for superseded chunks, top `k`.

# %%
def grams(text: str) -> Counter:
    t = f" {' '.join(tokens(text))} "
    return Counter(t[i:i + n] for n in (3, 4, 5) for i in range(len(t) - n + 1))


VOCAB = sorted({g for c in CHUNKS for g in grams(c["text"])})
INDEX = {g: i for i, g in enumerate(VOCAB)}
GDF = Counter(g for c in CHUNKS for g in set(grams(c["text"])))


def embed(text: str) -> np.ndarray:
    v = np.zeros(len(VOCAB))
    for g, n in grams(text).items():
        if g in INDEX:
            v[INDEX[g]] = (1 + math.log(n)) * math.log(len(CHUNKS) / GDF[g] + 1)
    return v / (np.linalg.norm(v) or 1)


MATRIX = np.stack([embed(c["text"]) for c in CHUNKS])


def vector_search(query: str, k: int = 3) -> list[dict]:
    # BEGIN SOLUTION
    sims = MATRIX @ embed(query)
    sims = np.array([s * (0.5 if c["status"].startswith("superseded") else 1) for s, c in zip(sims, CHUNKS)])
    return [CHUNKS[i] for i in np.argsort(sims)[::-1][:k] if sims[i] > 0]
    # END SOLUTION


scores = pd.DataFrame([{"search": n, "hit@1": round(hit_at_1(f), 2)} for n, f in
                       [("keyword baseline", port.keyword_search), ("BM25", bm25_search), ("vector", vector_search)]])
print(scores.to_string(index=False))
K.check(len(scores) == 3, "three retrievers scored")

# %% [markdown]
# ## 4 · Both as tools: which does the agent pick? (8')
#
# ✏️ **Exercise** · Wrap the two searches as tools with honest descriptions, run six questions (three English,
# three Arabic) through `K.run_agent` with both tools and `get_circular`, and record for each run: which search
# tools were called, in what order, and whether the answer cites the gold circular. The trace is the evidence.

# %%
def keyword_search_circulars(query: str) -> list[dict]:
    """Keyword (BM25) search over the circulars: best for exact terms, IDs and numbers. English or Arabic.

    Args:
        query: words to look for, e.g. "cancellation fee".
    """
    return [{"circular_id": c["circular_id"], "status": c["status"], "text": c["text"][:400]} for c in bm25_search(query)]


def vector_search_circulars(query: str) -> list[dict]:
    """Similarity search over the circulars: best for paraphrases and questions in other words. English or Arabic.

    Args:
        query: the question in your own words.
    """
    return [{"circular_id": c["circular_id"], "status": c["status"], "text": c["text"][:400]} for c in vector_search(query)]


p = port.Port(K.lab_dir("D2_2", reset=True))
SIX = EVAL[:3] + EVAL[8:11]
rows = []
for e in SIX:
    # BEGIN SOLUTION
    r = K.run_agent(e["q"], [keyword_search_circulars, vector_search_circulars, p.get_circular],
                    system=port.SYSTEM_PROMPT, max_steps=5, verbose=False)
    picks = [n for n, _ in r.tool_calls if n.endswith("search_circulars")]
    rows.append({"question": e["q"][:40], "picked": " > ".join(picks) or "none", "cites_gold": e["gold"] in r.final})
    # END SOLUTION
picks = pd.DataFrame(rows)
print(picks.to_string(index=False))
K.check(len(picks) == 6, "six traced runs")

# %% [markdown]
# 🔍 Did the agent pick by language, by phrasing, or always the first tool in the list? Swap the order of the two
# tools and run again: if the picks follow the order, the descriptions are not doing their job.

# %% [markdown]
# ## ✱ Stretch · When the corpus fits, skip retrieval
#
# Count the tokens of all eight circulars. If the whole corpus fits comfortably in the budget of Lab 2.1, putting
# it in the system prompt may beat any search. What would make you change your mind?

# %%
# BEGIN SOLUTION
corpus = "\n\n".join(d["text"] for d in port.load_circulars())
print(K.count_tokens(corpus), "tokens for all eight circulars")
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. Why does hit@1 matter more than hit@3 for an agent that quotes its first result?
# 2. Where does the protection against the superseded circular live: the index, the ranking or the prompt?
# 3. Which tool description would you change after reading the picks, and how?
