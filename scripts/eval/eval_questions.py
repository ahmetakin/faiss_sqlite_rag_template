import json
from datetime import datetime

from app.core.config import OUTPUT_DIR, ensure_directories
from app.core.rag import answer_with_rag


def print_sources(sources):
    print("\nKaynaklar:")

    for item in sources:
        print(
            "-",
            item.get("match_type"),
            "|",
            item.get("title"),
            "|",
            item.get("product_code"),
            "|",
            item.get("image_path")
        )


def save_results_to_json(results, filename=None):
    ensure_directories()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = OUTPUT_DIR / f"rag_results_{timestamp}.json"
    else:
        filename = OUTPUT_DIR / filename

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nJSON kaydedildi: {filename}")


if __name__ == "__main__":
    questions = [
        "Elektrikli araç batarya garantisi kaç yıl?",
        "Araç aküsü garanti süresi kaç yıl?",
        "Motor garantisi kaç yıl?",
        "Şanzıman garanti şartları nelerdir?",
        "Elektrik sistemleri garanti kapsamında mı?",
        "Fren balatası aşınırsa ne olur?",
        "Fren hidroliği nem oranı artarsa ne olur?",
        "Vakum pompası arızalanırsa fren nasıl etkilenir?",
        "Honda civic fc5 fren balatası görselini getir",
        "BREMBO fren diski görselini getir",
        "Debriyaj seti görselini getir",
        "Akü şarj cihazı görselini getir",
        "Araba aküsü görselini getir",
        "BOSCH akü görselini getir",
        "en iyi araba aküsü markası hangisi",
        "fiyat performans akü öner",
        "en iyi fren balatası hangisi",
        "en iyi fren diski hangisi",
        "en ucuz motor yağı hangisi",
        "en iyi motor yağı hangisi",
        "ENGINE-OIL-AKN ürün kodlu parçayı açıkla",
        "BRAKE-DISC-BREMBO ürün kodlu parçayı açıkla",
        "CLUTCH-KIT-LUK ürün kodlu parçayı açıkla",
        "AIR-FIL-MANN ürün kodlu parçayı açıkla",
        "turbo arızasında ne olur?",
        "DPF nasıl temizlenir?",
        "Start stop sistemi neden devreye girmez?",
        "ABS ışığı yanarsa ne anlama gelir?",
        "triger kayışı koparsa ne olur?",
        "yağ lambası kırmızı yanarsa ne yapılmalı?"
    ]

    all_results = []

    for question in questions:
        print("\n" + "=" * 80)
        print("Soru:", question)

        result = answer_with_rag(question, top_k=5)

        print("\nCevap:")
        print(result["answer"])

        print_sources(result["sources"])

        all_results.append(result)

    save_results_to_json(all_results)