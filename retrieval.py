# get_relevant_questions(queries, role, difficulty, k_per_query, max_total)
import chromadb
from config import CHROMA_PATH, COLLECTION_NAME

_collection = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection(COLLECTION_NAME)

def _where(role, difficulty):
    conds = []
    if role: conds.append({"role": role})
    if difficulty: conds.append({"difficulty": difficulty})
    if not conds: return None
    return conds[0] if len(conds) == 1 else {"$and": conds}

def _query(q, k, where):
    kwargs = {"query_texts": [q], "n_results": k}
    if where: kwargs["where"] = where
    r = _collection.query(**kwargs)
    return [
        {**m, "id": i, "question": d.split(": ", 1)[-1], "distance": dist, "matched_query": q,
         "tags": m["tags"].split(",") if m["tags"] else []}
        for i, d, m, dist in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]

def get_relevant_questions(queries, role=None, difficulty=None, k_per_query=5, max_total=20):
    if not queries or _collection.count() == 0:
        return []
    best = {}
    for q in queries:
        hits = _query(q, k_per_query, _where(role, difficulty))
        if len(hits) < k_per_query and role:
            hits += _query(q, k_per_query, _where(None, difficulty))   # fallback
        for h in hits:
            if h["id"] not in best or h["distance"] < best[h["id"]]["distance"]:
                best[h["id"]] = h
    return sorted(best.values(), key=lambda h: h["distance"])[:max_total]
