# Sinyal Botu Kurulumu (Telegram Bildirimli)

Bu bot, bilgisayarın kapalı olsa bile GitHub'ın sunucularında 7/24 çalışır,
her 5 dakikada bir fiyatı kontrol eder, sinyal çıktığında Telegram'a
bildirim gönderir.

Kurulum yaklaşık 10-15 dakika sürer, kod yazmana gerek yok.

## 1. Adım: Telegram Botu Oluştur

1. Telegram'da **@BotFather** hesabını bul, "Başlat" (Start) de.
2. `/newbot` yaz, gönder.
3. Botuna bir isim ver (örnek: `Kripto Sinyal Botum`).
4. Botuna bir kullanıcı adı ver, sonu `bot` ile bitmeli (örnek: `kriptosinyal_benim_bot`).
5. BotFather sana uzun bir **token** verecek, şuna benzer:
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   Bunu bir kenara not et — **TELEGRAM_BOT_TOKEN** olacak.

## 2. Adım: Chat ID'ni Öğren

1. Az önce oluşturduğun botu Telegram'da bul, "Başlat" de (ona herhangi bir mesaj at, örnek: "merhaba").
2. Tarayıcında şu adrese git (TOKEN yerine kendi tokenını yaz):
   `https://api.telegram.org/botTOKEN/getUpdates`
3. Çıkan sayfada `"chat":{"id":123456789,...` gibi bir kısım göreceksin.
   O sayı senin **TELEGRAM_CHAT_ID**'in.

## 3. Adım: GitHub Reposu Oluştur

1. [github.com](https://github.com) üzerinde ücretsiz bir hesap aç (yoksa).
2. Sağ üstten "New repository" ile yeni bir repo oluştur (örnek isim: `sinyal-botum`).
   **Public** (herkese açık) seç — ücretsiz kullanım limiti bu şekilde sınırsız oluyor.
3. Bu klasördeki tüm dosyaları (bu `README.md`, `signal_bot.py`, `requirements.txt`,
   ve `.github/workflows/sinyal-kontrol.yml`) o reponun içine yükle
   (GitHub'ın web arayüzünden "Add file" > "Upload files" ile sürükle-bırak yapabilirsin,
   `.github` klasör yapısının bozulmadığından emin ol).

## 4. Adım: Secrets (Gizli Bilgiler) Ekle

1. Repo sayfasında **Settings** > **Secrets and variables** > **Actions** yoluna git.
2. "New repository secret" ile iki tane gizli bilgi ekle:
   - İsim: `TELEGRAM_BOT_TOKEN` → değer: 1. adımda aldığın token
   - İsim: `TELEGRAM_CHAT_ID` → değer: 2. adımda bulduğun chat id

## 5. Adım: Çalıştığını Test Et

1. Repo sayfasında **Actions** sekmesine git.
2. "Sinyal Kontrolü" workflow'unu seç, sağdan **"Run workflow"** butonuna bas
   (elle tetikleme — 15 dakika beklemene gerek yok).
3. Birkaç saniye sonra yeşil tik (✓) görmelisin. Tıklayıp loglara bakabilirsin.
4. Eğer o an bir sinyal varsa Telegram'a mesaj gelecek; yoksa "sinyal yok" gibi bir log göreceksin.
   Elle tetiklemene gerek kalmadan da artık her 5 dakikada bir otomatik çalışacak.

## Ayarları Değiştirmek İstersen

`signal_bot.py` dosyasının en üstünde şu değerler var:

- `SYMBOL` — hangi kripto parayı izleyeceği (örn. `ETHUSDT`)
- `OVERSOLD` / `OVERBOUGHT` — RSI eşikleri
- `SMA_LONG` — trend filtresi periyodu
- `SL_MULT` / `TP_MULT` — zarar-kes / kâr-al çarpanları

Şu anki değerler, tarayıcıdaki panelde "Ayarları Optimize Et" ile bulduğumuz
kombinasyona göre ayarlandı. Panelde farklı bir kombinasyon bulursan,
buradaki değerleri de ona göre güncelleyip GitHub'a tekrar yükleyebilirsin.

## Önemli Notlar

- Bu sistem **gerçek para hareket ettirmez**, sadece bildirim gönderir.
  Karar yine sana ait.
- Aynı sinyal sürerken (örneğin 3 saat boyunca RSI hâlâ düşükse) bot seni
  **tekrar tekrar** rahatsız etmez — sadece yeni bir sinyal başladığında bildirir.
- GitHub'ın ücretsiz planı, herkese açık (public) repolarda **sınırsız**
  çalışma süresi tanır, bu yüzden hiçbir ücret ödemene gerek yok.
- Zamanlama tam olarak 5 dakikada bir garanti değildir; GitHub yoğun
  saatlerde birkaç dakika gecikme yapabilir, bu normaldir.
