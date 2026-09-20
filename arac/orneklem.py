#!/usr/bin/env python3
"""
Örneklem sayfalarını üretir: her sayfa tipi için bir örnek.

    python arac/orneklem.py            # görselleri dönüştür (eksikse), sayfaları yaz
    python arac/orneklem.py --yeniden  # görselleri de baştan dönüştür

Çıktı orneklem/ altına:
    index.html              örneklerin listesi
    fanzin.html  rapor.html  album.html  gorsel.html  video.html          (üretimler)
    podcast.html                                              (üretim, Spotify)
    etkinlik-fotograf.html  etkinlik-video.html
    etkinlik-akea.html  etkinlik-kurultay.html                            (etkinlikler)
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
import datetime
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
    """Nav'da aktif sekme örneklemin kendisi — ziyaretçi orada.

    (Nav'da örneklem sekmesi yokken burası arşiv/etkinlikler sekmesini
    işaretliyordu: sayfa tipinin yayında nereye düşeceğini göstersin diye.
    Sekme gelince bu yanlış oldu — aria-current bulunulan sayfayı söyler.)"""
    nav = UST.replace(' aria-current="page"', "")
    return nav.replace('orneklem/index.html">', 'orneklem/index.html" aria-current="page">', 1)


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
      <h1 data-alan="{b_alan}">{e(h1).replace("/", "/<wbr>")}</h1>
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


IG_ETIKET = re.compile(r"(?<![\w.])@([A-Za-z0-9_](?:[A-Za-z0-9_.]*[A-Za-z0-9_])?)")


def ig_bagla(metin_html: str) -> str:
    """Instagram'dan gelen metindeki @etiketler profile bağlanır, yeni sekmede
    açılır. Metin renginde kalır (lacivert link değil), altı noktalı çizgili."""
    return IG_ETIKET.sub(
        lambda m: (f'<a class="ig-etiket" href="https://www.instagram.com/{m.group(1)}/" '
                   f'target="_blank" rel="noopener">@{m.group(1)}</a>'), metin_html)


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
            out.append("      <p>" + "<br>\n        ".join(ig_bagla(e(s)) for s in satirlar) + "</p>")
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


def post_nav(onceki: tuple[str, str] | None, sonraki: tuple[str, str] | None) -> str:
    parca = []
    if onceki:
        parca.append(f'      <a class="onceki" href="{onceki[0]}">\n        <span class="yon">← Önceki örnek</span>\n        {e(onceki[1])}\n      </a>')
    if sonraki:
        parca.append(f'      <a class="sonraki" href="{sonraki[0]}">\n        <span class="yon">Sonraki örnek →</span>\n        {e(sonraki[1])}\n      </a>')
    return '\n    <nav class="post-nav">\n' + "\n".join(parca) + "\n    </nav>\n"


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
# DUYURU
# --------------------------------------------------------------------------
# Duyuru yeni bir sayfa tipi değil: etkinlik sayfasının olay OLMADAN önceki
# hali. Aynı kayıt, aynı adres. Elde fotoğraf, video, uzun yazı yokken sayfayı
# afiş taşır; etkinlik geçince afişin altına fotoğraflar ve yazı girer,
# "yaklaşan" rozeti düşer, sayfa kendiliğinden arşiv kaydı olur.
#
# Afiş kolektifin Instagram için zaten ürettiği görsel — siteye giren tek yeni
# malzeme o. Excel'de sütunu yok; ham/afis.jpg bekleniyor. Yoksa yer tutucu.

def afis_yer_tutucu(oran: str = "4 / 3") -> str:
    """Görsel gelene kadar duracak kutu. Dosya üretmiyoruz: ikon.svg'nin soru
    işareti + ne beklendiğini yazan tek bir inline SVG, her boyutta keskin."""
    return f"""<svg class="afis-bos" viewBox="0 0 400 300" style="aspect-ratio: {oran}"
         role="img" aria-label="Görsel henüz yok">
      <rect width="400" height="300" fill="var(--bg-alt)"></rect>
      <rect x="6" y="6" width="388" height="288" fill="none" stroke="var(--border)"
            stroke-width="3" stroke-dasharray="14 10"></rect>
      <g transform="translate(166 78) scale(2.2)" fill="var(--border)">
        <path d="M0 0 H24 V23 H15 V26 H9 V17 H18 V7 H7 V13 H0 Z"></path>
        <rect x="9" y="29" width="6" height="3"></rect>
      </g>
      <text x="200" y="228" text-anchor="middle" fill="var(--text-faint)"
            font-size="19" font-weight="700">GÖRSEL YOK</text>
      <text x="200" y="254" text-anchor="middle" fill="var(--text-faint)"
            font-size="14">ham/afis.jpg ya da ham/kapak.jpg bekleniyor</text>
    </svg>"""


def afis(k: Kayit, kucuk: bool = False) -> str:
    """Duyurunun görseli. Sırayla aranıyor:

        ham/afis.<uzantı>    etkinliğin afişi — duyuru için doğrusu bu
        ham/kapak.<uzantı>   kapak fotoğrafı — afiş yoksa
        (yoksa)              yer tutucu

    Afiş etkinlikten ÖNCE, kapak fotoğrafı SONRA var oluyor. Geçmiş
    etkinliklerde elde sadece kapak olduğu için sıralama böyle: duyuru
    afişle çıkar, arşive dönerken görseli kapak fotoğrafı olur."""
    ham_kok = KAYIT / k.klasor / "ham"
    kaynak = next((p for ad in ("afis.*", "kapak.*") for p in sorted(ham_kok.glob(ad))
                   if p.suffix.lower() in FOTO_UZANTI), None)
    if not kaynak:
        return afis_yer_tutucu()
    boyut = "600x600>" if kucuk else "1400x1400>"
    w = magick(kaynak, GORSEL / "duyuru" / f"{k.slug}{'-k' if kucuk else ''}.webp", boyut)
    en, boy = olcu(w)
    return (f'<img src="gorsel/duyuru/{w.name}" alt="{e(k.baslik)} afişi" '
            f'width="{en}" height="{boy}" loading="lazy">')


def duyuru_bilgi(k: Kayit) -> str:
    """Duyuruda insanın aradığı tek şey: ne zaman, nerede. Başlığın hemen
    altında, iri ve ayrı. Saatin Excel'de sütunu yok — eksikliği gizlemiyoruz."""
    yer = " · ".join(e(p) for p in (k.mekan, k.sehir) if p and p != "-")
    satir = [("Tarih", f'<time datetime="{k.tarih.iso()}">{k.tarih.yazi()}</time>', "C · Tam Tarih · D · bitiş"),
             ("Saat", '<span class="duyuru-eksik">Excel\'de saat sütunu yok — eklenecek</span>', "— · eksik sütun"),
             ("Yer", yer or '<span class="duyuru-eksik">Girilmemiş</span>', "E · Şehir · F · Mekan"),
             ("Tür", e(" / ".join(k.tipler)), "G · Etkinlik Tipi")]
    ogeler = "\n".join(
        f'      <div data-alan="{alan}">\n        <dt>{ad}</dt>\n        <dd>{deger}</dd>\n      </div>'
        for ad, deger, alan in satir)
    return f'    <dl class="duyuru-bilgi">\n{ogeler}\n    </dl>'


def duyuru_cagri(k: Kayit) -> str:
    """Duyurunun bittiği yer: katılmak isteyen ne yapacak. Takvim dosyası
    sayfa yayına alınırken üretilir; örneklemde düğme açıklama penceresi."""
    ig = (f'      <a class="duyuru-dugme" href="{e(k.ig_link)}">Instagram gönderisi ↗</a>'
          if k.ig_link else
          '      <span class="duyuru-dugme duyuru-dugme--yok">Instagram gönderisi — link girilmemiş</span>')
    return f"""
    <div class="duyuru-cagri" data-alan="M · IG Link">
      <button class="duyuru-dugme duyuru-dugme--ana" type="button" data-pencere="takvim-pencere">Takvime ekle</button>
{ig}
      <a class="duyuru-dugme" href="../tr/contact.html">Soru sor / katıl</a>
    </div>""" + pencere("takvim-pencere", "Takvime ekle",
                        "Bu düğme etkinliğin .ics dosyasını indirecek — tarih, saat ve yer "
                        "takvim uygulamasına doğrudan geçsin diye. Dosya sayfa yayına "
                        "alınırken Excel'deki tarihten üretilir.")


def duyuru_kart(k: Kayit, dosya: str, yaklasan: bool) -> str:
    """Duyuru listesindeki kart: afiş + tarih + tür + başlık. Ana sayfadaki
    .oge ızgarasının aynısı; tek farkı görsel kutusunu afişin doldurması."""
    rozet = '<span class="duyuru-rozet">yaklaşan</span>' if yaklasan else ""
    return f"""      <li class="oge oge--duyuru">
        <a href="{dosya}">
          <span class="oge-gorsel oge-gorsel--afis">{afis(k, kucuk=True)}{rozet}</span>
          <span class="oge-tip">{e(" / ".join(k.tipler))}
            <span class="oge-ok" aria-hidden="true">→</span></span>
          <span class="oge-tarih">{e(k.tarih.yazi())}</span>
          <span class="oge-metin">{e(k.baslik)}</span>
        </a>
      </li>"""


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
        ("fanzin.html", "Fanzin"), ("rapor.html", "Rapor"),
        ("album.html", "Foto albüm"), ("gorsel.html", "Tek görsel"),
        ("video.html", "Video"), ("podcast.html", "Üretim · Podcast"), 
        ("etkinlik-fotograf.html", "Etkinlik · Fotoğraflı"), ("etkinlik-video.html", "Etkinlik · Videolu"),
        ("etkinlik-akea.html", "Etkinlik · Konferans"), ("etkinlik-kurultay.html", "Etkinlik · Kurultay"),
        ("duyuru.html", "Duyuru · Tek etkinlik"), ("duyurular.html", "Duyuru · Liste"),
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
             + """
    </div>
    <div class="dil-blok" data-dil="en" hidden>"""
             + kitapcik_html("rapor-en-kitap", "rapor-en", s_en, "Report (EN)", "İçerik · Rapor (EN) PDF sayfaları")
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

    # ---- SUNUM (Kurultay etkinliğinin malzemesi) --------------------------
    # Sunum ayrı bir üretim sayfası DEĞİL: yapıldığı etkinliğin sayfasında,
    # etkinlik yazısının altında durur. Burada sadece o bölüm hazırlanıyor.
    k = bul(pr, "2025-mimarlik-ve-egitim-kurultayi-xiii-sunum")
    slaytlar = pptx_slaytlari(ham(k)[0], GORSEL / "sunum-kurultay")
    sunum_bolumu = f"""
    <section class="metin-bolum" data-alan="Etkinliğin malzemesi · Üretimler: “Kurultayı XIII — Sunum” (pptx)">
      <h2 class="metin-baslik">Sunum <span>· Nihal Evirgen</span></h2>
{slayt_html("sunum-slayt", "sunum-kurultay", slaytlar, "Kurultay sunumu")}
    </section>
"""

    # ---- KONUŞMA METNİ (AKEA etkinliğinin malzemesi) ----------------------
    # Uluslararası yayınlardaki konuşma metni kalıbı: bağlam notu, Türkçe
    # özet, orijinal metin (panel soruları ara başlık), bir alıntı. Ayrı
    # sayfa değil; AKEA etkinlik sayfasında, etkinlik yazısının altında.
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

    konusma_bolumu = f"""
    <p class="baglam-notu" data-alan="Etkinlik satırından · B · C · F (elle cümle)">
      Bu metin, {etk.tarih.yazi()} tarihinde {e(etk.sehir)}'da, {e(etk.mekan)}'nda AKEA'nın düzenlediği
      “{e(etk.baslik.replace("AKEA ", ""))}” panelinde Nihal Evirgen tarafından İngilizce olarak sunuldu.
    </p>

    <section class="metin-bolum" data-alan="Etkinliğin malzemesi · Üretimler: “Athens AKEA — Konuşma Metni” · L · uzun">
      <h2 class="metin-baslik">Konuşma metni <span>· Nihal Evirgen · İngilizce · {dakika} dk okuma</span></h2>
      <p class="metin-altbaslik">Türkçe özet</p>
{uzun_html(k.uzun)}
    </section>

    <!-- Konuşmanın kendisi. docx'teki metin düz yazı olarak girer;
         panelin soruları ara başlık. Dosya indirtilmez. -->
    <section class="metin-bolum" lang="en">
      <p class="metin-altbaslik">Full text (English)</p>
      <div class="prose" data-alan="docx metni (ham/ klasöründen)">
{chr(10).join(metin)}
      </div>
    </section>
"""

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

    # ---- ÜRETİM · PODCAST -------------------------------------------------
    k = bul(pr, "2025-podcast-06-mufredat-teshiri")
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
""" + uzun_html(k.uzun) + "\n" + temalar_html(k) + "\n" + etkinlik_kunye(k) + nav("podcast.html"))
    sayfa("podcast.html", k.baslik, k.ozet, "Üretim tipi: Podcast (Spotify)", govde)

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

    # ---- ETKİNLİK + MALZEMESİ: AKEA (konuşma metni) ve Kurultay (sunum) ---
    # Konuşma metni ve sunum etkinlik malzemesi, üretim değil: etkinlik
    # sayfasında fotoğraflar ve etkinlik yazısının altında dururlar.
    def etkinlik_fotolari(k: Kayit, klasor: str, grup: str) -> tuple[str, list[Path]]:
        fotolar = [magick(p, GORSEL / klasor / f"{i + 1:02}.webp", "1600x1600>", 76)
                   for i, p in enumerate(f for f in ham(k) if f.suffix.lower() in FOTO_UZANTI)]
        figs = [figur(klasor, w, f"{k.baslik}, fotoğraf {i + 1}", grup, "") for i, w in enumerate(fotolar)]
        blok = (f'    <div class="gallery" data-alan="İçerik · etkinliğin fotoğrafları (ham/ klasöründen)">\n'
                + "\n".join(figs) + "\n    </div>\n" + galeri_arac(f"{len(figs)} fotoğraf · tıklayınca büyür") + "\n")
        return blok, fotolar

    k = bul(ev, "2026-akea-calisan-mimarlarin-muhendislerin")
    galeri, _ = etkinlik_fotolari(k, "akea", "akea")
    govde = (post_head(k, ", ".join(k.tipler), meta=etkinlik_meta(k), label_alan="G · Etkinlik Tipi")
             + "\n" + galeri + uzun_html(k.uzun) + konusma_bolumu
             + temalar_html(k) + "\n" + etkinlik_kunye(k) + nav("etkinlik-akea.html"))
    sayfa("etkinlik-akea.html", k.baslik, k.ozet, "Etkinlik: Konferans + konuşma metni", govde,
          bolum="etkinlik", swiper=True)

    k = bul(ev, "2025-mimarlik-ve-egitim-kurultayi-xiii")
    galeri, _ = etkinlik_fotolari(k, "kurultay", "kurultay")
    govde = (post_head(k, ", ".join(k.tipler), meta=etkinlik_meta(k), label_alan="G · Etkinlik Tipi")
             + "\n" + galeri + uzun_html(k.uzun) + sunum_bolumu
             + temalar_html(k) + "\n" + etkinlik_kunye(k) + nav("etkinlik-kurultay.html"))
    sayfa("etkinlik-kurultay.html", k.baslik, k.ozet, "Etkinlik: Kurultay + sunum (slayt)", govde,
          bolum="etkinlik", swiper=True)

    # ---- DUYURU · TEK ETKİNLİK --------------------------------------------
    # Excel'deki en yeni etkinlik. Duyuru sayfası onun olay olmadan önceki
    # hali: fotoğraf yok, video yok; sayfayı afiş ve "ne zaman, nerede" taşıyor.
    d = ev[0]
    govde = (post_head(d, ", ".join(d.tipler), meta=etkinlik_meta(d), label_alan="G · Etkinlik Tipi")
             + f"""
    <p class="duyuru-durum" data-alan="C · Tam Tarih — tarih geçmediyse">
      <span class="duyuru-rozet">yaklaşan</span>
      Bu etkinlik henüz olmadı. Sayfada fotoğraf, video ve etkinlik yazısı
      yerine afiş ve katılım bilgisi var.
    </p>

    <!-- İÇERİK: afiş. Kolektifin Instagram için ürettiği görsel; siteye giren
         tek yeni malzeme. Excel'de sütunu yok — kayıt klasöründe ham/afis.jpg
         aranır, yoksa aşağıdaki yer tutucu durur. -->
    <figure class="duyuru-afis" data-alan="İçerik · afiş (ham/afis.jpg)">
      {afis(d)}
    </figure>
{duyuru_bilgi(d)}
{duyuru_cagri(d)}
""" + uzun_html(d.uzun, "Duyuru metni boş — Excel'de L sütunu doldurulunca burada görünür.")
             + "\n" + temalar_html(d) + "\n" + etkinlik_kunye(d) + f"""
    <p class="duyuru-not">
      <strong>Etkinlik geçince bu sayfa silinmiyor.</strong> Aynı adres kalır:
      “yaklaşan” rozeti düşer, afişin altına fotoğraflar, video ve etkinlik
      yazısı girer — sayfa kendiliğinden arşiv kaydına döner. Duyuru ile arşiv
      kaydı iki ayrı sayfa değil, aynı sayfanın iki hali.
    </p>
    <p class="duyuru-not duyuru-not--uyari">
      Örnekteki özet ve yazı arşivden geliyor, o yüzden geçmiş zamanda
      (“katıldık”). Gerçek duyuruda aynı sütunlar etkinlikten önce, gelecek
      zamanda yazılır.
    </p>
""" + nav("duyuru.html"))
    sayfa("duyuru.html", d.baslik, d.ozet, "Duyuru: tek etkinlik (yaklaşan)", govde, bolum="etkinlik")

    # ---- DUYURU · LİSTE ---------------------------------------------------
    # Yayında liste tarihi geçmemiş etkinliklerden kurulur. Excel şu an
    # geçmişin arşivi; ileri tarihli tek kayıt var. Örneklemin ızgarası boş
    # kalmasın diye en yeni altı etkinlik gösteriliyor, hangisinin gerçekten
    # yaklaşan olduğu rozetten okunuyor.
    b = datetime.date.today()
    bugun = (b.year, b.month, b.day)

    def yaklasan_mi(k: Kayit) -> bool:
        """Çok günlü etkinlik son günü bitene kadar duyuruda kalır: kartı
        ilk günü geçti diye düşmez."""
        return max(k.tarih.sirala(), k.tarih.bitis or (0, 0, 0)) >= bugun

    kartlar = "\n".join(duyuru_kart(k, "duyuru.html", yaklasan_mi(k)) for k in ev[:6])
    sayi = sum(1 for k in ev if yaklasan_mi(k))
    govde = f"""
    <header class="post-head">
      <p class="label">Duyurular</p>
      <h1>Yaklaşan etkinlikler</h1>
      <p class="subtitle">Tarihi gelmemiş her etkinlik burada bir kartla duruyor: afişi, tarihi, türü. Karta tıklayınca etkinliğin kendi duyuru sayfası açılıyor.</p>
    </header>

    <ul class="izgara izgara--orta duyuru-izgara" data-alan="Excel · tarihi geçmemiş etkinlik satırları">
{kartlar}
    </ul>

    <div class="prose">
      <p class="duyuru-not">Liste elle yazılmıyor: Excel'de tarihi bugünden ileri olan
        her etkinlik satırı kendiliğinden buraya düşüyor, tarih geçince kartı
        arşive geçiyor. Şu an Excel'de tarihi geçmemiş <strong>{sayi} etkinlik</strong> var;
        ızgara boş görünmesin diye örnekte en yeni altı etkinlik gösteriliyor,
        gerçekten yaklaşan olan “yaklaşan” rozetini taşıyor.</p>
    </div>
""" + nav("duyurular.html")
    sayfa("duyurular.html", "Yaklaşan etkinlikler", "Tarihi gelmemiş etkinliklerin duyuruları",
          "Duyuru: liste (kapak + alt sayfa)", govde, bolum="etkinlik")

    # ---- LİSTE ------------------------------------------------------------
    liste(SIRA)


def liste(sira) -> None:
    notlar = {
        "fanzin.html": ("Rahatsız Edici Sorular Fanzin #1", "Kitapçık: PDF sayfaları çevrilerek okunur, tam ekran."),
        "rapor.html": ("Mimarlar Ne Kadar Kazanıyor?", "Kitapçık (A4), Türkçe / English geçişi, anket bağlantısı."),
        "album.html": ("Güç Haritası - Yeditepe Üniversitesi", "Katılımcı işlerinden galeri; tıklayınca büyür."),
        "gorsel.html": ("Zihin Akış Bezi — ODTÜ", "Tek büyük görsel; tıklayınca büyür, yakınlaşır."),
        "video.html": ("Ankara, 10 Ekim, 15 Temmuz: Yas, Hafıza ve Mekan", "YouTube oynatıcı."),
        "podcast.html": ("Podcast 06 — Müfredat Teşhiri", "Spotify oynatıcı."),
        "etkinlik-fotograf.html": ("ARCH302 Sunum ve Jüri", "Süreç aşamalarına bölünmüş fotoğraflar."),
        "etkinlik-video.html": ("Venedik Bienali — Mimarlık İşçileri Buluşması", "YouTube + Instagram bağlantısı."),
        "etkinlik-akea.html": ("AKEA — Atina, 8 Şubat 2026", "Fotoğraflar, etkinlik yazısı, altında konuşma metni (Türkçe özet + İngilizce tam metin)."),
        "etkinlik-kurultay.html": ("Mimarlık ve Eğitim Kurultayı XIII", "Fotoğraflar, etkinlik yazısı, altında sunumun slaytları (tam ekran)."),
        "duyuru.html": ("Situated Architectural Pedagogies of Co-making / Becoming", "Afiş, “ne zaman nerede” bloğu, takvime ekle. Etkinlik geçince aynı sayfa arşiv kaydı olur."),
        "duyurular.html": ("Yaklaşan etkinlikler", "Duyuru kartları: afiş + tarih + tür; karta tıklayınca duyuru sayfası."),
    }

    def li(dosya, tip):
        ad, not_ = notlar[dosya]
        return (f'      <li><a href="{dosya}"><span class="orneklem-tip">{e(tip.split(" · ")[-1])}</span>'
                f'<span><span class="orneklem-ad">{e(ad)}</span><span class="orneklem-not">{e(not_)}</span></span></a></li>')

    uretim = "\n".join(li(d, t) for d, t in sira
                       if not d.startswith(("etkinlik", "duyuru")))
    etkinlik = "\n".join(li(d, t) for d, t in sira if d.startswith("etkinlik"))
    duyuru = "\n".join(li(d, t) for d, t in sira if d.startswith("duyuru"))
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

    <section class="orneklem-grup">
      <h2>Duyurular</h2>
      <p class="orneklem-aciklama">Etkinlik sayfasının olay olmadan önceki hali.
        Ayrı bir kayıt değil: aynı satır, aynı adres. Etkinlik geçince afişin
        altına fotoğraflar ve yazı girer, sayfa arşiv kaydına döner.</p>
      <ul class="orneklem-liste">
{duyuru}
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
