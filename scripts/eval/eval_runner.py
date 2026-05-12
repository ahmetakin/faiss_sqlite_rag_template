import json
from datetime import datetime
from pathlib import Path

from app.services.retrieval_service import hybrid_search


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_DATASET_PATH = PROJECT_ROOT / "configs" / "eval" / "automotive" / "eval_dataset.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"


def load_eval_dataset():
    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_first_expected_rank(sources, expected_product_codes):
    """
    Beklenen product_code ilk kaçıncı sırada gelmiş bulur.

    Dönüş:
    - 1, 2, 3 ... rank
    - None: hiç bulunamadı
    """
    expected_set = set(expected_product_codes or [])

    for index, item in enumerate(sources, start=1):
        product_code = item.get("product_code")

        if product_code in expected_set:
            return index

    return None


def calculate_mrr(rank):
    """
    MRR = Mean Reciprocal Rank

    Doğru cevap 1. sıradaysa: 1.0
    Doğru cevap 2. sıradaysa: 0.5
    Doğru cevap 3. sıradaysa: 0.333
    Yoksa: 0
    """
    if rank is None:
        return 0.0

    return 1.0 / rank


def get_first_source_value(sources, key):
    if not sources:
        return None

    return sources[0].get(key)


def evaluate_case(case, top_k=5):
    question = case["question"]
    expected_product_codes = case.get("expected_product_codes") or []
    expected_tool = case.get("expected_tool")
    expected_strict_family = case.get("expected_strict_family")
    expected_recommendation_mode = case.get("expected_recommendation_mode")

    sources = hybrid_search(question, top_k=top_k)

    returned_product_codes = [
        item.get("product_code")
        for item in sources
    ]

    rank = find_first_expected_rank(
        sources=sources,
        expected_product_codes=expected_product_codes,
    )

    hit_at_1 = rank == 1
    hit_at_3 = rank is not None and rank <= 3
    hit_at_k = rank is not None and rank <= top_k
    mrr = calculate_mrr(rank)

    actual_tool = get_first_source_value(sources, "selected_tool")
    actual_strict_family = get_first_source_value(sources, "strict_family")
    actual_recommendation_mode = get_first_source_value(sources, "recommendation_mode")

    tool_ok = True
    if expected_tool is not None:
        tool_ok = actual_tool == expected_tool

    strict_family_ok = True
    if "expected_strict_family" in case:
        strict_family_ok = actual_strict_family == expected_strict_family

    recommendation_mode_ok = True
    if expected_recommendation_mode is not None:
        recommendation_mode_ok = actual_recommendation_mode == expected_recommendation_mode

    return {
        "question": question,
        "expected_product_codes": expected_product_codes,
        "returned_product_codes": returned_product_codes,
        "rank": rank,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_k": hit_at_k,
        "mrr": round(mrr, 4),
        "expected_tool": expected_tool,
        "actual_tool": actual_tool,
        "tool_ok": tool_ok,
        "expected_strict_family": expected_strict_family,
        "actual_strict_family": actual_strict_family,
        "strict_family_ok": strict_family_ok,
        "expected_recommendation_mode": expected_recommendation_mode,
        "actual_recommendation_mode": actual_recommendation_mode,
        "recommendation_mode_ok": recommendation_mode_ok,
        "sources": sources,
    }


def summarize_results(results):
    total = len(results)

    if total == 0:
        return {}

    hit_at_1_count = sum(1 for x in results if x["hit_at_1"])
    hit_at_3_count = sum(1 for x in results if x["hit_at_3"])
    hit_at_k_count = sum(1 for x in results if x["hit_at_k"])
    tool_ok_count = sum(1 for x in results if x["tool_ok"])
    strict_family_ok_count = sum(1 for x in results if x["strict_family_ok"])
    recommendation_mode_ok_count = sum(1 for x in results if x["recommendation_mode_ok"])

    avg_mrr = sum(x["mrr"] for x in results) / total

    return {
        "total": total,
        "hit_at_1": round(hit_at_1_count / total, 4),
        "hit_at_3": round(hit_at_3_count / total, 4),
        "hit_at_k": round(hit_at_k_count / total, 4),
        "mrr": round(avg_mrr, 4),
        "tool_accuracy": round(tool_ok_count / total, 4),
        "strict_family_accuracy": round(strict_family_ok_count / total, 4),
        "recommendation_mode_accuracy": round(recommendation_mode_ok_count / total, 4),
    }


def print_summary(summary):
    print("\n" + "=" * 80)
    print("EVAL SUMMARY")
    print("=" * 80)
    print(f"Toplam soru              : {summary['total']}")
    print(f"Hit@1                    : {summary['hit_at_1']}")
    print(f"Hit@3                    : {summary['hit_at_3']}")
    print(f"Hit@K                    : {summary['hit_at_k']}")
    print(f"MRR                      : {summary['mrr']}")
    print(f"Tool accuracy            : {summary['tool_accuracy']}")
    print(f"Strict family accuracy   : {summary['strict_family_accuracy']}")
    print(f"Recommendation accuracy  : {summary['recommendation_mode_accuracy']}")


def print_failures(results):
    failures = [
        item for item in results
        if not (
            item["hit_at_1"]
            and item["tool_ok"]
            and item["strict_family_ok"]
            and item["recommendation_mode_ok"]
        )
    ]

    if not failures:
        print("\nTüm kritik kontroller başarılı.")
        return

    print("\n" + "=" * 80)
    print("FAILURES / REVIEW NEEDED")
    print("=" * 80)

    for item in failures:
        print("\nSoru:", item["question"])
        print("Expected:", item["expected_product_codes"])
        print("Returned:", item["returned_product_codes"])
        print("Rank:", item["rank"])
        print("Tool:", item["actual_tool"], "| expected:", item["expected_tool"])
        print("Strict family:", item["actual_strict_family"], "| expected:", item["expected_strict_family"])
        print("Recommendation mode:", item["actual_recommendation_mode"], "| expected:", item["expected_recommendation_mode"])


def save_report(results, summary):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"eval_report_{timestamp}.json"

    payload = {
        "summary": summary,
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nJSON eval raporu kaydedildi: {output_path}")


if __name__ == "__main__":
    dataset = load_eval_dataset()

    results = []

    for index, case in enumerate(dataset, start=1):
        print(f"[{index}/{len(dataset)}] Eval: {case['question']}")
        result = evaluate_case(case, top_k=5)
        results.append(result)

    summary = summarize_results(results)

    print_summary(summary)
    print_failures(results)
    save_report(results, summary)