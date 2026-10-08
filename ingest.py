# Usage: python ingest.py --file data/question_bank.json
import json, argparse
import chromadb
from config import CHROMA_PATH, COLLECTION_NAME

REQUIRED = ["id", "role", "topic", "difficulty", "question", "reference_answer"]

def main(path):
    entries = json.load(open(path))
    vocab = json.load(open("data/vocab.json"))

    ids, docs, metas, skipped = [], [], [], []
    for e in entries:
        missing = [f for f in REQUIRED if not e.get(f)]
        if missing:
            skipped.append((e.get("id"), f"missing {missing}"))
        elif e["role"] not in vocab["roles"]:
            skipped.append((e["id"], f"unknown role {e['role']}"))
        elif e["topic"] not in vocab["topics"]:
            skipped.append((e["id"], f"unknown topic {e['topic']}"))
        elif e["difficulty"] not in vocab["difficulties"]:
            skipped.append((e["id"], f"unknown difficulty {e['difficulty']}"))
        else:
            ids.append(e["id"])
            docs.append(f"{e['topic']}: {e['question']}")
            metas.append({
                "role": e["role"], "topic": e["topic"],
                "difficulty": e["difficulty"],
                "reference_answer": e["reference_answer"],
                "tags": ",".join(e.get("tags", [])),
            })

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    if ids:
        collection.upsert(ids=ids, documents=docs, metadatas=metas)

    print(f"read {len(entries)}, upserted {len(ids)}, skipped {len(skipped)}")
    for s in skipped:
        print("  skipped:", s)
    print("collection count:", collection.count())

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--file", default="data/question_bank.json")
    main(p.parse_args().file)
