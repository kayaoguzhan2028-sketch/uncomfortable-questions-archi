#!/usr/bin/env python3
"""
Örneklem sayfalarını üretir: her sayfa tipi için bir örnek.

    python arac/orneklem.py            # görselleri dönüştür (eksikse), sayfaları yaz
    python arac/orneklem.py --yeniden  # görselleri de baştan dönüştür

Çıktı orneklem/ altına:
    index.html              örneklerin listesi
    fanzin.html  rapor.html  sunum.html  yazi.html  album.html  gorsel.html
    video.html   etkinlik-podcast.html  etkinlik-fotograf.html  etkinlik-video.html
    gorsel/<ad>/…webp       sayfaların kullandığı görseller (ham/ klasörlerinden)
    lib/                    StPageFlip ve Swiper — internetten çekilmez
    orneklem.css / .js      örneklemin ek stili ve scripti

Metin (başlık, özet, uzun yazı, tarih, temalar …) Excel'den geliyor, elle
yazılmıyor. Excel değişince bu script tekrar çalıştırılır.

Neden sayfa.py'nin içinde değil: bunlar sayfayı yapacak kişiye gösterilecek
ÖRNEKLER. Kalıp onaylanınca sayfa.py her kayıt için bu kalıpla üretir;
bu dosya o zaman silinebilir.

Gerekenler: pymupdf (PDF → görsel), ImageMagick `magick` (webp, HEIC),
PowerPoint (PPTX → görsel; sadece Windows, COM üzerinden).
"""

import argparse
import html
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from veri import KOK, Kayit, oku  # noqa: E402

CIKTI = KOK / "orneklem"
GORSEL = CIKTI / "gorsel"
KAYIT = KOK / "kayit"
e = html.escape

DIL_ADI = {"TR": "Türkçe", "EN": "İngilizce", "TR-EN": "Türkçe, İngilizce"}
YAZAR_ADI = {"UQA": "Mimarlıkta Rahatsız Edici Sorular"}
FOTO_UZANTI = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


# --------------------------------------------------------------------------
# GÖRSEL DÖNÜŞTÜRME — sonuç varsa atlanır (--yeniden ile baştan)
# --------------------------------------------------------------------------

YENIDEN = False


def _gerek(hedef: Path) -> bool:
    return YENIDEN or not hedef.exists()


def magick(kaynak: Path, hedef: Path, boyut: str = "1600x1600>", kalite: int = 78) -> Path:
    """Fotoğrafı webp'e çevirir. -auto-orient: telefon fotoğrafının yönü."""
    if _gerek(hedef):
        hedef.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["magick", str(kaynak), "-auto-orient", "-resize", boyut,
                        "-strip", "-quality", str(kalite), str(hedef)], check=True)
    return hedef


def pdf_sayfalari(pdf: Path, klasor: Path, en: int = 760) -> list[Path]:
    """PDF'in her sayfasını <klasor>/001.webp … olarak yazar."""
    import pymupdf
    klasor.mkdir(parents=True, exist_ok=True)
    belge = pymupdf.open(pdf)
    cikti = []
    for i, sayfa in enumerate(belge):
        hedef = klasor / f"{i + 1:03}.webp"
        if _gerek(hedef):
            dpi = en / (sayfa.rect.width / 72)
            gecici = klasor / f"{i + 1:03}.png"
            sayfa.get_pixmap(dpi=round(dpi * 1.02)).save(gecici)
            magick(gecici, hedef, f"{en}x", 74)
            gecici.unlink()
        cikti.append(hedef)
    return cikti


def pptx_slaytlari(pptx: Path, klasor: Path) -> list[Path]:
    """PowerPoint'e slaytları PNG olarak dışa aktartır, sonra webp'e çevirir."""
    klasor.mkdir(parents=True, exist_ok=True)
    hazir = sorted(klasor.glob("[0-9][0-9].webp"))
    if hazir and not YENIDEN:
        return hazir
    gecici = klasor / "_png"
    gecici.mkdir(exist_ok=True)
    # Yollar ortam değişkeniyle geçiyor: "UNQİA" gibi Türkçe karakter
    # komut satırında bozulmasın.
    betik = ("$pp = New-Object -ComObject PowerPoint.Application; "
             "$p = $pp.Presentations.Open($env:KAYNAK, $true, $false, $false); "
             "$p.Export($env:HEDEF, 'PNG', 1920, 1080); $p.Close(); $pp.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", betik], check=True,
                   env={**os.environ, "KAYNAK": str(pptx), "HEDEF": str(gecici)})
    pngler = sorted(gecici.glob("*.PNG"), key=lambda p: int(re.sub(r"\D", "", p.stem)))
    cikti = []
    for i, png in enumerate(pngler):
        cikti.append(magick(png, klasor / f"{i + 1:02}.webp", "1600x", 80))
        magick(png, klasor / "kucuk" / f"{i + 1:02}.webp", "320x", 70)
        png.unlink()
    gecici.rmdir()
    return cikti


def youtube_kapak(kimlik: str, hedef: Path) -> Path:
    """Video kapağını yerel kopya olarak indirir: sayfa açılırken YouTube'a
    istek gitmesin (main.js'teki video kararıyla aynı)."""
    if _gerek(hedef):
        hedef.parent.mkdir(parents=True, exist_ok=True)
        gecici = hedef.with_suffix(".jpg")
        for boy in ("maxresdefault", "hqdefault"):
            try:
                urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{kimlik}/{boy}.jpg", gecici)
                break
            except OSError:
                continue
        magick(gecici, hedef, "1280x", 80)
        gecici.unlink()
    return hedef


def ham(k: Kayit) -> list[Path]:
    kok = KAYIT / k.klasor / "ham"
    return sorted(p for p in kok.rglob("*") if p.is_file() and p.name != ".gitkeep")


def olcu(webp: Path) -> tuple[int, int]:
    cikti = subprocess.run(["magick", "identify", "-format", "%w %h", str(webp)],
                           capture_output=True, text=True, check=True).stdout
    en, boy = cikti.split()
    return int(en), int(boy)


# --------------------------------------------------------------------------
# SAYFA PARÇALARI
# --------------------------------------------------------------------------

def _sablon():
    """Üst nav ve footer: yayındaki sayfadan alınıyor, elle kopyalanmıyor."""
    kaynak = (KOK / "tr/archive/2026-yas-hafiza-ve-mekan.html").read_text(encoding="utf-8")
    ust = kaynak[kaynak.index('<header class="ust kutu">'):kaynak.index("<main")]
    alt = kaynak[kaynak.index('<footer class="alt kutu">'):kaynak.index("<script")]
    surum = re.search(r"main\.style\.css\?v=(\d+)", kaynak).group(1)
    return ust.replace("../../", "../"), alt.replace("../../", "../"), surum


UST, ALT, SURUM = _sablon()


def ust_nav(bolum: str) -> str:
    """Nav'da aktif sekme: üretimde arşiv, etkinlikte etkinlikler."""
    nav = UST.replace(' aria-current="page"', "")
    capa = "#archive" if bolum == "uretim" else "#activity"
    return nav.replace(f'index.html{capa}">', f'index.html{capa}" aria-current="page">', 1)


def sayfa(dosya: str, baslik: str, ozet: str, serit: str, govde: str, bolum: str = "uretim",
          swiper: bool = False, pageflip: bool = False) -> None:
    css = '<link rel="stylesheet" href="lib/swiper-bundle.min.css">\n' if swiper else ""
    js = ""
    if pageflip:
        js += '<script src="lib/page-flip.browser.js"></script>\n'
    if swiper:
        js += '<script src="lib/swiper-bundle.min.js"></script>\n'
    metin = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(baslik)} — Mimarlıkta Rahatsız Edici Sorular</title>
<meta name="description" content="{e(ozet)}">
<link rel="icon" href="../ikon.svg" type="image/svg+xml">
<link rel="icon" href="../favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="stylesheet" href="../main.style.css?v={SURUM}">
{css}<link rel="stylesheet" href="orneklem.css">
</head>
<body class="kayit">
<div class="orneklem-serit">
  <span><strong>ÖRNEKLEM</strong> · {serit} · <a href="index.html">tüm örnekler</a></span>
  <button type="button" data-alan-dugme aria-pressed="false">Excel sütunlarını göster</button>
</div>
{ust_nav(bolum)}<main class="wrap">
  <article>
{govde}
  </article>
</main>

{ALT}<script src="../main.js?v={SURUM}"></script>
{js}<script src="orneklem.js"></script>
</body>
</html>
"""
    (CIKTI / dosya).write_text(metin, encoding="utf-8")
    print(f"  yazıldı  orneklem/{dosya}")


def post_head(k: Kayit, label: str, h1: str | None = None, meta: str | None = None,
              label_alan: str = "D · Üretim Tipi") -> str:
    h1 = h1 or k.baslik
    if meta is None:
        meta = tarih_html(k)
    if k.ozet:
        ozet = f'      <p class="subtitle" data-alan="K · Özet">{e(k.ozet)}</p>'
    else:
        ozet = ('      <p class="subtitle prose-bos" data-alan="K · Özet">'
                "Özet boş — Excel'de K sütunu doldurulunca burada, başlığın altında görünür.</p>")
    b_alan = "B · Aktivite Websitesi Adı"
    return f"""
    <header class="post-head">
      <p class="label" data-alan="{label_alan}">{e(label)}</p>
      <h1 data-alan="{b_alan}">{e(h1)}</h1>
{ozet}
      <p class="meta-line" data-alan="{meta_alan(k)}">
        {meta}
      </p>
    </header>
"""


def meta_alan(k: Kayit) -> str:
    return "C · Tam Tarih · E · Şehir · F · Mekan" if k.tur == "etkinlik" else "C · Tam Tarih · I · dil"


def tarih_html(k: Kayit) -> str:
    if k.tarih.var_mi:
        return f'<time datetime="{k.tarih.iso()}">{k.tarih.yazi()}</time>'
    return "Tarih belirsiz"


def etkinlik_meta(k: Kayit) -> str:
    parcalar = [tarih_html(k)] + [e(p) for p in (k.sehir, k.mekan) if p and p != "-"]
    return " · ".join(parcalar)


def uzun_html(metin: str, bos: str = "Uzun yazı boş — Excel'de L sütunu doldurulunca burada görünür.") -> str:
    """Excel'deki uzun yazı → paragraflar. Her satırı 'X — Y' olan paragraf
    liste olarak basılır (tema tema içerik, katılımcı katılımcı harita)."""
    if not metin.strip():
        return f'    <div class="prose" data-alan="L · uzun">\n      <p class="prose-bos">{e(bos)}</p>\n    </div>'
    out = []
    for par in [p.strip() for p in re.split(r"\n\s*\n", metin) if p.strip()]:
        satirlar = [s.strip() for s in par.split("\n") if s.strip()]
        if len(satirlar) > 1 and all(" — " in s for s in satirlar):
            li = []
            for s in satirlar:
                a, b = s.split(" — ", 1)
                li.append(f"        <li><strong>{e(a)}</strong> — {e(b)}</li>")
            out.append('      <ul class="icerik-listesi">\n' + "\n".join(li) + "\n      </ul>")
        else:
            out.append("      <p>" + "<br>\n        ".join(e(s) for s in satirlar) + "</p>")
    return '    <div class="prose" data-alan="L · uzun">\n' + "\n".join(out) + "\n    </div>"


def temalar_html(k: Kayit) -> str:
    alan = "H · Temalar" if k.tur == "etkinlik" else "E · Temalar"
    if not k.temalar:
        return f'    <p class="prose-bos" data-alan="{alan}">Tema girilmemiş.</p>'
    li = "\n".join(f'      <li><a class="tag" href="../tr/index.html#temalar">{e(t)}</a></li>'
                   for t in k.temalar)
    return f'    <ul class="tags" data-alan="{alan}">\n{li}\n    </ul>'


def kunye_html(satirlar: list[tuple[str, str]], alan: str) -> str:
    dl = "\n".join(f"      <dt>{e(a)}</dt>\n      <dd>{b}</dd>" for a, b in satirlar if b)
    return f'    <dl class="credits" data-alan="{alan}">\n{dl}\n    </dl>'


def uretim_kunye(k: Kayit, ek: list[tuple[str, str]] = ()) -> str:
    satirlar = [("Üreten", e(YAZAR_ADI.get(k.yazar, k.yazar))),
                ("Network", e(k.network)),
                ("Dil", e(DIL_ADI.get(k.dil, k.dil)))] + list(ek)
    return kunye_html(satirlar, "H · yazar_uretici · G · Network · I · dil · J · dosya_turu")


def etkinlik_kunye(k: Kayit) -> str:
    satirlar = [("Tür", e(", ".join(k.tipler))), ("Network", e(k.network))]
    if k.ig_link:
        satirlar.append(("Instagram", f'<a class="source-link" href="{e(k.ig_link)}">Gönderiyi aç</a>'))
    return kunye_html(satirlar, "G · Etkinlik Tipi · J · Network · M · IG Link")


def pencere(kimlik: str, baslik: str, metin: str) -> str:
    return f"""
    <dialog class="pencere" id="{kimlik}">
      <h2>{e(baslik)}</h2>
      <p>{e(metin)}</p>
      <form method="dialog"><button type="submit">Tamam</button></form>
    </dialog>"""


def indir(kimlik: str, etiket: str, bilgi: str, alan: str = "M · pdf linki") -> str:
    return f"""
    <div class="indir" data-alan="{alan}">
      <button class="indir-dugme" type="button" data-pencere="{kimlik}">{e(etiket)}</button>
      <span class="indir-bilgi">{e(bilgi)}</span>
    </div>""" + pencere(kimlik, etiket, "Bu düğmeye tıklayınca dosya indirilecek. "
                                         "İndirme bağlantısı site yayına alınırken eklenecek.")


def post_nav(onceki: tuple[str, str] | None, sonraki: tuple[str, str] | None) -> str:
    parca = []
    if onceki:
        parca.append(f'      <a class="onceki" href="{onceki[0]}">\n        <span class="yon">← Önceki örnek</span>\n        {e(onceki[1])}\n      </a>')
    if sonraki:
        parca.append(f'      <a class="sonraki" href="{sonraki[0]}">\n        <span class="yon">Sonraki örnek →</span>\n        {e(sonraki[1])}\n      </a>')
    return '\n    <nav class="post-nav">\n' + "\n".join(parca) + "\n    </nav>\n"


def mb(dosya: Path) -> str:
    boyut = dosya.stat().st_size / 1e6
    return f"{boyut:.0f} MB" if boyut >= 10 else f"{boyut:.1f} MB".replace(".", ",")


# --------------------------------------------------------------------------
# İÇERİK BİLEŞENLERİ
# --------------------------------------------------------------------------

def kitapcik_html(kimlik: str, klasor: str, sayfalar: list[Path], aciklama: str, alan: str) -> str:
    en, boy = olcu(sayfalar[0])
    divler = []
    for i, p in enumerate(sayfalar):
        nitelik = "src" if i == 0 else "data-src"
        divler.append(f'          <div class="sayfa"><img {nitelik}="gorsel/{klasor}/{p.name}" '
                      f'alt="{e(aciklama)}, sayfa {i + 1}" width="{en}" height="{boy}"></div>')
    n = len(sayfalar)
    return f"""
    <!-- İÇERİK: kitapçık. PDF'in her sayfası bir görsel (gorsel/{klasor}/001.webp …).
         Kapak tek, iç sayfalar karşılıklı açılır; telefonda tek sayfa.
         data-en / data-boy: sayfa görselinin piksel ölçüsü (oran buradan). -->
    <section class="kitapcik" id="{kimlik}" data-en="{en}" data-boy="{boy}" aria-label="{e(aciklama)} — oku" data-alan="{alan}">
      <div class="kitapcik-sahne">
        <div class="kitapcik-kitap">
{chr(10).join(divler)}
        </div>
      </div>
      <div class="kitapcik-arac">
        <button class="geri" type="button" aria-label="Önceki sayfa">← Önceki</button>
        <label class="kitapcik-konum">
          <span class="visually-hidden">Sayfaya git</span>
          <input type="range" min="1" max="{n}" value="1" step="1">
          <span class="kitapcik-sayac" aria-live="polite">1 / {n}</span>
        </label>
        <button class="ileri" type="button" aria-label="Sonraki sayfa">Sonraki →</button>
        <button class="tam-ekran-dugme" type="button" data-tam-ekran="{kimlik}" aria-pressed="false">Tam ekran ⤢</button>
      </div>
      <p class="kitapcik-ipucu">Sayfanın köşesinden tutup çevirebilir, ok tuşlarını ya da kaydırıcıyı kullanabilirsin.</p>
    </section>
"""


def slayt_html(kimlik: str, klasor: str, slaytlar: list[Path], aciklama: str) -> str:
    buyuk, kucuk = [], []
    for i, p in enumerate(slaytlar):
        yukle = "" if i == 0 else ' loading="lazy"'
        buyuk.append(f'          <div class="swiper-slide"><img src="gorsel/{klasor}/{p.name}" '
                     f'alt="{e(aciklama)}, slayt {i + 1}" width="1600" height="900"{yukle}></div>')
        kucuk.append(f'          <div class="swiper-slide"><img src="gorsel/{klasor}/kucuk/{p.name}" '
                     f'alt="" width="320" height="180" loading="lazy"></div>')
    n = len(slaytlar)
    return f"""
    <!-- İÇERİK: slayt. PPTX'in her slaytı bir görsel (gorsel/{klasor}/01.webp …),
         altta küçük önizlemeler (kucuk/). Yatay 16:9, telefonda da. -->
    <section class="slayt" id="{kimlik}" aria-label="{e(aciklama)} — slaytlar" data-alan="İçerik · PPTX slaytları (ham/ klasöründen)">
      <div class="swiper slayt-ana">
        <div class="swiper-wrapper">
{chr(10).join(buyuk)}
        </div>
      </div>
      <div class="slayt-arac">
        <button class="geri" type="button" aria-label="Önceki slayt">← Önceki</button>
        <span class="slayt-sayac" aria-live="polite">1 / {n}</span>
        <button class="ileri" type="button" aria-label="Sonraki slayt">Sonraki →</button>
        <button class="tam-ekran-dugme" type="button" data-tam-ekran="{kimlik}" aria-pressed="false">Tam ekran ⤢</button>
      </div>
      <div class="swiper slayt-kucuk" aria-hidden="true">
        <div class="swiper-wrapper">
{chr(10).join(kucuk)}
        </div>
      </div>
    </section>
"""


def galeri_arac(bilgi: str) -> str:
    """Albümün / tek görselin altındaki satır: bilgi + tam ekran düğmesi.
    Düğme hemen üstündeki bloğun ilk görselini büyüteçte açar."""
    return (f'    <div class="galeri-arac"><span>{e(bilgi)}</span>'
            '<button type="button" data-tam-galeri>Tam ekran ⤢</button></div>')


def figur(klasor: str, webp: Path, alt: str, grup: str, altyazi: str = "") -> str:
    en, boy = olcu(webp)
    yol = f"gorsel/{klasor}/{webp.name}"
    alt_yazi = f"\n        <figcaption>{e(altyazi)}</figcaption>" if altyazi else ""
    return (f'      <figure>\n        <button class="buyut-ac" type="button" data-grup="{grup}" '
            f'data-buyuk="{yol}" data-alt="{e(altyazi or alt)}" aria-label="Büyüt: {e(altyazi or alt)}">'
            f'<img src="{yol}" alt="{e(alt)}" width="{en}" height="{boy}" loading="lazy"></button>'
            f"{alt_yazi}\n      </figure>")


# --------------------------------------------------------------------------
# ÖRNEKLER
# --------------------------------------------------------------------------

def bul(grup: list[Kayit], klasor: str) -> Kayit:
    for k in grup:
        if k.klasor.name == klasor:
            return k
    raise SystemExit(f"Excel'de bulunamadı: {klasor}")


def main() -> None:
    global YENIDEN
    p = argparse.ArgumentParser(description="Örneklem sayfalarını üretir.")
    p.add_argument("--yeniden", action="store_true", help="görselleri de baştan dönüştür")
    YENIDEN = p.parse_args().yeniden

    ev, pr = oku()
    SIRA = [  # (dosya, liste başlığı) — önceki/sonraki bağlantıları bu sırayla
        ("fanzin.html", "Fanzin"), ("rapor.html", "Rapor"), ("sunum.html", "Sunum"),
        ("yazi.html", "Yazı"), ("album.html", "Foto albüm"), ("gorsel.html", "Tek görsel"),
        ("video.html", "Video"), ("etkinlik-podcast.html", "Etkinlik · Podcast"),
        ("etkinlik-fotograf.html", "Etkinlik · Fotoğraflı"), ("etkinlik-video.html", "Etkinlik · Videolu"),
    ]

    def nav(dosya):
        i = [s[0] for s in SIRA].index(dosya)
        return post_nav(SIRA[i - 1] if i > 0 else None, SIRA[i + 1] if i + 1 < len(SIRA) else None)

    # ---- FANZİN -----------------------------------------------------------
    k = bul(pr, "2025-rahatsiz-edici-sorular-fanzin-1")
    pdf = next(p for p in ham(k) if p.name.endswith("_TR.pdf"))
    sayfalar = pdf_sayfalari(pdf, GORSEL / "fanzin-1")
    govde = (post_head(k, ", ".join(k.tipler), meta=f"{tarih_html(k)} · Türkçe baskı")
             + kitapcik_html("fanzin-kitap", "fanzin-1", sayfalar, "Fanzin #1",
                             "İçerik · PDF sayfaları (ham/ klasöründen)")
             + indir("indir-pencere", "PDF'i indir", f"Türkçe · {len(sayfalar)} sayfa · {mb(pdf)}")
             + "\n" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n"
             + uretim_kunye(k, [("Biçim", f"Fanzin, {len(sayfalar)} sayfa, A5")]) + nav("fanzin.html"))
    sayfa("fanzin.html", k.baslik, k.ozet, "Üretim tipi: Fanzin (kitapçık)", govde, pageflip=True)

    # ---- RAPOR ------------------------------------------------------------
    tr = bul(pr, "2026-mimarlar-ne-kadar-kazaniyor-rapor-tr")
    en = bul(pr, "2026-mimarlar-ne-kadar-kazaniyor-rapor-en")
    anket = bul(pr, "2026-mimarlar-ne-kadar-kazaniyor-anket-formu")
    pdf_tr, pdf_en = ham(tr)[0], ham(en)[0]
    s_tr = pdf_sayfalari(pdf_tr, GORSEL / "rapor-tr")
    s_en = pdf_sayfalari(pdf_en, GORSEL / "rapor-en")
    baslik = tr.baslik.replace(" — Rapor (TR)", "")
    govde = (post_head(tr, "Rapor", h1=baslik,
                       meta=f"{tarih_html(tr)} · Türkçe ve İngilizce")
             + """
    <div class="dil-secim" role="group" aria-label="Rapor dili" data-alan="İki kayıt: Rapor (TR) + Rapor (EN)">
      <button type="button" data-dil="tr" aria-pressed="true">Türkçe</button>
      <button type="button" data-dil="en" aria-pressed="false">English</button>
    </div>
    <div class="dil-blok" data-dil="tr">"""
             + kitapcik_html("rapor-tr-kitap", "rapor-tr", s_tr, "Rapor (TR)", "İçerik · Rapor (TR) PDF sayfaları")
             + indir("indir-tr", "PDF'i indir", f"Türkçe · {len(s_tr)} sayfa · {mb(pdf_tr)}")
             + """
    </div>
    <div class="dil-blok" data-dil="en" hidden>"""
             + kitapcik_html("rapor-en-kitap", "rapor-en", s_en, "Report (EN)", "İçerik · Rapor (EN) PDF sayfaları")
             + indir("indir-en", "Download PDF", f"English · {len(s_en)} pages · {mb(pdf_en)}")
             + """
    </div>
    <div class="baglar" data-alan="Anket Formu kaydı · O · anket linki">
      <button class="source-link" type="button">Ankete katıl</button>
    </div>"""
             + "\n" + uzun_html(tr.uzun) + "\n" + temalar_html(tr) + "\n"
             + uretim_kunye(tr, [("Dil", "Türkçe, İngilizce"),
                                 ("Biçim", f"Rapor, A4 — TR {len(s_tr)}, EN {len(s_en)} sayfa")])
             + nav("rapor.html"))
    govde = govde.replace("<dt>Dil</dt>\n      <dd>Türkçe</dd>\n", "", 1)
    sayfa("rapor.html", baslik, tr.ozet, "Üretim tipi: Rapor (kitapçık, iki dil)", govde, pageflip=True)

    # ---- SUNUM ------------------------------------------------------------
    k = bul(pr, "2025-mimarlik-ve-egitim-kurultayi-xiii-sunum")
    # Üretim satırında özet / uzun / tema boş; metin sunumun yapıldığı
    # etkinliğin satırında (Etkinlikler 53: "Mimarlık ve Eğitim Kurultayı - XIII").
    etk = bul(ev, "2025-mimarlik-ve-egitim-kurultayi-xiii")
    k.ozet, k.uzun, k.temalar = k.ozet or etk.ozet, k.uzun or etk.uzun, k.temalar or etk.temalar
    pptx = ham(k)[0]
    slaytlar = pptx_slaytlari(pptx, GORSEL / "sunum-kurultay")
    govde = (post_head(k, "Sunum", meta=f"{etkinlik_meta(etk)} · {e(etk.network)}",
                       label_alan="D · Üretim Tipi (boş — dosya türünden: pptx)")
             + slayt_html("sunum-slayt", "sunum-kurultay", slaytlar, "Kurultay sunumu")
             + indir("indir-pencere", "Sunumu indir (PDF)", f"{len(slaytlar)} slayt · PowerPoint'ten PDF")
             + "\n" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n"
             + uretim_kunye(k, [("Sunan", "Nihal Evirgen"),
                                ("Biçim", f"Sunum, {len(slaytlar)} slayt, 16:9")]) + nav("sunum.html"))
    # Metin Etkinlikler sayfasından geldiği için etiketler de onu söylesin.
    for eski, yeni in (('"K · Özet"', '"Etkinlikler 53 · K · Özet"'),
                       ('"L · uzun"', '"Etkinlikler 53 · L · Uzun"'),
                       ('"E · Temalar"', '"Etkinlikler 53 · H · Temalar"'),
                       (f'"{meta_alan(k)}"', '"Etkinlikler 53 · C · Tam Tarih · E · Şehir · F · Mekan · J · Network"')):
        govde = govde.replace(eski, yeni)
    sayfa("sunum.html", k.baslik, k.ozet, "Üretim tipi: Sunum (yatay slayt)", govde, swiper=True)

    # ---- YAZI -------------------------------------------------------------
    # Uluslararası yayınlardaki konuşma metni kalıbı: başlık + özet, künye
    # satırı (tarih · yer · dil · okuma süresi), bir fotoğraf, bağlam notu,
    # Türkçe özet, orijinal metin (panel soruları ara başlık), bir alıntı,
    # sonda fotoğraflar ve etkinliğe bağlantı.
    k = bul(pr, "tarihsiz-athens-akea-konusma-metni")
    etk = bul(ev, "2026-akea-calisan-mimarlarin-muhendislerin")
    docx = next(p for p in ham(k) if p.suffix.lower() == ".docx")
    import zipfile
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    paragraflar = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
                   for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)]
    paragraflar = [p for p in paragraflar if p]
    kelime = sum(len(p.split()) for p in paragraflar)
    dakika = max(1, round(kelime / 200))

    # Panel soruları (soru işaretiyle biten kısa paragraflar) ara başlık olur.
    alinti = ("Looking toward the future, what is needed above all is international "
              "organization and solidarity across all fields.")
    metin, soru_sayisi = [], 0
    for p in paragraflar:
        if p.endswith("?") and len(p) < 220:
            soru_sayisi += 1
            if soru_sayisi == 3:   # alıntı, üçüncü bölümün önünde
                metin.append(f'      <blockquote class="alinti" data-alan="Alıntı · örnek — kolektif seçecek">'
                             f"<p>{e(alinti)}</p></blockquote>")
            metin.append(f"      <h2>{e(p)}</h2>")
        else:
            metin.append(f"      <p>{e(p)}</p>")

    # Fotoğraflar AKEA etkinliğinin ham/ klasöründen (galeri-1/).
    fotolar = [magick(p, GORSEL / "akea" / f"{i + 1:02}.webp", "1600x1600>", 76)
               for i, p in enumerate(f for f in ham(etk) if f.suffix.lower() in FOTO_UZANTI)]
    kapak = fotolar[2]
    kapak_fig = figur("akea", kapak, "Atina, Embros Tiyatrosu — panel", "akea", "")
    kapak_fig = kapak_fig.replace("<figure>", '<figure class="tek-gorsel" data-alan="İçerik · bir fotoğraf (etkinliğin ham/ klasöründen)">')
    galeri = [figur("akea", w, f"Atina AKEA panelinden, fotoğraf {i + 1}", "akea", "") for i, w in enumerate(fotolar)]

    meta = (f'<time datetime="{etk.tarih.iso()}">{etk.tarih.yazi()}</time> · {e(etk.sehir)} · '
            f"İngilizce · {dakika} dk okuma")
    govde = (post_head(k, "Konuşma metni", meta=meta)
             + f"""
{kapak_fig}

    <p class="baglam-notu" data-alan="Etkinlik satırından · B · C · F (elle cümle)">
      Bu metin, {etk.tarih.yazi()} tarihinde {e(etk.sehir)}'da, {e(etk.mekan)}'nda AKEA'nın düzenlediği
      “{e(etk.baslik.replace("AKEA ", ""))}” panelinde Nihal Evirgen tarafından İngilizce olarak sunuldu.
    </p>

    <section class="metin-bolum">
      <h2 class="metin-baslik">Türkçe özet</h2>
{uzun_html(k.uzun)}
    </section>

    <!-- İÇERİK: konuşmanın kendisi. docx'teki metin düz yazı olarak girer;
         panelin soruları ara başlık. Dosya indirtilmez. -->
    <section class="metin-bolum" lang="en">
      <h2 class="metin-baslik">Konuşma metni <span>(İngilizce)</span></h2>
      <div class="prose" data-alan="İçerik · docx metni (ham/ klasöründen)">
{chr(10).join(metin)}
      </div>
    </section>

    <section class="metin-bolum">
      <h2 class="metin-baslik">Panelden fotoğraflar</h2>
      <div class="gallery" data-alan="İçerik · etkinliğin fotoğrafları">
{chr(10).join(galeri)}
      </div>
{galeri_arac(f"{len(galeri)} fotoğraf · tıklayınca büyür")}
    </section>

    <div class="baglar" data-alan="Etkinlik kaydına bağlantı">
      <a class="source-link etkinlik-bag" href="../tr/index.html#activity">Etkinlik: {e(etk.baslik)}</a>
    </div>
""" + temalar_html(k) + "\n"
             + uretim_kunye(k, [("Konuşmacı", "Nihal Evirgen"),
                                ("Yer", f"{e(etk.mekan)}, {e(etk.sehir)}"),
                                ("Dil", "İngilizce (Türkçe özetli)"),
                                ("Uzunluk", f"{kelime:,} kelime · {dakika} dk".replace(",", "."))])
             + nav("yazi.html"))
    govde = govde.replace("<dt>Dil</dt>\n      <dd>Türkçe</dd>\n", "", 1)
    sayfa("yazi.html", k.baslik, k.ozet, "Üretim tipi: Yazı / konuşma metni", govde, swiper=True)

    # ---- ALBÜM (Güç Haritası — Toplu) -------------------------------------
    k = bul(pr, "2025-guc-haritasi-toplu")
    # Sayfada "Toplu" yazmıyor; yerine atölyenin yapıldığı okul (G · Network):
    # "Güç Haritası — Toplu" → "Güç Haritası - Yeditepe Üniversitesi"
    k.baslik = k.baslik.replace(" — Toplu", f" - {k.network}")
    kisiler = [x for x in pr if x.klasor.name.startswith("2025-guc-haritasi-") and x is not k]
    figs = []
    for x in kisiler:
        for dosya in ham(x):
            if dosya.suffix.lower() in FOTO_UZANTI:
                w = magick(dosya, GORSEL / "guc-haritasi" / f"{x.slug}.webp")
                figs.append(figur("guc-haritasi", w, f"Güç haritası — {x.yazar}", "guc", x.yazar))
    for dosya in ham(k):   # Excel'de ayrı satırı olmayan katılımcı (Atamert Önder)
        if dosya.suffix.lower() in FOTO_UZANTI:
            w = magick(dosya, GORSEL / "guc-haritasi" / "atamert-onder.webp")
            figs.append(figur("guc-haritasi", w, "Güç haritası — Atamert Önder", "guc", "Atamert Önder"))
    govde = (post_head(k, ", ".join(k.tipler))
             + f"""
    <!-- İÇERİK: foto albüm. Yatay şerit, her görselin altında katılımcı.
         Görsele tıklayınca ekranı kaplayan görünüm (yakınlaştırılabilir). -->
    <div class="gallery" data-alan="İçerik · katılımcı kayıtlarının görselleri · H · yazar">
{chr(10).join(figs)}
    </div>
{galeri_arac(f"{len(figs)} harita · tıklayınca büyür")}
""" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n"
             + uretim_kunye(k, [("Katılımcı", f"{len(figs)} harita")]) + nav("album.html"))
    sayfa("album.html", k.baslik, k.ozet, "Üretim tipi: Foto albüm (toplu atölye)", govde, swiper=True)

    # ---- TEK GÖRSEL (Zihin Akış Bezi — ODTÜ) ------------------------------
    k = bul(pr, "tarihsiz-zihin-akis-bezi-odtu")
    w = magick(ham(k)[0], GORSEL / "bez-odtu" / "bez.webp", "2000x2000>")
    fig = figur("bez-odtu", w, k.baslik, "bez", "")
    fig = fig.replace("<figure>", '<figure class="tek-gorsel" data-alan="İçerik · tek görsel (ham/ klasöründen)">')
    govde = (post_head(k, ", ".join(k.tipler)) + "\n" + fig + "\n"
             + galeri_arac("Tıklayınca büyür, yakınlaşır") + "\n"
             + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n" + uretim_kunye(k) + nav("gorsel.html"))
    sayfa("gorsel.html", k.baslik, k.ozet, "Üretim tipi: Tek görsel", govde, swiper=True)

    # ---- VİDEO (Yas, Hafıza ve Mekan) -------------------------------------
    k = next(x for x in pr if x.klasor.name == "2026-yas-hafiza-ve-mekan")
    yayin = (KOK / "tr/archive/2026-yas-hafiza-ve-mekan.html").read_text(encoding="utf-8")
    kimlik = k.video or re.search(r'data-video="([\w-]{11})"', yayin).group(1)
    ad, _, seri = k.baslik.partition(" | ")
    govde = (post_head(k, "Video", h1=ad, meta=f"{tarih_html(k)} · İpek Bengisu Kumaş, Berk Bulut")
             + f"""
    <!-- İÇERİK: video. Kapak yerel görsel; tıklanınca YouTube oynatıcısı yüklenir (main.js). -->
    <div class="video" data-video="{kimlik}" data-baslik="{e(k.baslik)}" data-alan="N · video linki">
      <button class="video-ac" type="button" aria-label="Videoyu oynat">
        <img src="../kayit/uretimler/2026-yas-hafiza-ve-mekan/kapak.webp" alt="" width="1280" height="720">
        <span class="video-play" aria-hidden="true"></span>
      </button>
    </div>
""" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n"
             + uretim_kunye(k, [("Seri", e(seri)), ("Konuk", "İpek Bengisu Kumaş"), ("Sunan", "Berk Bulut")])
             + nav("video.html"))
    sayfa("video.html", ad, k.ozet, "Üretim tipi: Video (YouTube)", govde)

    # ---- ETKİNLİK · PODCAST -----------------------------------------------
    k = bul(ev, "2025-podcast-06-mufredat-teshiri")
    bolum = k.baslik.rsplit(" - ", 1)[-1]                 # "06-Müfredat Teşhiri: Sezin Sarıca-Ülkü Karakaş"
    no, _, kalan = bolum.partition("-")
    konu, _, kisiler_ = kalan.partition(":")
    kimlik = k.spotify_link.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
    govde = (post_head(k, ", ".join(k.tipler), meta=etkinlik_meta(k), label_alan="G · Etkinlik Tipi")
             + f"""
    <!-- İÇERİK: podcast. Kart; tıklanınca Spotify oynatıcısı yüklenir (orneklem.js, DİNLE). -->
    <div class="dinle" data-spotify="{e(kimlik)}" data-baslik="{e(k.baslik)}" data-alan="O · Spotify Link">
      <button class="dinle-ac" type="button" aria-label="Bölümü dinle">
        <span class="dinle-play" aria-hidden="true"></span>
        <span class="dinle-metin">
          <span class="dinle-ust">Açık Mimarlık · Bölüm {e(no.strip())}</span>
          <span class="dinle-baslik">{e(konu.strip())}</span>
          <span class="dinle-kisi">{e(kisiler_.strip().replace("-", ", "))}</span>
        </span>
      </button>
    </div>
    <p class="video-not">
      Oynatmazsa
      <a href="{e(k.spotify_link)}">Spotify'da dinle ↗</a>
    </p>
""" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n" + etkinlik_kunye(k) + nav("etkinlik-podcast.html"))
    sayfa("etkinlik-podcast.html", k.baslik, k.ozet, "Etkinlik: Podcast (Spotify)", govde, bolum="etkinlik")

    # ---- ETKİNLİK · FOTOĞRAFLI (ARCH302) ----------------------------------
    k = bul(ev, "2025-arch302-sunum-ve-juri")
    asamalar = {}
    for dosya in ham(k):
        if dosya.suffix.lower() in FOTO_UZANTI:
            asamalar.setdefault(dosya.parent.name, []).append(dosya)
    bloklar = []
    for klasor in sorted(asamalar):
        # "02-Prejury-24.04.25" → ("Prejury", 24.04.2025)
        m = re.match(r"\d+-(.*)-(\d{2})\.(\d{2})\.(\d{2})$", klasor)
        ad, tarih = (m.group(1), f"{int(m.group(2))}.{m.group(3)}.20{m.group(4)}") if m else (klasor, "")
        from veri import tarih_coz
        tarih = tarih_coz(tarih).yazi() if tarih else ""
        figs = []
        for i, dosya in enumerate(asamalar[klasor]):
            w = magick(dosya, GORSEL / "arch302" / f"{klasor[:2]}-{i + 1:02}.webp", "1400x1400>", 74)
            figs.append(figur("arch302", w, f"{ad}, fotoğraf {i + 1}", "arch302", f"{ad} — {i + 1}"))
        bloklar.append(f"""
    <section class="asama">
      <h2>{e(ad)}</h2>
      <p class="asama-tarih">{tarih}</p>
      <div class="gallery">
{chr(10).join(figs)}
      </div>
  {galeri_arac(f"{len(figs)} fotoğraf")}
    </section>""")
    govde = (post_head(k, ", ".join(k.tipler), meta=etkinlik_meta(k), label_alan="G · Etkinlik Tipi")
             + "\n    <!-- İÇERİK: fotoğraflar, ham/ içindeki alt klasörlere (süreç aşamalarına) göre.\n"
               "         Klasör adı: 02-Prejury-24.04.25 → başlık \"Prejury\", tarih 24 Nisan 2025. -->\n"
             + '    <div data-alan="İçerik · ham/ alt klasörleri = aşamalar">'
             + "".join(bloklar) + "\n    </div>\n"
             + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n" + etkinlik_kunye(k) + nav("etkinlik-fotograf.html"))
    sayfa("etkinlik-fotograf.html", k.baslik, k.ozet, "Etkinlik: Fotoğraflı (süreç aşamaları)", govde,
          bolum="etkinlik", swiper=True)

    # ---- ETKİNLİK · VİDEOLU (Venedik Bienali) -----------------------------
    k = bul(ev, "2025-venedik-bienali-mimarlik-iscileri")
    kapak = youtube_kapak(k.video, GORSEL / "venedik" / "kapak.webp")
    govde = (post_head(k, ", ".join(k.tipler), meta=etkinlik_meta(k), label_alan="G · Etkinlik Tipi")
             + f"""
    <!-- İÇERİK: video. Kapak yerel görsel (YouTube'dan bir kez indirildi);
         tıklanınca oynatıcı yüklenir (main.js). -->
    <div class="video" data-video="{k.video}" data-baslik="{e(k.baslik)}" data-alan="N · Youtube Link">
      <button class="video-ac" type="button" aria-label="Videoyu oynat">
        <img src="gorsel/venedik/{kapak.name}" alt="" width="1280" height="720">
        <span class="video-play" aria-hidden="true"></span>
      </button>
    </div>
""" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n" + etkinlik_kunye(k) + nav("etkinlik-video.html"))
    sayfa("etkinlik-video.html", k.baslik, k.ozet, "Etkinlik: Videolu (YouTube + Instagram)", govde,
          bolum="etkinlik")

    # ---- LİSTE ------------------------------------------------------------
    liste(SIRA)


def liste(sira) -> None:
    notlar = {
        "fanzin.html": ("Rahatsız Edici Sorular Fanzin #1", "Kitapçık: PDF sayfaları çevrilerek okunur, tam ekran, indir düğmesi."),
        "rapor.html": ("Mimarlar Ne Kadar Kazanıyor?", "Kitapçık (A4), Türkçe / English geçişi, anket bağlantısı."),
        "sunum.html": ("Mimarlık ve Eğitim Kurultayı XIII — Sunum", "Yatay slayt gösterici (16:9), küçük önizlemeler, tam ekran."),
        "yazi.html": ("Athens AKEA — Konuşma Metni", "Görselsiz, metin ağırlıklı sayfa."),
        "album.html": ("Güç Haritası - Yeditepe Üniversitesi", "Katılımcı işlerinden galeri; tıklayınca büyür."),
        "gorsel.html": ("Zihin Akış Bezi — ODTÜ", "Tek büyük görsel; tıklayınca büyür, yakınlaşır."),
        "video.html": ("Ankara, 10 Ekim, 15 Temmuz: Yas, Hafıza ve Mekan", "YouTube oynatıcı."),
        "etkinlik-podcast.html": ("Podcast 06 — Müfredat Teşhiri", "Spotify oynatıcı."),
        "etkinlik-fotograf.html": ("ARCH302 Sunum ve Jüri", "Süreç aşamalarına bölünmüş fotoğraflar."),
        "etkinlik-video.html": ("Venedik Bienali — Mimarlık İşçileri Buluşması", "YouTube + Instagram bağlantısı."),
    }

    def li(dosya, tip):
        ad, not_ = notlar[dosya]
        return (f'      <li><a href="{dosya}"><span class="orneklem-tip">{e(tip.replace("Etkinlik · ", ""))}</span>'
                f'<span><span class="orneklem-ad">{e(ad)}</span><span class="orneklem-not">{e(not_)}</span></span></a></li>')

    uretim = "\n".join(li(d, t) for d, t in sira if not d.startswith("etkinlik"))
    etkinlik = "\n".join(li(d, t) for d, t in sira if d.startswith("etkinlik"))
    govde = f"""
    <header class="post-head">
      <p class="label">Örneklem</p>
      <h1>Sayfa örnekleri</h1>
      <p class="subtitle">Her sayfa tipi için bir örnek. Hepsi aynı iskeleti kullanıyor: başlık, özet, içerik, uzun yazı. Tipten tipe değişen tek şey içerik bölümü.</p>
    </header>

    <div class="prose">
      <p>Her örneğin üstündeki <strong>“Excel sütunlarını göster”</strong> düğmesi, sayfadaki her parçanın
        <em>Activity List</em> tablosunun hangi sütunundan geldiğini gösterir. Bağlantının sonuna
        <code>?alanlar</code> eklenirse sayfa etiketler açık gelir.</p>
    </div>

    <section class="orneklem-grup">
      <h2>Üretimler</h2>
      <ul class="orneklem-liste">
{uretim}
      </ul>
    </section>

    <section class="orneklem-grup">
      <h2>Etkinlikler</h2>
      <ul class="orneklem-liste">
{etkinlik}
      </ul>
    </section>
"""
    metin = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Örneklem — Mimarlıkta Rahatsız Edici Sorular</title>
<meta name="description" content="Üretim ve etkinlik sayfalarının örnekleri">
<link rel="icon" href="../ikon.svg" type="image/svg+xml">
<link rel="icon" href="../favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="stylesheet" href="../main.style.css?v={SURUM}">
<link rel="stylesheet" href="orneklem.css">
</head>
<body class="kayit">
<div class="orneklem-serit">
  <span><strong>ÖRNEKLEM</strong> · sayfa tiplerinin örnekleri</span>
</div>
{ust_nav("uretim")}<main class="wrap">
  <article>
{govde}
  </article>
</main>

{ALT}<script src="../main.js?v={SURUM}"></script>
</body>
</html>
"""
    (CIKTI / "index.html").write_text(metin, encoding="utf-8")
    print("  yazıldı  orneklem/index.html")


if __name__ == "__main__":
    main()
