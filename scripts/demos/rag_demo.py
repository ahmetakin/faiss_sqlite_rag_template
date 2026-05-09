from app.rag import answer_with_rag

if __name__ == "__main__":
    questions = [
        "Elektrikli araç batarya garantisi kaç yıl?",
        "ENGINE-OIL-CASTROL ürün kodlu parçayı açıkla",
        "Fren balatası aşınırsa ne olur?",
        "Araba aküsü görselini getir"
    ]

    for q in questions:
        print("\n" + "=" * 80)
        print("Soru:", q)

        result = answer_with_rag(q, top_k=5)

        print("\nCevap:")
        print(result["answer"])

        print("\nKaynaklar:")
        for s in result["sources"]:
            print("-", s["title"], "|", s["product_code"], "|", s["image_path"])
'''
(.llmproject_env) user@user:~/ahmet-ai/faiss_sqlite_automotive$ PYTHONPATH=. python scripts/04_rag_demo.py

================================================================================
Soru: Elektrikli araç batarya garantisi kaç yıl?
Embedding modeli yükleniyor...
Loading weights: 100%|████████████████████████████████████████████████████| 625/625 [00:03<00:00, 159.47it/s]
Model hazır.
Model device: cuda:0

Cevap:
Elektrikli araç yüksek voltaj bataryaları **8 yıl** veya **160.000 kilometre** garanti kapsamındadır.

*   **Marka:** DemoAuto
*   **Kategori:** garanti
*   **Ürün Kodu:** EV-BATTERY-WARRANTY
*   **Görsel:** None

Kaynaklar:
- Elektrikli Araç Batarya Garanti Politikası | EV-BATTERY-WARRANTY | None
- Araç Aküsü Görseli | BAT-12V-PWRLN | images/car_battery_powerline.webp
- Araç Aküsü Görseli | BAT-12V-VRSTRT | images/car_battery_ever_start.jpeg
- Araç Aküsü Görseli | BAT-12V-BOSCH | images/car_battery_bosch.png
- Fren Balatası Görseli | BRK-PAD-FRONT-SBS-FC5 | images/brake_pad_sbs_honda_civic_fc5_front.jpg

================================================================================
Soru: ENGINE-OIL-CASTROL ürün kodlu parçayı açıkla

Cevap:
ENGINE-OIL-CASTROL ürün kodlu parça, Castrol Magnetic 5w-30 marka motor yağıdır. Bu koruyucu sıvı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önler ve motor ömrünü uzatır.

*   **Marka:** CASTROL
*   **Kategori:** motor_yagi_gorsel
*   **Görsel:** images/engine_oil_castrol_magnetic.jpg

Kaynaklar:
- Motor yağı görseli | ENGINE-OIL-CASTROL | images/engine_oil_castrol_magnetic.jpg

================================================================================
Soru: Fren balatası aşınırsa ne olur?

Cevap:
Fren balatası aşındığında frenleme sırasında ötme sesi duyulabilir, fren mesafesi uzayabilir, pedalda sertleşme hissedilebilir veya direksiyonda titreşim oluşabilir. Balata kalınlığı kritik seviyeye düştüğünde değişim yapılmalıdır.

**Ürün Kodu:** BRK-PAD-INFO
**Marka:** DemoAuto
**Kategori:** teknik_bilgi
**Görsel:** None

Kaynaklar:
- Fren Balatası Arıza Belirtileri | BRK-PAD-INFO | None
- Fren Balatası Görseli | BRK-PAD-FRONT-SBS-FC5 | images/brake_pad_sbs_honda_civic_fc5_front.jpg
- Fren Balatası Görseli | BRK-PAD-FRONT-OSIMCO-FC5 | images/brake_pad_osimco_honda_civic_fc5_front.png
- Fren Balatası Görseli | BRK-PAD-FRONT-BREMBO-FC5 | images/brake_pad_brembo_honda_civic_fc5_front.jpg
- Fren Balatası Görseli | BRK-PAD-FRONT-BOSCH-FC5 | images/brake_pad_bosch_honda_civic_fc5_front.jpg

================================================================================
Soru: Araba aküsü görselini getir

Cevap:
Verilen context bilgilerine göre araba aküsü görseli bulunmamaktadır. Context'te yalnızca **Fren Balatası** görselleri ve teknik bilgileri yer almaktadır.

*   **Marka:** SBS, OSIMCO, BREMBO, BOSCH (Fren Balatası için)
*   **Kategori:** yedek_parca_gorsel
*   **Görsel Yolları:**
    *   `images/brake_pad_sbs_honda_civic_fc5_front.jpg`
    *   `images/brake_pad_osimco_honda_civic_fc5_front.png`
    *   `images/brake_pad_brembo_honda_civic_fc5_front.jpg`
    *   `images/brake_pad_bosch_honda_civic_fc5_front.jpg`

Kaynaklar:
- Fren Balatası Görseli | BRK-PAD-FRONT-SBS-FC5 | images/brake_pad_sbs_honda_civic_fc5_front.jpg
- Fren Balatası Görseli | BRK-PAD-FRONT-OSIMCO-FC5 | images/brake_pad_osimco_honda_civic_fc5_front.png
- Fren Balatası Görseli | BRK-PAD-FRONT-BREMBO-FC5 | images/brake_pad_brembo_honda_civic_fc5_front.jpg
- Fren Balatası Görseli | BRK-PAD-FRONT-BOSCH-FC5 | images/brake_pad_bosch_honda_civic_fc5_front.jpg
- Fren Balatası Arıza Belirtileri | BRK-PAD-INFO | None



'''