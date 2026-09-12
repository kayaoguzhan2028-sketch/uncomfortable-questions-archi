#!/usr/bin/env python3
"""ikon.svg'den favicon.ico ve apple-touch-icon.png üretir.

    python arac/favicon.py

NEDEN
    Sayfalar ikon.svg'yi favicon olarak veriyor ve modern tarayıcılarda
    bu yeterli. Ama SVG favicon'u okumayan yerler var: eski Safari,
    bazı RSS okuyucular, link önizlemesi çıkaran kazıyıcılar. Onlar
    kök dizinde favicon.ico arar, bulamazsa boş kutu gösterir.

    O yüzden ICO'yu SVG'den ÜRETİYORUZ, elle çizmiyoruz: ikon değişirse
    bu script tekrar çalıştırılır ve ikisi asla ayrı düşmez.

ŞEKİL
    ikon.svg'deki yolun aynısı — blok soru işareti, eğri yok, hepsi dik
    açı. Koordinatlar 24x32'lik kutuda; kare ikona ortalanıyor.
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow kurulu değil. Kur:  python -m pip install Pillow")

KOK = Path(__file__).resolve().parent.parent

# ikon.svg'deki path ile birebir aynı. Değiştirirsen ikisini birlikte değiştir.
GOVDE = [(0, 0), (24, 0), (24, 23), (15, 23), (15, 26), (9, 26),
         (9, 17), (18, 17), (18, 7), (7, 7), (7, 13), (0, 13)]
NOKTA = (9, 29, 15, 32)          # sol, üst, sağ, alt
KUTU_EN, KUTU_BOY = 24, 32

SIYAH = (12, 12, 12, 255)
SEFFAF = (0, 0, 0, 0)

# ICO içine birden fazla boy koyuyoruz: sekme 16, kısayol 32, bazı yerler 48.
ICO_BOYLAR = [16, 32, 48]
DOKUNMA_BOY = 180                # apple-touch-icon — iOS ana ekran


def ciz(boy: int) -> Image.Image:
    """Kare, saydam zeminli ikon. İşaret ortalanır, kenarda pay bırakılır."""
    # 4 kat büyük çizip küçültüyoruz: kenarlar yumuşasın (kendi anti-aliasing'imiz,
    # çünkü ImageDraw.polygon kenar yumuşatma yapmaz).
    kat = 4
    tuval = Image.new("RGBA", (boy * kat, boy * kat), SEFFAF)
    d = ImageDraw.Draw(tuval)

    pay = 0.12                                    # kenar payı
    ic = boy * kat * (1 - 2 * pay)
    olcek = ic / KUTU_BOY                         # yükseklik sığdırır
    dx = (boy * kat - KUTU_EN * olcek) / 2        # yatayda ortala
    dy = (boy * kat - KUTU_BOY * olcek) / 2

    d.polygon([(dx + x * olcek, dy + y * olcek) for x, y in GOVDE], fill=SIYAH)
    sol, ust, sag, alt = NOKTA
    d.rectangle([dx + sol * olcek, dy + ust * olcek,
                 dx + sag * olcek, dy + alt * olcek], fill=SIYAH)

    return tuval.resize((boy, boy), Image.LANCZOS)


def main():
    ico = KOK / "favicon.ico"
    ciz(max(ICO_BOYLAR)).save(ico, format="ICO",
                              sizes=[(b, b) for b in ICO_BOYLAR])
    print(f"  + favicon.ico        ({ico.stat().st_size:,} bayt, "
          f"{'/'.join(str(b) for b in ICO_BOYLAR)} px)")

    png = KOK / "apple-touch-icon.png"
    # iOS saydamlığı siyaha boyar; beyaz zemin veriyoruz.
    kare = Image.new("RGBA", (DOKUNMA_BOY, DOKUNMA_BOY), (255, 255, 255, 255))
    kare.alpha_composite(ciz(DOKUNMA_BOY))
    kare.convert("RGB").save(png, format="PNG", optimize=True)
    print(f"  + apple-touch-icon.png ({png.stat().st_size:,} bayt, "
          f"{DOKUNMA_BOY}px)")


if __name__ == "__main__":
    main()
