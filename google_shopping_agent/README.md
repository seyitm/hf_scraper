# Google Shopping Agent for HarbiFırsat

Google Shopping üzerinden indirimli ürünleri arayıp HarbiFırsat platformuna admin onayı için gönderen bir agent.

## Özellikler

- 🔍 **Google Shopping Arama**: SERP API ile indirimli ürün arama
- 💰 **İndirim Filtreleme**: Minimum indirim yüzdesi belirleme
- 🏷️ **Popüler Aramalar**: Supabase'deki en çok alarm kurulan keyword'ler
- ✅ **Ürün Seçimi**: Listeden ürün seçip admin onayına gönderme
- 📊 **Sıralama & Filtreleme**: Fiyat, indirim, rating'e göre sıralama
- 📥 **Export**: CSV, Excel, JSON formatlarında dışa aktarma

## Kurulum

1. Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

2. `.env` dosyası oluşturun:

```bash
cp .env.example .env
```

3. API anahtarlarınızı ekleyin:

```env
SERP_API_KEY=your_serp_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

## Kullanım

### Streamlit Web Arayüzü (Önerilen)

```bash
streamlit run streamlit_app.py
```

Web arayüzünde:
1. Sidebar'dan SERP API ve Supabase bilgilerini girin
2. Arama yapın veya popüler aramalardan seçin
3. Sonuçları filtreleyin ve sıralayın
4. İstediğiniz ürünleri seçin
5. "Seçilenleri Onaya Gönder" ile Supabase'e gönderin

### Komut Satırı

```bash
# Temel çalıştırma
python run.py

# Belirli keyword arama
python run.py --keyword "iPhone 15" --min-discount 15

# Dry run (database'e yazmadan)
python run.py --dry-run
```

## Dosya Yapısı

```
google_shopping_agent/
├── streamlit_app.py      # Web arayüzü
├── agent.py              # Ana agent mantığı
├── serp_api_client.py    # SERP API istemcisi
├── supabase_client.py    # Supabase istemcisi
├── models.py             # Veri modelleri
├── config.py             # Konfigürasyon
├── run.py                # CLI çalıştırıcı
└── requirements.txt      # Bağımlılıklar
```

## Supabase Fonksiyonları

Popüler aramaları çekmek için Supabase'de `get_popular_keywords` fonksiyonu kullanılır:

```sql
-- Bu fonksiyon zaten migration ile oluşturuldu
SELECT * FROM get_popular_keywords(6);
```

## Lisans

MIT License
