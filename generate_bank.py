import json, re, time
from utils import client, MODEL

ROLES = {
    "backend developer": ["SQL", "Python", "system design", "APIs", "algorithms"],
    "frontend developer": ["JavaScript", "React", "CSS", "web performance", "algorithms"],
    "data analyst": ["SQL", "statistics", "data visualization", "Excel", "Python"],
    "data scientist": ["machine learning", "statistics", "Python", "SQL", "model evaluation"],
    "product manager": ["product strategy", "metrics", "prioritization", "stakeholder management", "user research"],
}
DIFFICULTIES = ["easy", "medium", "hard"]
PER_BATCH = 4

def batch(role, topic, difficulty):
    prompt = f"""Write {PER_BATCH} distinct {difficulty}-level interview questions on "{topic}"
for a {role}. Return ONLY JSON: {{"questions": [{{"question": str,
"reference_answer": str (1-3 sentences, factually correct), "tags": [2-3 short strings]}}]}}"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.8,
        max_tokens=3000,
    )
    return json.loads(resp.choices[0].message.content)["questions"]

bank, seen, counters = [], set(), {}
for role, topics in ROLES.items():
    code = "".join(w[0] for w in role.split())
    for topic in topics:
        slug = re.sub(r"\W+", "", topic.lower())
        for diff in DIFFICULTIES:
            try:
                items = batch(role, topic, diff)
            except Exception as e:
                print("skip", role, topic, diff, e)
                continue
            for it in items:
                key = it["question"].strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                n = counters[(role, topic)] = counters.get((role, topic), 0) + 1
                bank.append({
                    "id": f"{code}-{slug}-{n:03d}",
                    "role": role, "topic": topic, "difficulty": diff,
                    "question": it["question"].strip(),
                    "reference_answer": it["reference_answer"].strip(),
                    "tags": it.get("tags", []),
                })
            time.sleep(1)  # be gentle with rate limits
            print(role, topic, diff, len(bank))

json.dump(bank, open("data/question_bank.json", "w"), indent=2)
json.dump({"roles": list(ROLES),
           "topics": sorted({t for ts in ROLES.values() for t in ts}),
           "difficulties": DIFFICULTIES},
          open("data/vocab.json", "w"), indent=2)
print("done:", len(bank))
