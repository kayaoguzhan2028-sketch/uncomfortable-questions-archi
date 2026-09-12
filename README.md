# Mimarlıkta Rahatsız Edici Sorular — arşiv sitesi

2024'te Ankara'da kurulan bağımsız kolektifin etkinlik ve üretim arşivi.
62 etkinlik, 66 üretim; her biri kendi sayfası.

Yayında: https://kayaoguzhan2028-sketch.github.io/uncomfortable-questions-archi/

Statik site — derleme adımı, bağımlılık, sunucu yok. GitHub Pages doğrudan
`main` dalını yayınlıyor.

---

## Klasör yapısı

Her kaydın malzemesi tek klasörde: metni, fotoğrafları ve sayfası bir arada.

Site iki dilde: `tr/` ve `en/`. Kayıtların **malzemesi** ise dilden bağımsız,
tek kopya, `kayit/` altında — fotoğraf iki dilde de aynı, repoda iki kere
durmasın diye.

```
index.html                 dil seçer, tr/ ya da en/'e yönlendirir
main.style.css             sitenin TEK stil dosyası
main.js                    sitenin TEK script dosyası
ikon.svg                   soru işareti — favicon
favicon.ico                SVG okumayan tarayıcılar için yedek (üretilir)
apple-touch-icon.png       iOS ana ekran ikonu (üretilir)

tr/                        Türkçe sayfa ağacı    ┐
  index.html               ana sayfa             │ ÜRETİLİR,
  activity.html            etkinlik arşivi       │ elle düzenlenmez
  archive.html             üretim arşivi         │
  contact.html             iletişim              │
  activity/<slug>.html     tek etkinlik sayfası  │
  archive/<slug>.html      tek üretim sayfası    │
en/                        aynısının İngilizcesi ┘

kayit/                     kayıtların malzemesi (dilden bağımsız)
  etkinlikler/
    2026-1-mayis-tandogan/
      ├── yazi.md          sayfanın metni (kaynak)
      ├── kapak.webp       siteye giren fotoğraflar
      └── ham/             ⛔ repoya girmez — ham fotoğraflar
  uretimler/
    2026-yas-hafiza-ve-mekan/

arac/                      yerel araçlar (siteye dahil değil)
```

Yayındaki dosya adları İngilizce, nav'daki sekmelerle aynı kelimeler.
`index.html` adı **sadece ana sayfada** zorunlu: sunucu bir klasör istendiğinde
onu servis ediyor. Diğerleri kendi adını taşıyor — bir editörde on tane
`index.html` açıkken hangisinin ne olduğu okunmuyordu.

Manifesto ve temalar ayrı sayfa **değil**, ana sayfanın bölümleri; nav onlara
çapa (`index.html#manifesto`) ile iniyor.

`tr/` ve `en/` altındaki her şey `arac/sayfa.py` çıktısıdır. Oradaki bir
dosyayı elle düzenleme — bir dahaki üretimde silinir. Metni değiştirmek için
`arac/sayfa.py` içindeki `METIN` sözlüğüne ya da `kayit/.../yazi.md`'ye bak.

Klasör adı `<yıl>-<kısaltılmış başlık>`. Sıralama klasör adından değil,
Excel'deki tarihten yapılıyor; o yüzden ada ay/gün yazmıyoruz.

Tarihi bilinmeyen 14 üretim `tarihsiz-` önekiyle duruyor. Tarih netleştikçe
Excel'den düzeltilip klasör yeniden adlandırılır.

---

## Repoya girmeyenler

| ne | neden |
|---|---|
| `Activity List.xlsx` | Ham veri kaynağı. Yerelde kalır, hiçbir koşulda pushlanmaz. |
| `ham/` klasörleri | Ham fotoğraflar. Sadece webp çıktısı repoya girer. |
| `__pycache__/` | Python'un derleme önbelleği. |

Bunlar `.gitignore`'da. `.claude/settings.json` ayrıca Google Drive'ın yazma
araçlarını (dosya oluşturma, üzerine yazma, silme, izin değiştirme) engelliyor
— arşiv klasörü kolektifin, yanlışlıkla bir şeye dokunulmasın diye.

---

## Dil

Kökteki `index.html` ziyaretçiyi yönlendirir. **IP'ye bakmıyor** — GitHub Pages
statik bir sunucu, ziyaretçinin nereden geldiğini bilmez ve bunu değiştiremeyiz.
Bakılan şey sırasıyla:

1. Daha önce TR/EN düğmesiyle yapılmış seçim (`localStorage`).
2. Tarayıcının dil ayarı (`navigator.language`). IP'den daha doğru: Berlin'deki
   Türk öğrenci Türkçe, Ankara'daki Erasmus öğrencisi İngilizce görür.
3. Hiçbiri yoksa Türkçe.

JavaScript kapalıysa kökte iki bağlantı görünür, site çalışmaya devam eder.

### Ne çevrildi, ne çevrilmedi

| ne | durum |
|---|---|
| Arayüz (nav, bölüm adları, form, footer) | Çevrildi — `METIN` sözlüğü |
| Giriş ve footer tanıtım paragrafı | Çevrildi, **kolektifin onayından geçmedi** |
| Manifesto, tema metinleri, 32 soru | **Çevrilmedi.** İngilizce sayfada Türkçe aslı, üstünde çeviri notuyla duruyor |
| Kayıt sayfaları (128 kayıt) | Çevrilmedi |

Manifesto ve sorular bilerek çevrilmedi: kolektifin kendi politik beyanı, bir
makine çevirisi kolektifin adı altında yayınlanmaz. İngilizcesi geldiğinde
`sayfa.py`'ye eklenecek.

---

## Fotoğraf eklemek

Ham fotoğrafı kaydın `kayit/.../ham/` klasörüne at, sonra:

```bash
python arac/webp.py           # yeni gelenleri çevir
python arac/webp.py --izle    # açık bırak, attığın fotoğraf anında çevrilsin
```

Webp bir üst klasörde, `index.html`'in yanında oluşur. Araç üç şeyi
kendiliğinden hallediyor:

- **Yön düzeltme** — telefon fotoğrafları EXIF'teki döndürme notu yüzünden
  sitede yan yatar; uygulanıp düzeltiliyor.
- **Metadata silme** — telefon fotoğrafları **GPS konumu** ve cihaz bilgisi
  taşır. Halka açık bir repoya girmesin diye sıyrılıyor.
- **Ad temizleme** — Türkçe karakter ve boşluklar URL'de sorun çıkarır;
  `Büyük Foto.JPG` → `buyuk-foto.webp`.

Galeri sırası dosya adına göre. Sırayı garantilemek için ham dosyaları
`01_`, `02_` diye adlandır.

---

## Araçlar

| araç | ne yapar |
|---|---|
| `arac/veri.py` | Excel'i okur ve temizler. Diğer araçlar Excel'e değil buraya bakar. |
| `arac/iskele.py` | Eksik kayıt klasörlerini açar. Var olan `yazi.md`'yi **ezmez**. |
| `arac/webp.py` | `ham/` içindeki fotoğrafları webp'e çevirir. |
| `arac/favicon.py` | `ikon.svg`'den `favicon.ico` ve `apple-touch-icon.png` üretir. İkon değişirse tekrar çalıştır. |

`veri.py` Excel'in dağınıklığını tek yerde topluyor: tarihler beş ayrı
formatta yazılmış (`17.05.2024`, `2025-04-02`, `2025-06`, tarih aralıkları,
bir de ayrı sütunlarda), "Üretim Tipi" sütununa birkaç yerde tip yerine
aktivite ID'si sızmış, YouTube linkleri kendi sütununda değil "Aktivite Drive
Adı" sütununda `YT_link:` önekiyle duruyor.

---

## Sayfa yazmak

`yazi.md` sayfanın **kaynağı**, sayfanın kendisi değil. Orayı düzenleyince
site hemen değişmez.

Şu an sayfalar elle yazılıyor. Şablon oturduğunda `arac/sayfa.py` yazılacak
ve `yazi.md` + Excel verisi + klasördeki webp'lerden `index.html` üretecek.

---

## Stil

`main.style.css` sitenin tek stil dosyası. Sayfaların kendi `<style>` bloğu
**yok**; bir şey birden fazla sayfada görünüyorsa oraya yazılır.

Renk ve tipografi dosyanın başındaki `:root` bloğunda token olarak duruyor;
altındaki hiçbir kuralda çıplak renk yok. Siteyi beyaz zemine çevirmek yedi
satırlık bir değişiklik — nasıl yapılacağı o bloğun üstünde yazıyor.

Başlıklar CSS'te büyük harfe çevrilmiyor: `text-transform: uppercase`
Türkçe'de i/İ eşlemesini bozuyor ve bazı ekran okuyucular sonucu harf harf
okuyor. Büyük harfli görünen başlıklar metnin kendisinde öyle yazılı.

Video gömme sayfa açılırken yüklenmiyor — önce yerel kapak görseli duruyor,
ziyaretçi tıklayınca oynatıcı yerine geçiyor. Tıklanana kadar YouTube'a
hiçbir istek gitmiyor.

Site JavaScript olmadan da tam çalışır; `main.js` yalnızca video kapağını
oynatıcıya çeviriyor.

---

## Sürümleme (cache-busting)

Site GitHub Pages'te, önünde Cloudflare var. Pages her dosyaya
`Cache-Control: max-age=600` gönderiyor ve **bunu değiştiremiyoruz** — Pages
özel header kabul etmiyor, `.htaccess` çalışmıyor. O yüzden önbellek kırma
tamamen adresteki `?v=` damgası üzerine kurulu.

**Her push'tan önce çalıştır — sıra önemli:**

```bash
./bump-version.sh
git add -A
git commit -m "..."
git push
```

Damgayı basmadan commit edersen hiçbir işe yaramaz.

Script tüm `.html` dosyalarındaki yerel `<link href="*.css">` ve
`<script src="*.js">` etiketlerine `?v=YYYYMMDDHHMM` basar (varsa günceller),
damgayı `VERSION` dosyasına yazar. `https://` içeren satırlara dokunmaz — CDN
adresleri sürümü zaten yolunda taşır.

### ⚠ Görseller versiyonlanmıyor

Script **sadece** `.js` ve `.css` damgalar. **Aynı adla bir görseli
değiştirirsen ziyaretçiye eskisi gider.** Bir görselin içeriğini
değiştireceksen dosyayı yeniden adlandır (`kapak.webp` → `kapak-2.webp`) ve
sayfadaki bağlantıyı güncelle.

### Neden perl, neden sed değil

Git Bash'te `awk` satır sonlarını bozuyor — ama ölçtük, bu ortamdaki
GNU sed 4.9 de aynısını yapıyor:

```
CRLF satir sonlu bir dosyada, sadece ilk satiri degistiren komut:

  baslangic       ->  61 0d 0a 62 0d 0a
  sed -E -i       ->  41 0a    62 0a      CR (0d) her satirdan silindi
  perl -i -pe     ->  41 0d 0a 62 0d 0a   baytlar korundu
```

Çalışma kopyası CRLF olduğu için (`core.autocrlf=true`) bu, alakasız
dosyaların baştan aşağı değişmiş görünmesine yol açar. `perl -i -pe` aynı
testte baytları koruyor, o yüzden script perl kullanıyor.

`.gitattributes` ayrıca `*.sh` dosyalarını LF'e sabitliyor — shell script
CRLF ile checkout edilirse `#!/bin/sh` satırı kırılır.

---

## Yerelde çalıştırmak

```bash
python -m http.server 8765
```

Sayfaları dosyaya çift tıklayarak (`file://`) açma — gömülü video
oynatmaz, YouTube `http(s)` kaynağı ister.
