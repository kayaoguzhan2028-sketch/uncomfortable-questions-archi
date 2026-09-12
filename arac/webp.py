#!/usr/bin/env python3
"""
Fotoğrafları webp'e çeviren araç.

NE YAPAR
--------
Her kaydın kendi klasöründe bir 'ham/' alt klasörü var. Oraya ne atarsan
webp'i bir üst klasörde, index.html'in yanında oluşur.

    etkinlikler/2024/05-17-mimarlik-ogrencileri-deneme-toplantisi/
    ├── ham/                      ⛔ .gitignore'da — repoya girmez
    │   ├── IMG_4821.JPG              ham fotoğrafları BURAYA at
    │   └── 02 ikinci kare.png
    ├── img-4821.webp             ← script üretir, siteye bunlar girer
    ├── 02-ikinci-kare.webp
    └── yazi.md

Ham fotoğraf repoya hiç girmez; sadece webp'ler girer.

KULLANIM
--------
    python arac/webp.py              # yeni/değişmiş fotoğrafları çevir
    python arac/webp.py --izle       # açık bırak, gelen fotoğrafı anında çevir
    python arac/webp.py --zorla      # hepsini baştan çevir
    python arac/webp.py --kalite 90  # daha yüksek kalite (varsayılan 82)

NOTLAR
------
- Telefon fotoğraflarının yan yatması düzeltilir (EXIF yönü uygulanır).
- EXIF SİLİNİR. Önemli: telefon fotoğrafları GPS konumu ve cihaz bilgisi
  taşır; bunlar halka açık bir repoya girmemeli.
- Dosya adları URL'e uygun hale getirilir (Türkçe karakter, boşluk temizlenir).
- Galeri sırası dosya adına göre. Sırayı garantilemek için ham dosyaları
  01_, 02_, 03_ diye adlandır.
- Aynı fotoğrafı iki kez çevirmez; kaynak değişmedikçe atlar.
"""

import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow kurulu değil. Kur:  python -m pip install Pillow")

KOK = Path(__file__).resolve().parent.parent
# Kayıt malzemesi kayit/ altında, dilden bağımsız (bkz. veri.py Kayit.kaynak)
BOLUMLER = ("kayit/etkinlikler", "kayit/uretimler")
HAM = "ham"

UZANTILAR = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

# Sitede bir fotoğraf bundan geniş gösterilmiyor. Retina ekranda bile 2000px
# fazlasıyla yeterli; üstü sadece dosya boyutu demek.
MAKS_KENAR = 2000

TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slug(metin: str) -> str:
    metin = metin.translate(TR)
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    metin = re.sub(r"[^a-zA-Z0-9]+", "-", metin).strip("-").lower()
    return metin or "isimsiz"


def cevir(kaynak: Path, hedef: Path, kalite: int, maks: int) -> tuple[int, int]:
    with Image.open(kaynak) as im:
        # Telefonlar fotoğrafı düz kaydedip "şu kadar döndür" diye not düşer.
        # Uygulamazsak fotoğraflar sitede yan yatar.
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")

        if max(im.size) > maks:
            im.thumbnail((maks, maks), Image.LANCZOS)

        hedef.parent.mkdir(parents=True, exist_ok=True)
        # exif/icc aktarmıyoruz — metadata sıyrılsın (konum bilgisi vs.)
        im.save(hedef, "WEBP", quality=kalite, method=6)

    return kaynak.stat().st_size, hedef.stat().st_size


def ham_klasorler() -> list[Path]:
    """Tüm kayıt klasörlerindeki ham/ alt klasörlerini bulur."""
    bulunan = []
    for bolum in BOLUMLER:
        kok = KOK / bolum
        if kok.exists():
            bulunan.extend(sorted(d for d in kok.rglob(HAM) if d.is_dir()))
    return bulunan


def tara(kalite: int, maks: int, zorla: bool, sessiz: bool = False) -> int:
    klasorler = ham_klasorler()
    if not klasorler and not sessiz:
        print("Hiç 'ham/' klasörü yok. Ham fotoğrafları bir kaydın ham/ "
              "klasörüne at, sonra tekrar çalıştır.")
        return 0

    cevrilen = atlanan = hatali = 0
    ham_top = web_top = 0

    for ham_dizin in klasorler:
        hedef_dizin = ham_dizin.parent          # kaydın kendi klasörü
        for kaynak in sorted(ham_dizin.iterdir()):
            if not kaynak.is_file():
                continue

            if kaynak.suffix.lower() in {".heic", ".heif"}:
                if not sessiz:
                    print(f"  ! {kaynak.name} — HEIC okunamıyor. "
                          "Kur: python -m pip install pillow-heif")
                hatali += 1
                continue

            if kaynak.suffix.lower() not in UZANTILAR:
                continue

            hedef = hedef_dizin / (slug(kaynak.stem) + ".webp")

            if not zorla and hedef.exists() and hedef.stat().st_mtime >= kaynak.stat().st_mtime:
                atlanan += 1
                continue

            try:
                ham, web = cevir(kaynak, hedef, kalite, maks)
            except Exception as hata:
                print(f"  ! {kaynak.relative_to(KOK)} — çevrilemedi: {hata}")
                hatali += 1
                continue

            ham_top += ham
            web_top += web
            cevrilen += 1
            if not sessiz:
                print(f"  + {hedef.relative_to(KOK)}  ({ham//1024} KB -> {web//1024} KB)")

    if cevrilen and not sessiz:
        kazanc = 100 - (web_top * 100 // max(ham_top, 1))
        print(f"\n{cevrilen} fotoğraf çevrildi, %{kazanc} küçüldü.")
    if atlanan and not sessiz:
        print(f"{atlanan} fotoğraf zaten güncel, atlandı.")
    if hatali:
        print(f"{hatali} dosya çevrilemedi.")

    return cevrilen


def main() -> None:
    p = argparse.ArgumentParser(description="Fotoğrafları webp'e çevirir.")
    p.add_argument("--izle", action="store_true",
                   help="arka planda bekle, yeni fotoğraf geldikçe çevir")
    p.add_argument("--zorla", action="store_true", help="hepsini baştan çevir")
    p.add_argument("--kalite", type=int, default=82, help="webp kalitesi (varsayılan 82)")
    p.add_argument("--maks", type=int, default=MAKS_KENAR,
                   help=f"en uzun kenar, piksel (varsayılan {MAKS_KENAR})")
    a = p.parse_args()

    if a.izle:
        print("İzleniyor: tüm ham/ klasörleri  (durdurmak için Ctrl+C)")
        tara(a.kalite, a.maks, a.zorla)
        try:
            while True:
                time.sleep(3)
                tara(a.kalite, a.maks, False)
        except KeyboardInterrupt:
            print("\nDurduruldu.")
    else:
        tara(a.kalite, a.maks, a.zorla)


if __name__ == "__main__":
    main()
