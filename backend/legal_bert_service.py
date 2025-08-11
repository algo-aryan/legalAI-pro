# legal_bert_service.py
# Flask blueprint implementing /api/contract/upload
# Uses law-ai/InLegalBERT only for extraction, but also stores a Gemini ContractAnalyzer for chat

import os
import io
import re
import math
import uuid
from flask import Blueprint, request, jsonify, current_app
import pdfplumber
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm
from globals import contract_analyzers

# Import Gemini ContractAnalyzer for chat integration
from contract_bot import ContractAnalyzer as GeminiContractAnalyzer
bp = Blueprint("contract_api", __name__)

# ---------------- CONFIG ----------------
MODEL_NAME = os.environ.get("LEGAL_MODEL", "law-ai/InLegalBERT")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 16))
MAX_LENGTH = 512

CONTRACT_TYPES = [
    "Non-Disclosure Agreement",
    "Lease Agreement",
    "Employment Agreement",
    "Service Agreement",
    "Sale / Purchase Agreement",
    "Loan Agreement",
    "License Agreement",
    "Joint Venture / Partnership Agreement",
    "Construction Agreement",
]
RISK_KEYWORDS = {
    "indemnity": 2.0,
    "liability": 1.8,
    "penalty": 1.5,
    "termination": 1.2,
    "warranty": 1.0,
    "third party": 1.4,
    "dispute": 1.6,
    "breach": 2.0,
    "limitation of liability": 2.0,
}
KEY_TERM_TOP_K = 8

# --------- Model load (global on import) ----------
def _load_model():
    print(f"[legal_bert_service] Loading tokenizer & model {MODEL_NAME} -> {DEVICE}")
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    mdl = AutoModel.from_pretrained(MODEL_NAME)
    mdl.to(DEVICE)
    mdl.eval()
    return tok, mdl

_tokenizer, _model = _load_model()

# ------------- Utilities -------------
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text_pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for p in pdf.pages:
            try:
                page_text = p.extract_text() or ""
            except Exception:
                page_text = ""
            text_pages.append(page_text)
    return "\n".join(text_pages)

def split_to_sentences(text: str):
    text = re.sub(r"\s+", " ", text)
    sents = re.split(r'(?<=\.|\?|!)\s+(?=[A-Z0-9\"\'`])', text)
    return [s.strip() for s in sents if len(s.strip()) > 10]

def batch_iter(xs, bs):
    for i in range(0, len(xs), bs):
        yield xs[i:i+bs]

def get_embeddings(texts):
    if len(texts) == 0:
        return np.zeros((0, _model.config.hidden_size))
    all_emb = []
    with torch.no_grad():
        for batch in batch_iter(texts, BATCH_SIZE):
            enc = _tokenizer(batch, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
            enc = {k: v.to(DEVICE) for k, v in enc.items()}
            out = _model(**enc)
            cls = out.last_hidden_state[:, 0, :].cpu().numpy()
            all_emb.append(cls)
    return np.vstack(all_emb)

def cosine_sim(a, b):
    if a.shape[0] == 0 or b.shape[0] == 0:
        return np.zeros((a.shape[0], b.shape[0]))
    an = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    bn = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return np.matmul(an, bn.T)

def extract_date_candidates(text):
    patterns = [
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b",
        r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
        r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{4}\b",
    ]
    found = []
    for p in patterns:
        for m in re.findall(p, text, flags=re.IGNORECASE):
            if isinstance(m, tuple):
                part = " ".join([x for x in m if x])
                found.append(part)
            else:
                found.append(m)
    uniq = []
    for f in found:
        if f not in uniq:
            uniq.append(f)
        if len(uniq) >= 20:
            break
    longer = [d for d in uniq if re.search(r"\d{1,2}[\/\-\s]", d) or re.search(r"\d{1,2}(st|nd|rd|th)?\s", d)]
    return longer if longer else uniq

def extract_parties_by_patterns(text):
    t = text[:20000]
    parties = []
    patterns = [
        r"between\s+(.{3,200}?)\s+and\s+(.{3,200}?)\b",
        r"by and between\s+(.{3,200}?)\s+and\s+(.{3,200}?)\b",
        r"party of the first part[:,]?\s*(.{3,200}?)\b",
        r"party of the second part[:,]?\s*(.{3,200}?)\b",
    ]
    for p in patterns:
        for m in re.findall(p, t, flags=re.IGNORECASE | re.DOTALL):
            if isinstance(m, tuple):
                for g in m:
                    g = re.sub(r"\s+", " ", g).strip()
                    g = re.sub(r"[,;].*$", "", g).strip()
                    if 3 < len(g) < 200 and g not in parties:
                        parties.append(g)
            else:
                g = re.sub(r"\s+", " ", m).strip()
                g = re.sub(r"[,;].*$", "", g).strip()
                if 3 < len(g) < 200 and g not in parties:
                    parties.append(g)
    if len(parties) < 2:
        caps = re.findall(r"\b([A-Z][a-zA-Z0-9&,.()'\-]{2,100})\b", t)
        uniq = []
        for c in caps:
            if len(c) > 3 and c.lower() not in [u.lower() for u in uniq]:
                uniq.append(c)
            if len(uniq) >= 4:
                break
        for u in uniq:
            if u not in parties:
                parties.append(u)
    return parties[:6]

def extract_duration_candidates(text):
    patterns = [
        r"(for a period of\s+\w+\s*\(\d+\)\s+years?)",
        r"(for a period of\s+[\w\s,\-\(\)]+?years?)",
        r"(for a term of\s+[\w\s,\-\(\)]+?years?)",
        r"(commencement.*?\b(\d{4}|\d{1,2}\s+years?))",
        r"(term of this agreement is\s+[\w\s,\-\(\)]+?years?)",
    ]
    found = []
    for p in patterns:
        for m in re.findall(p, text, flags=re.IGNORECASE):
            if isinstance(m, tuple):
                part = " ".join([x for x in m if x])
                found.append(part.strip())
            else:
                found.append(m.strip())
            if len(found) >= 10:
                break
    return found

# ------------ main analyzer ------------
def analyze_text(text):
    sentences = split_to_sentences(text)
    if not sentences:
        sentences = [text]
    sent_emb = get_embeddings(sentences)

    # Contract type
    type_emb = get_embeddings(CONTRACT_TYPES)
    sims = cosine_sim(type_emb, sent_emb)
    if sims.size == 0:
        contract_type = CONTRACT_TYPES[0]
        contract_type_score = 0.0
    else:
        max_sims = sims.max(axis=1)
        best_type_idx = int(np.argmax(max_sims))
        contract_type = CONTRACT_TYPES[best_type_idx]
        contract_type_score = float(max_sims[best_type_idx])
    # --- Force Lease Agreement if title contains "LEASE"
    # Improved and more comprehensive contract type keyword mapping
    AGREEMENT_KEYWORDS = {
        # NDAs
        "NDA": "Non-Disclosure Agreement",
        "NON DISCLOSURE": "Non-Disclosure Agreement",
        "NON-DISCLOSURE": "Non-Disclosure Agreement",
        "CONFIDENTIALITY AGREEMENT": "Non-Disclosure Agreement",
        # Lease
        "LEASE": "Lease Agreement",
        "TENANCY": "Lease Agreement",
        "RENTAL AGREEMENT": "Lease Agreement",
        "SUBLEASE": "Lease Agreement",
        # Employment
        "EMPLOYMENT": "Employment Agreement",
        "EMPLOYEE CONTRACT": "Employment Agreement",
        "OFFER LETTER": "Employment Agreement",
        # Service
        "SERVICE AGREEMENT": "Service Agreement",
        "PROFESSIONAL SERVICES": "Service Agreement",
        "CONSULTING AGREEMENT": "Service Agreement",
        "STATEMENT OF WORK": "Service Agreement",
        "INDEPENDENT CONTRACTOR": "Service Agreement",
        # Sale/Purchase
        "PURCHASE AGREEMENT": "Sale / Purchase Agreement",
        "SALES AGREEMENT": "Sale / Purchase Agreement",
        "PURCHASE ORDER": "Sale / Purchase Agreement",
        "BILL OF SALE": "Sale / Purchase Agreement",
        # Loan
        "LOAN": "Loan Agreement",
        "PROMISSORY NOTE": "Loan Agreement",
        "CREDIT AGREEMENT": "Loan Agreement",
        "LINE OF CREDIT": "Loan Agreement",
        # License
        "LICENSE": "License Agreement",
        "LICENSING": "License Agreement",
        "SOFTWARE LICENSE": "License Agreement",
        "SAAS": "License Agreement",
        "SOFTWARE-AS-A-SERVICE": "License Agreement",
        # Partnership/Joint Venture
        "PARTNERSHIP": "Joint Venture / Partnership Agreement",
        "JOINT VENTURE": "Joint Venture / Partnership Agreement",
        "JV AGREEMENT": "Joint Venture / Partnership Agreement",
        # Construction
        "CONSTRUCTION": "Construction Agreement",
        "CONTRACTOR AGREEMENT": "Construction Agreement",
        "GENERAL CONTRACTOR": "Construction Agreement",
        # Franchise
        "FRANCHISE AGREEMENT": "Franchise Agreement",
        # Distribution
        "DISTRIBUTION AGREEMENT": "Distribution Agreement",
        "RESELLER": "Distribution Agreement",
        # Others
        "SHAREHOLDER AGREEMENT": "Shareholder Agreement",
        "STOCK PURCHASE": "Shareholder Agreement",
        "FOUNDERS AGREEMENT": "Founders Agreement",
        "OPERATING AGREEMENT": "Operating Agreement",
        "SUPPLY AGREEMENT": "Supply Agreement",
        "MAINTENANCE": "Service Agreement",
        "SUPPORT": "Service Agreement",
        "AGENCY AGREEMENT": "Agency Agreement"
    }


    header_sample = text[:500].upper()
    for keyword, ctype in AGREEMENT_KEYWORDS.items():
        if keyword in header_sample:
            contract_type = ctype
            break

    # Key Terms
    keyword_prompts = list(RISK_KEYWORDS.keys()) + ["confidentiality", "governing law", "payment", "warranty", "assignment", "scope of work", "termination"]
    key_emb = get_embeddings(keyword_prompts)
    sims_k = cosine_sim(key_emb, sent_emb)
    key_terms = []
    seen_idx = set()
    for i, kw in enumerate(keyword_prompts):
        if sims_k.size == 0:
            continue
        best_idx = int(np.argmax(sims_k[i]))
        score = float(sims_k[i, best_idx])
        if best_idx not in seen_idx and score > 0.45:
            key_terms.append({"keyword": kw, "sentence": sentences[best_idx], "score": score})
            seen_idx.add(best_idx)
        if len(key_terms) >= KEY_TERM_TOP_K:
            break

    # Dates
    date_cands = extract_date_candidates(text)
    date_prompt_emb = get_embeddings([
        "This agreement is made on DATE",
        "Effective date of this agreement is DATE"
    ])
    date_results = []
    for d in date_cands:
        found_idx = next((i for i, s in enumerate(sentences) if d.lower() in s.lower()), None)
        confidence = 0.0
        context = sentences[found_idx] if found_idx is not None else ""
        if found_idx is not None and date_prompt_emb.shape[0] > 0:
            sc = cosine_sim(date_prompt_emb, sent_emb[found_idx:found_idx+1]).max()
            confidence = float(sc)
        date_results.append({"date": d, "context": context, "confidence": confidence})
    def date_rank(d):
        ctx = d["context"].lower()
        score = d["confidence"]
        if any(w in ctx for w in ["commence", "commencement", "start date", "effective date", "effective", "begin"]):
            score += 2.0
        if any(w in ctx for w in ["terminate", "termination", "expiry", "expire", "end date"]):
            score -= 2.0
        return score
    date_results.sort(key=date_rank, reverse=True)

    parties = extract_parties_by_patterns(text)
    durations = extract_duration_candidates(text)

    # Risk Scoring
    risk_score = 0.0
    risk_hits = []
    rk_list = list(RISK_KEYWORDS.keys())
    rk_emb = get_embeddings(rk_list)
    sims_rk = cosine_sim(rk_emb, sent_emb)
    for i, rk in enumerate(rk_list):
        if sims_rk.size == 0:
            continue
        best_idx = int(np.argmax(sims_rk[i]))
        best_score = float(sims_rk[i, best_idx])
        if best_score > 0.45:
            contribution = best_score * RISK_KEYWORDS[rk]
            risk_score += contribution
            risk_hits.append({"keyword": rk, "sentence": sentences[best_idx], "sim": best_score, "weight": RISK_KEYWORDS[rk]})
    seen_contexts = set()
    unique_hits = []
    for hit in risk_hits:
        ctx_sig = hit["sentence"].strip().lower()
        if ctx_sig not in seen_contexts:
            unique_hits.append(hit)
            seen_contexts.add(ctx_sig)
    risk_hits = unique_hits

    risk_norm = (1 - math.exp(-risk_score / 2.0)) * 100
    if risk_norm > 75:
        risk_level = "HIGH"
    elif risk_norm > 35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    summary_date = 'N/A'
    for d in date_results:
        ctx = d["context"].lower()
        if any(w in ctx for w in ["commence", "commencement", "start date", "effective date", "effective", "begin"]):
            summary_date = d["date"]
            break
    if summary_date == 'N/A' and date_results:
        summary_date = date_results[0]['date']

    return {
        "contract_type": contract_type,
        "contract_type_confidence": contract_type_score,
        "parties": parties,
        "dates": date_results,
        "durations": durations,
        "key_terms": key_terms,
        "risk": {"score": risk_norm, "level": risk_level, "hits": risk_hits},
        "summary_date": summary_date
    }

# ------------- Flask route --------------
@bp.route("/contract/upload", methods=["POST"])
def upload_and_analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        content = f.read()
        text = extract_text_from_pdf_bytes(content) or content.decode("utf-8", errors="ignore")
        analysis = analyze_text(text)
        summary_date = analysis.get('summary_date', 'N/A')
        summary_parts = [
            f"Contract Type: {analysis['contract_type']}",
            f"Parties: {', '.join(analysis['parties']) if analysis['parties'] else 'N/A'}",
            f"Date: {summary_date}",
            f"Durations: {', '.join(analysis['durations']) if analysis['durations'] else 'N/A'}"
        ]
        risks_list = [{
            "keyword": hit["keyword"],
            "context": hit["sentence"],
            "level": analysis["risk"]["level"],
            "score": round(hit["sim"] * 100, 2)
        } for hit in analysis["risk"]["hits"]]
        terms_list = [{
            "keyword": term["keyword"],
            "context": term["sentence"],
            "score": round(term["score"] * 100, 2)
        } for term in analysis["key_terms"]]

        session_id = str(uuid.uuid4())
        os.makedirs("uploads", exist_ok=True)
        temp_path = os.path.join("uploads", f"{session_id}_{f.filename}")
        with open(temp_path, "wb") as out_f:
            out_f.write(content)
        gemini_analyzer = GeminiContractAnalyzer()
        gemini_analyzer.load_document(temp_path)
        contract_analyzers[session_id] = gemini_analyzer

        return jsonify({
            "filename": f.filename,
            "session_id": session_id,
            "summary": "\n".join(summary_parts),
            "risks": risks_list,
            "terms": terms_list
        }), 200

    except Exception as e:
        current_app.logger.exception("Error analyzing file")
        return jsonify({"error": str(e)}), 500
