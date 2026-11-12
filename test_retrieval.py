# Checks retrieval against the Chroma collection
from retrieval import get_relevant_questions

def test_filters_apply():
    hits = get_relevant_questions(["SQL joins"], role="backend developer", difficulty="easy", max_total=5)
    assert hits
    assert all(h["role"] == "backend developer" and h["difficulty"] == "easy" for h in hits)

def test_topic_relevance():
    hits = get_relevant_questions(["React hooks"], role="frontend developer", max_total=5)
    assert any(h["topic"] == "React" for h in hits[:3])
