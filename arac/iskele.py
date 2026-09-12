#!/usr/bin/env python3
"""
Excel'deki her kayıt için bir klasör açar.

    etkinlikler/2024/05-17-mimarlik-ogrencileri-deneme-toplantisi/
    ├── ham/         ham fotoğrafları buraya at (repoya girmez)
    └── yazi.md      kaydın metni — Drive'dan gelen yazıyı buraya yapıştır

index.html'i bu script üretmez; onu sayfa şablonu netleşince sayfa.py yapacak.

GÜVENLİ: var olan hiçbir dosyanın üstüne yazmaz. Sen yazi.md'yi doldurduktan
sonra tekrar çalıştırabilirsin, yazdıklarına dokunmaz.

    python arac/iskele.py            # eksik klasörleri aç
    python arac/iskele.py --listele  # hiçbir şey oluşturma, ne yapacağını göster
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from veri import KOK, Kayit, oku       # noqa: E402


TASLAK = """\
{baslik}

<!-- ---------------------------------------------------------------------
  {kunye}

  Yukarıdaki künye Excel'den geliyor ve sayfaya OTOMATİK yazılıyor; burada
  tekrar yazmana gerek yok. Bu dosyaya sadece kaydın METNİNİ yaz.

  Fotoğraflar: ham fotoğrafları bu klasördeki ham/ içine at, sonra
  `python arac/webp.py` çalıştır. Webp'ler bu klasörde oluşur ve sayfaya
  kendiliğinden dizilir. Sıra dosya adına göre — sırayı garantilemek için
  ham dosyaları 01_, 02_ diye adlandır.

  NOT: Bu dosya sayfanın KAYNAĞI, sayfanın kendisi değil. Burayı düzenleyince
  site hemen değişmez; `python arac/sayfa.py` çalıştırmak gerekir.
---------------------------------------------------------------------- -->

"""


def kunye(k: Kayit) -> str:
    parcalar = [k.tarih.yazi()]
    if k.tur == "etkinlik":
        parcalar += [p for p in (k.sehir, k.mekan) if p and p != "-"]
    else:
        parcalar += [p for p in (k.yazar, k.dil) if p]
    if k.tipler:
        parcalar.append(" / ".join(k.tipler))
    return "  ·  ".join(parcalar)


def kur(kayitlar: list[Kayit], listele: bool) -> tuple[int, int]:
    yeni = mevcut = 0
    for k in kayitlar:
        dizin = KOK / k.klasor
        yazi = dizin / "yazi.md"

        if yazi.exists():
            mevcut += 1
            continue

        yeni += 1
        if listele:
            print(f"  + {k.klasor}")
            continue

        (dizin / "ham").mkdir(parents=True, exist_ok=True)
        yazi.write_text(
            TASLAK.format(baslik=f"# {k.baslik}", kunye=kunye(k)),
            encoding="utf-8",
        )
        # ham/ boşken git'te görünmesi için
        (dizin / "ham" / ".gitkeep").touch()

    return yeni, mevcut


def main() -> None:
    p = argparse.ArgumentParser(description="Kayıt klasörlerini açar.")
    p.add_argument("--listele", action="store_true",
                   help="hiçbir şey oluşturma, ne yapılacağını göster")
    a = p.parse_args()

    etkinlikler, uretimler = oku()

    for ad, grup in (("ETKİNLİKLER", etkinlikler), ("ÜRETİMLER", uretimler)):
        print(f"\n=== {ad} ({len(grup)}) ===")
        yeni, mevcut = kur(grup, a.listele)
        if a.listele:
            print(f"  -> {yeni} klasör açılacak, {mevcut} zaten var")
        else:
            print(f"  {yeni} klasör açıldı, {mevcut} zaten vardı")

    if not a.listele:
        print("\nSıradaki adım: bir kaydın yazi.md'sini doldur, ham/ içine "
              "fotoğraf at, `python arac/webp.py` çalıştır.")


if __name__ == "__main__":
    main()
