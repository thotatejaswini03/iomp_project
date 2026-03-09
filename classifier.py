"""
classifier.py — NLP Pipeline
Raw Text -> Preprocess -> TF-IDF -> Cosine Similarity -> Category + Priority
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

for resource in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"]:
    try:
        nltk.download(resource, quiet=True)
    except Exception:
        pass

CATEGORY_SEEDS = {
    "HR & Payroll": (
        "salary payroll compensation wage increment bonus appraisal hike performance "
        "leave annual casual sick medical maternity paternity attendance transfer "
        "promotion demotion probation contract appointment termination resignation "
        "harassment discrimination gender bias workplace bullying hr policy"
    ),
    "IT & Systems": (
        "laptop computer desktop hardware software application system crash error "
        "network internet wifi connectivity vpn access login password reset account "
        "email outlook teams zoom installation update upgrade server database "
        "printer scanner peripheral device it support helpdesk technical issue"
    ),
    "Finance & Reimbursement": (
        "reimbursement expense claim invoice payment refund tax deduction allowance "
        "travel conveyance medical bill receipt finance accounts pending amount "
        "salary deduction pf provident fund insurance premium advance loan recovery"
    ),
    "Facilities & Infrastructure": (
        "office building parking cafeteria canteen food transport bus shuttle "
        "housekeeping cleanliness restroom washroom maintenance repair electricity "
        "ac air conditioning heating ventilation lift elevator safety fire exit "
        "security access card badge infrastructure workspace desk chair furniture"
    ),
    "Management & Policy": (
        "manager supervisor team lead management leadership policy unfair treatment "
        "workload overwork overtime deadline pressure micromanagement favoritism "
        "nepotism biased evaluation review feedback culture toxic "
        "communication miscommunication team conflict colleague behavior"
    ),
    "Legal & Compliance": (
        "legal compliance violation law regulation contract breach confidentiality "
        "data privacy nda agreement sexual harassment misconduct investigation "
        "audit fraud corruption unethical illegal disciplinary action warning"
    ),
}

# ── Priority keyword tiers ────────────────────────────────────────────────────
# HIGH: Financial loss, safety, harassment, legal, urgent non-payment
HIGH_KEYWORDS = [
    # Urgency signals
    "urgent", "urgently", "immediately", "emergency", "critical", "asap",
    "serious", "severe", "unsafe", "danger", "dangerous",
    # Financial non-payment (very common grievances)
    "not credited", "not yet credited", "yet credited", "not received", "not yet received",
    "not paid", "not yet paid", "unpaid", "salary not",
    "salary pending", "salary delay", "salary hold", "salary deducted",
    "wrongly deducted", "incorrect deduction", "payment not", "payment pending",
    "reimbursement pending", "reimbursement not", "claim not", "not reimbursed",
    "dues pending", "outstanding dues", "months pending", "weeks pending",
    # Harassment and safety
    "harassment", "harassed", "abuse", "abused", "assault", "assaulted",
    "threat", "threatened", "violence", "bullying", "bullied", "forced",
    "discrimination", "discriminated", "toxic", "hostile",
    # Legal
    "illegal", "fraud", "corrupt", "misconduct", "violation", "breach",
    "wrongful", "termination", "fired unfairly",
]

# MEDIUM: Functional issues, delays, broken systems
MEDIUM_KEYWORDS = [
    # Delay and pending
    "delay", "delayed", "pending", "overdue", "waiting", "waited",
    "not working", "not resolved", "unresolved", "ignored", "no response",
    "no action", "no reply",
    # System and work issues
    "broken", "crashed", "error", "failed", "failure", "issue", "problem",
    "concern", "complaint", "incorrect", "wrong", "missing",
    "not functioning", "malfunction", "slow", "not accessible",
    # HR issues
    "leave rejected", "leave not approved", "attendance issue",
    "transfer issue", "appraisal issue", "promotion pending",
    "increment pending", "unfair", "biased",
    # Facilities
    "not cleaned", "not repaired", "not maintained", "not available",
    "out of order", "not working properly",
]

_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words("english"))


def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in _stop_words and len(t) > 2]
    tokens = [_lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)


def _build_vectorizer():
    categories = list(CATEGORY_SEEDS.keys())
    seeds = [preprocess(CATEGORY_SEEDS[c]) for c in categories]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    seed_matrix = vectorizer.fit_transform(seeds)
    return vectorizer, seed_matrix, categories


_vectorizer, _seed_matrix, _categories = _build_vectorizer()


def classify_category(text: str):
    processed = preprocess(text)
    if not processed.strip():
        return "General", 0.0
    text_vec = _vectorizer.transform([processed])
    similarities = cosine_similarity(text_vec, _seed_matrix)[0]
    best_idx = int(np.argmax(similarities))
    confidence = float(similarities[best_idx])
    if confidence < 0.05:
        return "General", confidence
    return _categories[best_idx], round(confidence, 3)


def classify_priority(text: str) -> str:
    """
    Priority detection on original text (lowercased) + preprocessed tokens.
    Checks multi-word phrases on raw text first for accuracy.
    """
    raw = text.lower()
    processed = preprocess(text)

    # Check HIGH on raw text first (catches multi-word phrases like "not credited")
    if any(kw in raw for kw in HIGH_KEYWORDS):
        return "High"

    # Check MEDIUM on raw text
    if any(kw in raw for kw in MEDIUM_KEYWORDS):
        return "Medium"

    # Fallback check on processed tokens
    if any(kw in processed for kw in HIGH_KEYWORDS):
        return "High"
    if any(kw in processed for kw in MEDIUM_KEYWORDS):
        return "Medium"

    return "Low"


def classify(text: str) -> dict:
    category, confidence = classify_category(text)
    priority = classify_priority(text)
    return {
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "processed_text": preprocess(text),
    }
