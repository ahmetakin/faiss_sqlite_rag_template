from app.core.router import detect_query_intent
from app.core.tool_router import select_tool


questions = [
    "Elektrikli araç batarya garantisi kaç yıl?",
    "Fren balatası aşınırsa ne olur?",
    "BOSCH akü görselini getir",
    "ENGINE-OIL-CASTROL ürün kodlu parçayı açıkla",
    "en iyi motor yağı hangisi",
    "DPF nasıl temizlenir?",
]


if __name__ == "__main__":
    for question in questions:
        route = detect_query_intent(question)
        selected_tool = select_tool(question, route)

        print("=" * 80)
        print("Soru:", question)
        print("Intent:", route["intent"])
        print("Strict family:", route["strict_family"])
        print("Seçilen tool:", selected_tool)