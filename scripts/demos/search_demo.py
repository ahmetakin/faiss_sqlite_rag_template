from app.search import search_by_text


def print_results(results):
    print("\nSonuçlar:\n")

    for i, item in enumerate(results, start=1):
        print(f"{i}. Skor       : {item['score']:.4f}")
        print(f"   Match      : {item.get('match_type')}")
        print(f"   Vector Tip : {item.get('vector_type')}")
        print(f"   Tip        : {item['item_type']}")
        print(f"   Başlık     : {item['title']}")
        print(f"   Kategori   : {item['category']}")
        print(f"   Ürün kodu  : {item['product_code']}")
        print(f"   Kaynak     : {item['source']}")
        print(f"   Görsel     : {item['image_path']}")
        print(f"   İçerik     : {item['content']}")
        print(f"   Metadata   : {item['metadata']}")
        print("-" * 80)


if __name__ == "__main__":
    queries = [
        "elektrikli araç batarya garanti süresi kaç yıl",
        "araba aküsü görselini getir",
        "fren balatası aşınırsa ne olur",
        "motor yağı kaç kilometrede değişir",
        "ENGINE-OIL-CASTROL ürün kodlu parça",
        "Castrol motor yağı görselini getir",
        "BOSCH akü görseli",
        "Honda civic fc5 ön fren balatası"
    ]

    for query in queries:
        print("\n" + "=" * 80)
        print("Sorgu:", query)
        results = search_by_text(query, top_k=5)
        print_results(results)

'''
(.llmproject_env) user@user:~/ahmet-ai/faiss_sqlite_automotive$ PYTHONPATH=. python scripts/03_search_demo.py

================================================================================
Sorgu: elektrikli araç batarya garanti süresi kaç yıl
Embedding modeli yükleniyor...
Loading weights: 100%|███████████████████████████████████████████████| 625/625 [00:00<00:00, 693.02it/s]
Model hazır.
Model device: cuda:0

Sonuçlar:

1. Skor       : 0.8554
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : text
   Başlık     : Elektrikli Araç Batarya Garanti Politikası
   Kategori   : garanti
   Ürün kodu  : EV-BATTERY-WARRANTY
   Kaynak     : servis_dokumani
   Görsel     : None
   İçerik     : Elektrikli araç yüksek voltaj bataryaları 8 yıl veya 160.000 kilometre garanti kapsamındadır. Garanti kapsamında değerlendirilebilmesi için batarya kapasitesinin belirlenen eşik seviyenin altına düşmesi gerekir. Yetkisiz müdahale, fiziksel hasar veya uygunsuz şarj altyapısı nedeniyle oluşan arızalar garanti dışı sayılabilir.
   Metadata   : {'brand': 'DemoAuto', 'vehicle_type': 'electric', 'department': 'after_sales'}
--------------------------------------------------------------------------------
2. Skor       : 0.7976
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Araç Aküsü Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BAT-12V-PWRLN
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/car_battery_powerline.webp
   İçerik     : 12V araç aküsü, otomotiv marş sistemi ve elektrik besleme parçası.
   Metadata   : {'brand': 'POWERLINE', 'part_group': 'battery', 'voltage': '12V'}
--------------------------------------------------------------------------------
3. Skor       : 0.7910
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Araç Aküsü Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BAT-12V-VRSTRT
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/car_battery_ever_start.jpeg
   İçerik     : 12V araç aküsü, otomotiv marş sistemi ve elektrik besleme parçası.
   Metadata   : {'brand': 'EVER START', 'part_group': 'battery', 'voltage': '12V'}
--------------------------------------------------------------------------------
4. Skor       : 0.7854
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Araç Aküsü Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BAT-12V-BOSCH
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/car_battery_bosch.png
   İçerik     : 12V araç aküsü, otomotiv marş sistemi ve elektrik besleme parçası.
   Metadata   : {'brand': 'BOSCH', 'part_group': 'battery', 'voltage': '12V'}
--------------------------------------------------------------------------------
5. Skor       : 0.7735
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : text
   Başlık     : Fren Balatası Arıza Belirtileri
   Kategori   : teknik_bilgi
   Ürün kodu  : BRK-PAD-INFO
   Kaynak     : teknik_bilgi_bankasi
   Görsel     : None
   İçerik     : Fren balatası aşınması durumunda frenleme sırasında ötme sesi, fren mesafesinde uzama, pedalda sertleşme veya direksiyonda titreşim görülebilir. Balata kalınlığı kritik seviyeye düştüğünde balata değişimi yapılmalıdır.
   Metadata   : {'brand': 'DemoAuto', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: araba aküsü görselini getir

Sonuçlar:

1. Skor       : 0.7906
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-SBS-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_sbs_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'SBS', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
2. Skor       : 0.7867
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-OSIMCO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_osimco_honda_civic_fc5_front.png
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'OSIMCO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
3. Skor       : 0.7802
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BREMBO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_brembo_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça.Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BREMBO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
4. Skor       : 0.7791
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BOSCH-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_bosch_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BOSCH', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
5. Skor       : 0.7783
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Araç Aküsü Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BAT-12V-PWRLN
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/car_battery_powerline.webp
   İçerik     : 12V araç aküsü, otomotiv marş sistemi ve elektrik besleme parçası.
   Metadata   : {'brand': 'POWERLINE', 'part_group': 'battery', 'voltage': '12V'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: fren balatası aşınırsa ne olur

Sonuçlar:

1. Skor       : 0.7874
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : text
   Başlık     : Fren Balatası Arıza Belirtileri
   Kategori   : teknik_bilgi
   Ürün kodu  : BRK-PAD-INFO
   Kaynak     : teknik_bilgi_bankasi
   Görsel     : None
   İçerik     : Fren balatası aşınması durumunda frenleme sırasında ötme sesi, fren mesafesinde uzama, pedalda sertleşme veya direksiyonda titreşim görülebilir. Balata kalınlığı kritik seviyeye düştüğünde balata değişimi yapılmalıdır.
   Metadata   : {'brand': 'DemoAuto', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
2. Skor       : 0.7729
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-SBS-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_sbs_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'SBS', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
3. Skor       : 0.7685
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-OSIMCO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_osimco_honda_civic_fc5_front.png
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'OSIMCO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
4. Skor       : 0.7622
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BREMBO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_brembo_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça.Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BREMBO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
5. Skor       : 0.7588
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BOSCH-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_bosch_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BOSCH', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: motor yağı kaç kilometrede değişir

Sonuçlar:

1. Skor       : 0.7733
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-TOTAL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_total_quartz_5w_40.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Total Quartz 5w-40 marka.
   Metadata   : {'brand': 'TOTAL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
2. Skor       : 0.7723
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-PPLUS
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_performance_plus_5w_20.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Performance Plus 5w-20 marka.
   Metadata   : {'brand': 'PERFORMANCE PLUS', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
3. Skor       : 0.7716
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : text
   Başlık     : Motor Yağı Değişim Prosedürü
   Kategori   : servis
   Ürün kodu  : ENG-OIL-SERVICE
   Kaynak     : servis_proseduru
   Görsel     : None
   İçerik     : Benzinli araçlarda motor yağı değişimi normal kullanım koşullarında 10.000 kilometre veya 12 ayda bir yapılmalıdır. Ağır kullanım koşullarında bu süre 7.500 kilometreye düşürülebilir. Yağ filtresi her yağ değişiminde yenilenmelidir.
   Metadata   : {'brand': 'DemoAuto', 'part_group': 'engine'}
--------------------------------------------------------------------------------
4. Skor       : 0.7681
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-SHELL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_shell_helix_ultra_5w_40.jpeg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Shell helix ultra 5w-40 marka.
   Metadata   : {'brand': 'SHELL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
5. Skor       : 0.7673
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-CASTROL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_castrol_magnetic.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Castrol Magnetic 5w-30 marka.
   Metadata   : {'brand': 'CASTROL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: ENGINE-OIL-CASTROL ürün kodlu parça

Sonuçlar:

1. Skor       : 1.0000
   Match      : exact_product_code
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-CASTROL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_castrol_magnetic.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Castrol Magnetic 5w-30 marka.
   Metadata   : {'brand': 'CASTROL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: Castrol motor yağı görselini getir

Sonuçlar:

1. Skor       : 0.8378
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-CASTROL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_castrol_magnetic.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Castrol Magnetic 5w-30 marka.
   Metadata   : {'brand': 'CASTROL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
2. Skor       : 0.8312
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-TOTAL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_total_quartz_5w_40.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Total Quartz 5w-40 marka.
   Metadata   : {'brand': 'TOTAL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
3. Skor       : 0.8296
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-PPLUS
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_performance_plus_5w_20.jpg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Performance Plus 5w-20 marka.
   Metadata   : {'brand': 'PERFORMANCE PLUS', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
4. Skor       : 0.8273
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Motor yağı görseli
   Kategori   : motor_yagi_gorsel
   Ürün kodu  : ENGINE-OIL-SHELL
   Kaynak     : motor_yag_gorsel_katalogu
   Görsel     : images/engine_oil_shell_helix_ultra_5w_40.jpeg
   İçerik     : Motor yağı, motorun iç parçalarını yağlayarak sürtünmeden kaynaklı aşınmayı önleyen ve motor ömrünü uzatan koruyucu sıvıdır. Shell helix ultra 5w-40 marka.
   Metadata   : {'brand': 'SHELL', 'part_group': 'engine_system'}
--------------------------------------------------------------------------------
5. Skor       : 0.7879
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-OSIMCO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_osimco_honda_civic_fc5_front.png
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'OSIMCO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: BOSCH akü görseli

Sonuçlar:

1. Skor       : 0.7738
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-OSIMCO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_osimco_honda_civic_fc5_front.png
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'OSIMCO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
2. Skor       : 0.7708
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BOSCH-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_bosch_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BOSCH', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
3. Skor       : 0.7696
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-SBS-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_sbs_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'SBS', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
4. Skor       : 0.7594
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BREMBO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_brembo_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça.Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BREMBO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
5. Skor       : 0.7307
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Araç Aküsü Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BAT-12V-PWRLN
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/car_battery_powerline.webp
   İçerik     : 12V araç aküsü, otomotiv marş sistemi ve elektrik besleme parçası.
   Metadata   : {'brand': 'POWERLINE', 'part_group': 'battery', 'voltage': '12V'}
--------------------------------------------------------------------------------

================================================================================
Sorgu: Honda civic fc5 ön fren balatası

Sonuçlar:

1. Skor       : 0.8452
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-SBS-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_sbs_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'SBS', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
2. Skor       : 0.8440
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-OSIMCO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_osimco_honda_civic_fc5_front.png
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'OSIMCO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
3. Skor       : 0.8396
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BOSCH-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_bosch_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça. Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BOSCH', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
4. Skor       : 0.8392
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : image
   Başlık     : Fren Balatası Görseli
   Kategori   : yedek_parca_gorsel
   Ürün kodu  : BRK-PAD-FRONT-BREMBO-FC5
   Kaynak     : parca_gorsel_katalogu
   Görsel     : images/brake_pad_brembo_honda_civic_fc5_front.jpg
   İçerik     : Ön fren balatası, disk fren sistemi için kullanılan yedek parça.Honda civic fc5 kasa uyumlu.
   Metadata   : {'brand': 'BREMBO', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
5. Skor       : 0.7707
   Match      : semantic_faiss
   Vector Tip : text
   Tip        : text
   Başlık     : Fren Balatası Arıza Belirtileri
   Kategori   : teknik_bilgi
   Ürün kodu  : BRK-PAD-INFO
   Kaynak     : teknik_bilgi_bankasi
   Görsel     : None
   İçerik     : Fren balatası aşınması durumunda frenleme sırasında ötme sesi, fren mesafesinde uzama, pedalda sertleşme veya direksiyonda titreşim görülebilir. Balata kalınlığı kritik seviyeye düştüğünde balata değişimi yapılmalıdır.
   Metadata   : {'brand': 'DemoAuto', 'part_group': 'brake_system'}
--------------------------------------------------------------------------------
(.llmproject_env) user@user:~/ahmet-ai/faiss_sqlite_automotive$



'''