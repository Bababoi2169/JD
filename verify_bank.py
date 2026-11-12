import json, time
from utils import chat, MODEL

PATH = "data/question_bank.json"
BATCH = 8

def check(batch):
    items = [{k: e[k] for k in ("id", "role", "topic", "question", "reference_answer")} for e in batch]
    prompt = f"""You are a strict senior engineer reviewing interview questions.
For each item decide:
- "ok": the question is clear and self-contained, and the reference answer is accurate
- "fix": the question is fine but the answer is wrong or misleading; give corrected_answer (1-3 sentences)
- "bad": the question is ambiguous, off-topic for the role, or unanswerable
Be skeptical: if you are not sure the answer is correct, use "fix" or "bad".
Return ONLY JSON: {{"results": [{{"id": str, "verdict": "ok"|"fix"|"bad", "corrected_answer": str or null, "note": str}}]}}

{json.dumps(items)}"""
    resp = chat(model=MODEL, messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}, temperature=0.1,
                max_tokens=4000, reasoning_effort="low")
    return json.loads(resp.choices[0].message.content)["results"]

def main():
    bank = json.load(open(PATH))
    by_id = {e["id"]: e for e in bank}
    todo = [e for e in bank if e.get("status", "unverified") == "unverified"]
    for i in range(0, len(todo), BATCH):
        try:
            results = check(todo[i:i + BATCH])
        except Exception as ex:
            print("batch failed:", ex)
            continue
        for r in results:
            e = by_id.get(r.get("id"))
            if not e:
                continue
            if r.get("verdict") == "ok":
                e["status"] = "auto_ok"
            else:
                e["status"] = "flagged"
                e["review_note"] = r.get("note", "")
                if r.get("verdict") == "fix" and r.get("corrected_answer"):
                    e["suggested_answer"] = r["corrected_answer"]
        json.dump(bank, open(PATH, "w"), indent=2)   # saved every batch, so it can resume
        print(f"{min(i + BATCH, len(todo))}/{len(todo)} checked")
        time.sleep(2)
    print("flagged:", sum(e.get("status") == "flagged" for e in bank), "of", len(bank))

if __name__ == "__main__":
    main()
