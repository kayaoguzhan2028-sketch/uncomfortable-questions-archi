#!/usr/bin/env python3
"""Gerçek fotoğraflar gelene kadar duracak yer tutucu görseller üretir.

    python arac/yertutucu.py

NEDEN
    Sayfadaki görsel kutuları boşken yerleşimi değerlendirmek zor: fotoğraf
    ne kadar yer kaplayacak, oran doğru mu, altındaki metin nereye düşüyor.
    Bu script o kutuları doldurur.

    Üretilen dosyalar GERÇEK İÇERİK DEĞİL ve öyle görünmesinler diye
    üzerlerinde ne oldukları ve hangi dosyanın beklendiği yazılı. Gerçek
    fotoğraf gelince aynı adla üzerine yazılır, başka hiçbir şey değişmez.
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow kurulu değil. Kur:  python -m pip install Pillow")

KOK = Path(__file__).resolve().parent.parent

ZEMIN = (226, 224, 220)
CIZGI = (188, 185, 180)
YAZI = (120, 116, 110)
ISARET = (206, 203, 198)

# (dosya, genişlik, yükseklik, üzerine yazılacak not)
ISTENENLER = [
    ("kolektif.webp", 1600, 900, "kolektif fotoğrafı"),
    ("sorular.webp", 1600, 900, "sorular bölümü fotoğrafı"),
]

# ikon.svg ile aynı koordinatlar — yer tutucu bile siteye ait görünsün.
GOVDE = [(0, 0), (24, 0), (24, 23), (15, 23), (15, 26), (9, 26),
         (9, 17), (18, 17), (18, 7), (7, 7), (7, 13), (0, 13)]
NOKTA = (9, 29, 15, 32)


def yazi_tipi(boy):
    for ad in ("arialbd.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(ad, boy)
        except OSError:
            continue
    return ImageFont.load_default()


def uret(dosya, en, boy, not_):
    g = Image.new("RGB", (en, boy), ZEMIN)
    d = ImageDraw.Draw(g)

    # Kesikli çerçeve — "burası henüz boş" demenin en okunur yolu
    adim, kalin = 24, 3
    for x in range(0, en, adim * 2):
        d.rectangle([x, 0, x + adim, kalin], fill=CIZGI)
        d.rectangle([x, boy - kalin, x + adim, boy], fill=CIZGI)
    for y in range(0, boy, adim * 2):
        d.rectangle([0, y, kalin, y + adim], fill=CIZGI)
        d.rectangle([en - kalin, y, en, y + adim], fill=CIZGI)

    # Soluk soru işareti
    olcek = boy * 0.42 / 32
    dx, dy = (en - 24 * olcek) / 2, (boy - 32 * olcek) / 2 - boy * 0.06
    d.polygon([(dx + x * olcek, dy + y * olcek) for x, y in GOVDE], fill=ISARET)
    sol, ust, sag, alt = NOKTA
    d.rectangle([dx + sol * olcek, dy + ust * olcek,
                 dx + sag * olcek, dy + alt * olcek], fill=ISARET)

    # Ne olduğu ve hangi dosyanın beklendiği — gerçek içerik sanılmasın
    f1, f2 = yazi_tipi(int(boy * 0.055)), yazi_tipi(int(boy * 0.038))
    for metin, f, ay in ((f"YER TUTUCU — {not_}", f1, 0.76),
                         (f"gerçek fotoğrafı {dosya} adıyla kök dizine koy",
                          f2, 0.845)):
        w = d.textbbox((0, 0), metin, font=f)[2]
        d.text(((en - w) / 2, boy * ay), metin, font=f, fill=YAZI)

    yol = KOK / dosya
    g.save(yol, format="WEBP", quality=80, method=6)
    print(f"  + {dosya}  ({yol.stat().st_size:,} bayt, {en}x{boy})")


def main():
    for dosya, en, boy, not_ in ISTENENLER:
        uret(dosya, en, boy, not_)
    print("\nGerçek fotoğraf gelince aynı adla üzerine yaz — sayfada başka\n"
          "hiçbir şey değişmiyor.")


if __name__ == "__main__":
    main()
