#!/usr/bin/env python3
"""Kayıtların çalışma tablosu: her kaydın neyi var, neyi eksik.

    python arac/durum.py            # ekrana özet + eksik listesi
    python arac/durum.py --csv      # durum.csv yazar, Excel'de açılır
    python arac/durum.py --json     # telefon listesinin verisini basar

NEDEN
    "Activity List.xlsx" ham veri kaynağı — 40 küsur sütun, dağınık.
    Kayıt kayıt ilerlerken lazım olan şey o değil: hangi kaydın metni
    yazılmış, hangisinin fotoğrafı ayıklanmış, hangisi hiç ellenmemiş.
    Bu tablo onu veriyor.

    durum.csv REPOYA GİRMEZ, üretilen bir çalışma kağıdı. Excel'i
    düzenleme — kaynak orası; buradaki tablo ondan türüyor.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import veri

KOK = Path(__file__).resolve().parent.parent

BASLIKLAR = ["sira", "tur", "klasor", "baslik", "tarih", "yer", "tip",
             "tema", "video", "yazi", "foto", "ham", "durum"]


def bos_mu(md: Path) -> bool:
    """yazi.md'de başlık ve yorum bloğu dışında bir şey var mı.

    İskele her dosyaya bir '# Başlık' ve bir açıklama yorumu yazıyor;
    dosya var diye metin yazılmış sayılmaz."""
    if not md.exists():
        return True
    govde = []
    metin = md.read_text(encoding="utf-8")
    # yorum bloklarını at
    while "<!--" in metin and "-->" in metin:
        bas = metin.index("<!--")
        metin = metin[:bas] + metin[metin.index("-->", bas) + 3:]
    for satir in metin.splitlines():
        s = satir.strip()
        if s and not s.startswith("#"):
            govde.append(s)
    return not govde


def satir(i: int, k) -> dict:
    klasor = KOK / k.kaynak
    foto = sorted(p.name for p in klasor.glob("*.webp")) if klasor.exists() else []
    ham = list((klasor / "ham").glob("*")) if (klasor / "ham").exists() else []
    ham = [p for p in ham if p.is_file() and p.name != ".gitkeep"]
    yazi = not bos_mu(klasor / "yazi.md")

    if yazi and foto:
        durum = "tamam"
        if "kapak.webp" not in foto:
            durum = "kapak yok"
    elif yazi:
        durum = "foto yok"
    elif foto:
        durum = "yazi yok"
    elif ham:
        durum = "ham var, cevrilmemis"
    else:
        durum = "bos"

    return {
        "sira": i,
        "tur": k.tur,
        "klasor": k.klasor.as_posix(),
        "baslik": k.baslik,
        "tarih": k.tarih.yazi(),
        "yer": ", ".join(x for x in (k.sehir, k.mekan) if x) or k.yazar,
        "tip": " / ".join(k.tipler),
        "tema": " / ".join(k.temalar),
        "video": k.video or "",
        "yazi": "var" if yazi else "",
        "foto": len(foto),
        "ham": len(ham),
        "durum": durum,
    }


def main():
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--csv", action="store_true", help="durum.csv yaz")
    a.add_argument("--json", action="store_true",
                   help="satirlari JSON basar (telefon listesi bunu gomuyor)")
    a.add_argument("--tur", choices=["etkinlik", "uretim"], help="sadece bu tür")
    s = a.parse_args()

    ev, pr = veri.oku()
    kayitlar = {"etkinlik": ev, "uretim": pr}.get(s.tur) or (ev + pr)
    satirlar = [satir(i, k) for i, k in enumerate(kayitlar, 1)]

    if s.json:
        print(json.dumps(satirlar, ensure_ascii=False, indent=0))
        return

    if s.csv:
        # utf-8-sig: BOM olmadan Excel Türkçe karakterleri bozuyor.
        hedef = KOK / "durum.csv"
        with hedef.open("w", encoding="utf-8-sig", newline="") as f:
            y = csv.DictWriter(f, BASLIKLAR, delimiter=";")
            y.writeheader()
            y.writerows(satirlar)
        print(f"  + durum.csv  ({len(satirlar)} satır)")
        return

    sayim = {}
    for r in satirlar:
        sayim[r["durum"]] = sayim.get(r["durum"], 0) + 1

    print(f"\n{len(satirlar)} kayıt\n")
    for d, n in sorted(sayim.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {d}")

    print("\nElle tutulacaklar (metni ya da fotoğrafı olan):\n")
    for r in satirlar:
        if r["durum"] != "bos":
            print(f'  {r["durum"]:<22} {r["klasor"]}')

    print("\nTabloyu Excel'de açmak için:  python arac/durum.py --csv")


if __name__ == "__main__":
    main()
