"""Explainable ranking: exact skills coverage and corpus-based TF-IDF cosine."""
import math
import re
import unicodedata
from collections import Counter


def normalize(text):
    text = unicodedata.normalize('NFKD', text.casefold())
    return ''.join(c for c in text if not unicodedata.combining(c)).strip()


def parse_skills(text):
    return {normalize(s) for s in re.split(r'[,;\n]+', text) if s.strip()}


def tokens(text):
    # Preserve technical terms such as C++, C# and TF-IDF.
    return re.findall(r'[a-z0-9]+(?:\+\+|#|-[a-z0-9]+)*', normalize(text))


def tfidf_vectors(documents):
    counts = [Counter(tokens(d)) for d in documents]
    frequency = Counter(term for count in counts for term in count)
    n = len(counts)
    return [{term: (1 + math.log(count)) * (1 + math.log((n + 1) / (frequency[term] + 1)))
             for term, count in terms.items()} for terms in counts]


def cosine(a, b):
    denominator = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return sum(v * b.get(k, 0) for k, v in a.items()) / denominator if denominator else 0.0


def rank_offers(offers, skills_text, interests=''):
    skills = parse_skills(skills_text)
    profile = ' '.join(sorted(skills)) + ' ' + interests
    vectors = tfidf_vectors([profile] + [o['title'] + ' ' + o['description'] + ' ' + ' '.join(o['skills']) for o in offers])
    results = []
    for offer, vector in zip(offers, vectors[1:]):
        matched = [s for s in offer['skills'] if normalize(s) in skills]
        missing = [s for s in offer['skills'] if normalize(s) not in skills]
        coverage = len(matched) / len(offer['skills']) if offer['skills'] else 0.0
        similarity = max(0.0, min(1.0, cosine(vectors[0], vector)))
        score = round(100 * (0.8 * coverage + 0.2 * similarity))
        results.append(dict(offer, matched=matched, missing=missing, score=score,
                            coverage=round(100*coverage), similarity=round(100*similarity)))
    return sorted(results, key=lambda o: (-o['score'], -o['coverage'], o['title']))
