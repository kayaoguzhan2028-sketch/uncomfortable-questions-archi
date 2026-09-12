#!/usr/bin/env python3
"""
Site sayfalarını üretir.

Nav ve footer TEK yerde — burada — duruyor. Bir bağlantı değişince 128 sayfayı
tek tek düzeltmek yerine bu script tekrar çalıştırılır.

    python arac/sayfa.py           # tüm liste sayfalarını üret
    python arac/sayfa.py --listele # yazma, ne üretileceğini göster

Ürettikleri:
    etkinlikler/index.html   Activity — 62 etkinlik
    uretimler/index.html     Works — 66 üretim
    temalar/index.html       Themes — 5 tema, akordeon
    iletisim/index.html      Connect — iletişim + form
"""

import argparse
import collections
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from veri import KOK, oku  # noqa: E402

SITE_AD = "Mimarlıkta Rahatsız Edici Sorular"

# Site iki dilde üretiliyor: tr/ ve en/. İlk dil varsayılan.
DILLER = ("tr", "en")

# ARAYÜZ metinleri. Sadece arayüz: başlık, düğme, bölüm adı, form etiketi.
# Manifesto, tema metinleri ve 32 soru BURADA YOK — onlar kolektifin kendi
# politik beyanı, makine çevirisiyle kolektifin adı altında yayınlanmaz.
# İngilizce sayfada Türkçe asılları bir çeviri notuyla duruyor.
METIN = {
    "tr": {
        "dil_ad": "Türkçe", "oteki": "en", "oteki_ad": "EN",
        "kayit": "kayıt",
        "tema_baslik": "Temalara göre",
        "tema_bos": "Bu temada henüz kayıt yok.",
        "tema_dahasi": "… ve {n} tane daha (toplam {t}).",
        "tema_metin_yok": "Bu temanın metni henüz girilmedi.",
        "tema_cikan": "Bu temalardan çıkanlar",
        "hepsi_ok": "Hepsi ↓",
        "etkinlikler": "etkinlik", "uretimler": "üretim",
        "s_tema": "Tema", "s_soru": "Soru", "s_no": "No",
        "soru_bolum": "{n} rahatsız edici soru",
        "soru_ilk": "Listedeki ilk {n} soru.",
        "soru_tamami": "Kalan {n} soru ve tamamı →",
        "b_temalar": "Temalar",
        "b_nasil": "Nasıl çalışıyoruz",
        "b_manifesto": "Manifesto",
        "b_son": "Son etkinlikler",
        "b_ag": "Ağımız",
        "manifesto_tamami": "Manifestonun tamamı →",
        "hack_baslik": "Kurumları hacklemek",
        "hack_metin": "Kurumları dışarıdan izlemiyoruz; içeriden dönüştürüyoruz. "
                      "Fakülteler, stüdyolar ve ofisler birer tartışma alanı.",
        "foto_bekliyor": "Kolektif fotoğrafı buraya gelecek.",
        "diyagram_bekliyor": "Ağ diyagramı buraya gelecek.",
        "ceviri_notu": "",
        "il_baslik": "Sen de bir soru sor.<br>Listeyi birlikte büyütelim.",
        "il_toplanti": "Toplantılar", "il_toplanti_d": "Açık. Üyelik yok, aidat yok, hiyerarşi yok.",
        "il_nerede": "Nerede", "il_nerede_d": "Ankara — ve çevrimiçi",
        "il_eposta": "E-posta",
        "il_form": "Bize yaz",
        "f_ad": "Ad", "f_soyad": "Soyad", "f_eposta": "E-posta",
        "f_kurum": "Kurum / okul", "f_ilgi": "Neyle ilgilisin?", "f_sec": "Seç…",
        "f_i1": "Toplantılara katılmak", "f_i2": "Bir soru önermek",
        "f_i3": "Üretime katkı (yazı, fanzin, podcast)",
        "f_i4": "Kendi okulumda etkinlik", "f_i5": "Diğer",
        "f_mesaj": "Mesajın", "f_yer": "Sormak istediğin rahatsız edici soru…",
        "f_onay": "Mesajımın kolektifle paylaşılmasını kabul ediyorum.",
        "f_gonder": "Gönder",
        "f_not": 'Form şu an bir yere bağlı değil — kurulana kadar '
                 '<a href="mailto:merhaba@uqinarchi.com">e-posta</a> ile yazabilirsin.',
        "alt_soru": "Sen de bir soru sor",
        "alt_katil": "Nasıl katılırım",
        "ana_baslik": "mimarlıkta rahatsız edici sorular",
    },
    "en": {
        "dil_ad": "English", "oteki": "tr", "oteki_ad": "TR",
        "kayit": "records",
        "tema_baslik": "By theme",
        "tema_bos": "No records under this theme yet.",
        "tema_dahasi": "… and {n} more ({t} in total).",
        "tema_metin_yok": "This theme has no text yet.",
        "tema_cikan": "Out of these themes",
        "hepsi_ok": "See all ↓",
        "etkinlikler": "events", "uretimler": "works",
        "s_tema": "Theme", "s_soru": "Question", "s_no": "No",
        "soru_bolum": "{n} uncomfortable questions",
        "soru_ilk": "The first {n} questions on the list.",
        "soru_tamami": "The remaining {n}, and the full list →",
        "b_temalar": "Themes",
        "b_nasil": "How we work",
        "b_manifesto": "Manifesto",
        "b_son": "Latest activities",
        "b_ag": "Our network",
        "manifesto_tamami": "Read the full manifesto →",
        "hack_baslik": "Hacking the institution",
        "hack_metin": "We do not watch institutions from the outside; we change them "
                      "from within. Faculties, studios and offices are all grounds "
                      "for argument.",
        "foto_bekliyor": "Collective photograph goes here.",
        "diyagram_bekliyor": "Network diagram goes here.",
        # İngilizce sayfada çevrilmemiş bölümlerin üstünde duruyor.
        "ceviri_notu": "Not translated yet. The Turkish original follows — an "
                       "English version will replace it once the collective "
                       "provides one.",
        "il_baslik": "Ask an uncomfortable question.<br>Let us grow the list together.",
        "il_toplanti": "Meetings", "il_toplanti_d": "Open. No membership, no dues, no hierarchy.",
        "il_nerede": "Where", "il_nerede_d": "Ankara — and online",
        "il_eposta": "Email",
        "il_form": "Get in touch",
        "f_ad": "First name", "f_soyad": "Last name", "f_eposta": "Email",
        "f_kurum": "Institution / school", "f_ilgi": "What brings you here?",
        "f_sec": "Choose…",
        "f_i1": "Joining the meetings", "f_i2": "Proposing a question",
        "f_i3": "Contributing (writing, zine, podcast)",
        "f_i4": "An event at my own school", "f_i5": "Something else",
        "f_mesaj": "Your message", "f_yer": "The uncomfortable question you want to ask…",
        "f_onay": "I agree that my message may be shared with the collective.",
        "f_gonder": "Send",
        "f_not": 'The form is not connected to anything yet — until it is, write to '
                 '<a href="mailto:merhaba@uqinarchi.com">merhaba@uqinarchi.com</a>.',
        "alt_soru": "Ask an uncomfortable question",
        "alt_katil": "How to participate",
        "ana_baslik": "uncomfortable questions in architecture",
    },
}

# İngilizce giriş ve alt metin. Bunlar tanıtım paragrafı, manifesto değil;
# çevrildi ama kolektifin onayından geçmedi — README'de not düşüldü.
GIRIS_EN = (
    "Uncomfortable Questions in Architecture is an independent collective founded "
    "in Ankara in 2024. Students, academics and architectural workers take up "
    "together the structural inequalities, labour regimes and pedagogical "
    "deadlocks met in both education and professional practice. We see "
    "architecture not only as a technical mode of production but as a political "
    "field of action that opens up both the architect's position as a worker-subject "
    "and the dynamics of the built environment. We believe systematic inequalities "
    "can only be overcome when these three groups organise together. We work "
    "horizontally, refusing hierarchy, on a voluntary basis."
)

ALT_METIN_EN = (
    "Uncomfortable Questions in Architecture was founded in Ankara in 2024. An "
    "independent collective. No membership, no dues, no hierarchy. Meetings are "
    "open, production is collective, decisions are taken horizontally. Whatever is "
    "passed over in silence in architectural education and practice is worth "
    "saying out loud; we open grounds for argument inside the discipline's "
    "comfortable areas. We ask how architecture is made, by whose labour it is "
    "built, and in whose name it is remembered. If you are a student, an academic "
    "or an architectural worker, you are already part of this. Add one more "
    "question to the ones above. Let us grow the list."
)


def S(dil, anahtar, **k):
    """Arayüz metni. Eksik anahtar sessizce geçmesin diye KeyError bırakıyoruz."""
    m = METIN[dil][anahtar]
    return m.format(**k) if k else m


def giris(dil):
    return GIRIS_EN if dil == "en" else GIRIS


def alt_metin(dil):
    return ALT_METIN_EN if dil == "en" else ALT_METIN


def notlu(dil, govde):
    """İngilizce sayfada çevrilmemiş Türkçe bloğun üstüne not koyar."""
    if dil == "tr":
        return govde
    return f'<p class="ceviri-notu">{S(dil, "ceviri_notu")}</p>\n' + govde

IKON = ('<svg class="site-ikon" viewBox="0 0 24 32" aria-hidden="true" focusable="false">'
        '<path fill="currentColor" d="M0 0 H24 V23 H15 V26 H9 V17 H18 V7 H7 V13 H0 Z"/>'
        '<rect fill="currentColor" x="9" y="29" width="6" height="3"/></svg>')

# Nav bağlantıları: (etiket, kök'e göre yol, bu sayfanın kimliği)
NAV = [
    ("Manifesto", "manifesto/", "manifesto"),
    ("Themes", "temalar/", "temalar"),
    ("Activity", "etkinlikler/", "etkinlikler"),
    ("Network", "#network", "network"),
]

TEMALAR = [
    ("Mimarlık ve Pedagoji", "mimarlik-ve-pedagoji"),
    ("Stüdyo Kültürü", "studyo-kulturu"),
    ("Müfredat Teşhiri", "mufredat-teshiri"),
    ("Sınıf ve Emek", "sinif-ve-emek"),
    ("Toplumsal Cinsiyet", "toplumsal-cinsiyet"),
]

# 2024 listesindeki rahatsız edici sorular. Beş tema sabit bir döngüyle
# tekrar ediyor (01 Pedagoji, 02 Stüdyo, 03 Müfredat, 04 Sınıf, 05 Cinsiyet,
# 06 Pedagoji...), her satır bu döngüye uyuyor — çeviri kendi yapısıyla
# doğrulanmış oluyor. Numara listedeki sıradan geliyor, elle yazılmıyor.
SORULAR = [
    ('Mimarlık ve Pedagoji', '"Mimar" kimdir? Mimarların ve mimarlığın rolü nedir?'),
    ('Stüdyo Kültürü', 'Mimarlar hep inşa mı eder?'),
    ('Müfredat Teşhiri', 'Mimarlık tasarım stüdyolarında tasarım sürecini, ya da yapmama/inşa etmeme seçeneklerini konuşuyor muyuz?'),
    ('Sınıf ve Emek', 'Bilgi üretmenin ya da aktarmanın bazı biçimlerinin doğru olmadığını biliyor olduğunuzda ne yaparsınız?'),
    ('Toplumsal Cinsiyet', 'Mimarlık üretimi ve eğitimi sırasında doğru olmadığını düşündüğünüz yöntemler var mı? Varsa bunlara karşı ne yapılabileceğini düşünüyorsunuz?'),
    ('Mimarlık ve Pedagoji', 'Ne kadar maaş alıyorsunuz? Hak ettiğiniz ücreti aldığınızı düşünüyor musunuz?'),
    ('Stüdyo Kültürü', 'Günde kaç saat mesai yapıyorsunuz? Ne sıklıkla fazla mesaiye kalıyorsunuz?'),
    ('Müfredat Teşhiri', 'Çalışma süreniz ve iş tanımınızdan emin misiniz?'),
    ('Sınıf ve Emek', 'Bursiyer ile asistan pozisyonları arasında ne fark vardır? İş tanımları eşitlenebilir mi?'),
    ('Toplumsal Cinsiyet', 'Araştırma asistanı ile eğitim asistanı arasında ne fark vardır? İş tanımları eşitlenebilir mi?'),
    ('Mimarlık ve Pedagoji', 'Üniversitelerde akademik personelin büyük kısmını yarı zamanlı öğretim üyelerinden oluşturmak yönünde bir politika uygulandığını düşünüyor musunuz?'),
    ('Stüdyo Kültürü', 'Akademik araştırma yürütmek için gerekli zaman ve gelire sahip misiniz?'),
    ('Müfredat Teşhiri', 'Çalışma yaşantınızda görülmeyen ve ücretsiz emeğe ne oranda tanık oldunuz?'),
    ('Sınıf ve Emek', 'Çalışma yaşantınızla ilgili kararlar konusunda otoritenin size ait olduğuna inanıyor musunuz? Otoritenizin sınırları nerede başlayıp bitiyor?'),
    ('Toplumsal Cinsiyet', 'Prekaryanın sizin için anlamı nedir?'),
    ('Mimarlık ve Pedagoji', 'Yaratıcılığın sizin için anlamı nedir?'),
    ('Stüdyo Kültürü', 'Çalıştığınız yer maaş, ikramiye ve terfi konularında transparan mı?'),
    ('Müfredat Teşhiri', 'Mimarlık eğitiminde ya da çalışma hayatında travmatik tecrübeleriniz var mı?'),
    ('Sınıf ve Emek', 'Çalıştığınız yerde bir meseleyle ilgili toplum içinde konuşmaktan misilleme ya da şantaj korkusuyla kaçındığınız oldu mu?'),
    ('Toplumsal Cinsiyet', 'Çalışma alanınızda konuşma ve ifade özgürlüğü olduğunu düşünüyor musunuz?'),
    ('Mimarlık ve Pedagoji', 'Çalıştığınız yerde örgütlenme konusunda gerekli bilgi ve platformların erişilebilir olduğunu düşünüyor musunuz?'),
    ('Stüdyo Kültürü', 'Sizce kiminle ve nasıl örgütlenebiliriz?'),
    ('Müfredat Teşhiri', 'Mimarlıkta işleyen tasarım süreçleri, etik ve çalışma koşulları üzerinde nasıl söz sahibi olabiliriz?'),
    ('Sınıf ve Emek', 'Materyaller için belirlediğimiz gerekli koşulları neden emek için de tanımlamıyoruz?'),
    ('Toplumsal Cinsiyet', 'Profesyonel pratik ve akademik alan birbirinden bağımsız mıdır?'),
    ('Mimarlık ve Pedagoji', 'Mekan üretimine odaklanan ekonomik sistem mimarlık pratiğini nasıl etkiliyor?'),
    ('Stüdyo Kültürü', 'Mevcut sistem ile mimarlık eğitim müfredatı arasındaki ilişki nedir?'),
    ('Müfredat Teşhiri', 'Mevcut mimarlık müfredatının üretim süreçlerini, inşa emeğini ve şantiye alanlarını da dikkate aldığını düşünüyor musunuz?'),
    ('Sınıf ve Emek', 'Mimarlık pedagojisinin değişmesi, mimarlığın üretim biçimlerini nasıl değiştirirdi?'),
    ('Toplumsal Cinsiyet', 'Derslik ve stüdyoları kamuya açık eleştirel mekanlara dönüştürebilir miyiz?'),
    ('Mimarlık ve Pedagoji', 'Mekanla, kendimizle ve birbirimizle olan bağlarımızı nasıl görünür kılabiliriz?'),
    ('Stüdyo Kültürü', 'Eğer emek, yapma biçimleri, bilgi birikimi ve inşa sürecinin kendisi merkeze alınırsa, mimarlık ve tasarım alanlarının bilgisi ve pratikleri nasıl dönüşür?'),
]


def soru_tablosu(dil, sinir=None):
    """Soru tablosu. sinir verilirse ilk o kadarını yazar.

    Soruların kendisi çevrilmiyor: kolektifin sorduğu sorular, benim
    çevirim değil. Sadece sütun başlıkları dile göre değişiyor."""
    goster = SORULAR[:sinir] if sinir else SORULAR
    p = ['  <div class="tablo-kaydir">', '    <table class="soru-tablo">',
         '      <thead>',
         f'        <tr><th>{S(dil, "s_tema")}</th><th>{S(dil, "s_soru")}</th>'
         f'<th class="s-no">{S(dil, "s_no")}</th></tr>',
         '      </thead>', '      <tbody>']
    for i, (tema, soru) in enumerate(goster, start=1):
        p.append('        <tr>')
        p.append(f'          <td class="s-tema">{html.escape(tema)}</td>')
        p.append(f'          <td>{html.escape(soru)}</td>')
        p.append(f'          <td class="s-no">{i:02d}</td>')
        p.append('        </tr>')
    p += ['      </tbody>', '    </table>', '  </div>']
    return "\n".join(p)


TEMA_METIN = {
    "Mimarlık ve Pedagoji":
        "Mimarlıkta Rahatsız Edici Sorular (UQA), mimarlığın sterilleştirilmiş "
        "alanlarından, pürüzsüz tasarım yüzeylerinden ve kurumsal sessizliğinden "
        "duyulan rahatsızlıktan doğmuştur. Bu rahatsızlık, sadece bireysel bir duygu "
        "değil; gücün kimde toplandığını, emeğin nasıl görünmez kılındığını ve hangi "
        "normların bize “doğal” olarak sunulduğunu anlamamızı sağlayan politik bir "
        "pusuladır. Bu rahatsızlığı bir son değil, sistemin çatlaklarını genişletecek "
        "bir dönüşüm yakıtı ve eleştirel düşünmenin bir gerekliliği olarak kabul "
        "ediyoruz.",
}

GIRIS = (
    "Mimarlıkta Rahatsız Edici Sorular, 2024’te Ankara’da kurulan bağımsız bir "
    "kolektiftir. Öğrenciler, akademisyenler ve mimarlık işçileri; hem eğitim hem "
    "meslek pratiklerinde karşılaşılan yapısal eşitsizlikleri, emek rejimlerini ve "
    "pedagojik tıkanıklıkları birlikte ele alıyor. Mimarlığı yalnızca teknik bir "
    "üretim biçimi olarak değil, hem işçi-özne olarak mimarın konumunu hem de yapılı "
    "çevrenin dinamiklerini açan politik bir eylem alanı olarak görüyoruz. Sistematik "
    "eşitsizliklerin ancak bu üçlü yapının birlikte örgütlenmesiyle aşılabileceğine "
    "inanıyoruz. Hiyerarşiyi reddeden yatay bir örgütlenme modelini benimsiyor, "
    "gönüllülük esasına dayalı çalışıyoruz."
)

ALT_METIN = (
    "Mimarlıkta Rahatsız Edici Sorular, 2024’te Ankara’da kuruldu. Bağımsız bir "
    "kolektif. Üyelik yok, aidat yok, hiyerarşi yok. Toplantılar açık, üretimler "
    "kolektif, kararlar yatay alınır. Mimarlık eğitiminde ve meslekte sessiz kalınan "
    "ne varsa konuşulmaya değer; disiplinin “rahat” alanlarında dönüştürücü tartışma "
    "zeminleri açıyoruz. Mimarlığın nasıl yapıldığını, kimin emeğiyle inşa edildiğini, "
    "kimin adıyla anıldığını sorguluyoruz. Sen de bir öğrenciysen, akademisyensen, "
    "mimarlık işçisiysen buradasın. Yukarıdaki sorulara bir tane daha ekle. Listeyi "
    "büyütelim."
)


def kac(n: int) -> str:
    return f"../" * n


def bas(dil: str, baslik: str, aciklama: str, derinlik: int, yol: str) -> str:
    k = kac(derinlik)
    ot = S(dil, "oteki")
    return f"""<!DOCTYPE html>
<html lang="{dil}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(baslik)} — {SITE_AD}</title>
<meta name="description" content="{html.escape(aciklama)}">
<link rel="icon" href="{k}ikon.svg" type="image/svg+xml">
<link rel="alternate" hreflang="{dil}" href="{k}{dil}/{yol}">
<link rel="alternate" hreflang="{ot}" href="{k}{ot}/{yol}">
<link rel="stylesheet" href="{k}main.style.css">
</head>
<body>
"""


def ust(dil: str, aktif: str, derinlik: int, yol: str) -> str:
    """Üç satırlı çerçeveli nav. Bulunduğun sayfa siyah ve altı çizili.

    yol: dil kökünden sonraki kısım ('', 'manifesto/', ...). Dil düğmesi
    öteki dilde AYNI sayfaya gitsin diye lazım."""
    k = kac(derinlik)
    ot, ot_ad = S(dil, "oteki"), S(dil, "oteki_ad")
    baglar = []
    for etiket_, hedef_yol, kimlik in NAV:
        hedef = (f"{k}{dil}/index.html{hedef_yol}" if hedef_yol.startswith("#")
                 else f"{k}{dil}/{hedef_yol}")
        simdi = ' aria-current="page"' if kimlik == aktif else ""
        baglar.append(f'<a href="{hedef}"{simdi}>{etiket_}</a>')

    uretim_simdi = ' aria-current="page"' if aktif == "uretimler" else ""
    iletisim_simdi = ' aria-current="page"' if aktif == "iletisim" else ""

    return f"""<header class="ust kutu">
  <div class="ust-satir">
    <a class="ust-ikon" href="{k}{dil}/" aria-label="{SITE_AD}">{IKON}</a>
    <span class="ust-ad">{SITE_AD}</span>
    <span class="ust-sag ust-grup">
      <a class="ust-dil" href="{k}{ot}/{yol}" data-dil="{ot}" hreflang="{ot}">{ot_ad}</a>
      <a href="{k}{dil}/iletisim/"{iletisim_simdi}>Connect</a>
    </span>
  </div>
  <div class="ust-satir">
    {chr(10).join('    ' + b for b in baglar).strip()}
  </div>
  <div class="ust-satir">
    <a class="ust-genis" href="{k}{dil}/uretimler/"{uretim_simdi}>Productions / Archive</a>
    <span></span>
    <a class="ust-sag" href="https://www.instagram.com/">Instagram</a>
  </div>
</header>
"""


def alt(dil: str, derinlik: int) -> str:
    k = kac(derinlik)
    # Şemadaki footer üstü şerit görsel. Dosya yoksa etiket hiç yazılmıyor —
    # kırık görsel ya da boş yer tutucu bırakmıyoruz.
    serit = (f'<div class="alt-gorsel kutu"><img src="{k}alt-gorsel.webp" alt=""></div>'
             if (KOK / "alt-gorsel.webp").exists() else "")
    return serit + f"""
<footer class="alt kutu">
  <div class="ust-satir">
    <a class="ust-ikon" href="{k}{dil}/" aria-label="{SITE_AD}">{IKON}</a>
    <span class="ust-ad">{S(dil, "alt_soru")}</span>
    <a class="ust-sag" href="{k}{dil}/iletisim/">Connect</a>
  </div>
  <div class="ust-satir">
    <a href="https://www.instagram.com/">Instagram</a>
    <a href="{k}{dil}/iletisim/">{S(dil, "il_eposta")}</a>
    <span></span>
    <a class="ust-sag" href="{k}{dil}/iletisim/">{S(dil, "alt_katil")}</a>
  </div>
  <p class="alt-metin">{alt_metin(dil)}</p>
  <div class="ust-satir">
    <a href="{k}{dil}/manifesto/">Manifesto</a>
    <span></span>
    <a href="{k}{dil}/temalar/">Themes</a>
    <a class="ust-sag" href="{k}{dil}/index.html#network">Network</a>
  </div>
  <div class="ust-satir alt-satir--6">
    <a href="{k}{dil}/etkinlikler/">Conferences</a>
    <a href="{k}{dil}/etkinlikler/">Podcasts</a>
    <a href="{k}{dil}/etkinlikler/">Activity</a>
    <a href="{k}{dil}/etkinlikler/">Events</a>
    <a href="{k}{dil}/uretimler/">Archive</a>
    <a class="ust-sag" href="{k}{dil}/uretimler/">News/Updates</a>
  </div>
  <div class="ust-satir alt-satir--3">
    <a href="{k}{dil}/iletisim/">Terms</a>
    <span style="text-align:center">www.uqinarchi.com</span>
    <span class="ust-sag">©2026 All Rights Reserved</span>
  </div>
</footer>

<script src="{k}main.js"></script>
</body>
</html>
"""


def kart(dil, kayit, derinlik: int) -> str:
    """Izgaradaki tek kayıt.

    Sayfa tr/ ya da en/ altında, FOTOĞRAF kayit/ altında: fotoğraf iki dilde
    de aynı, repoda tek kopya duruyor."""
    k = kac(derinlik)
    sayfa = f"{k}{dil}/{kayit.klasor.as_posix()}/"
    gorsel = KOK / kayit.kaynak / "kapak.webp"
    ic = (f'<img src="{k}{kayit.kaynak.as_posix()}/kapak.webp" alt="" loading="lazy">'
          if gorsel.exists() else IKON)
    tip = " / ".join(kayit.tipler) or "—"
    return f"""      <li class="oge">
        <a href="{sayfa}">
          <span class="oge-gorsel">{ic}</span>
          <span class="oge-tarih">{html.escape(kayit.tarih.yazi())}</span><br>
          <span class="oge-tip">{html.escape(tip)}</span>
          <span class="oge-metin">{html.escape(kayit.baslik)}</span>
        </a>
      </li>"""


def tema_akordeonu(dil, kayitlar, derinlik):
    """Solda başlık, sağda açılır tema satırları.

    Satırlar gerçek kayıtlara açılıyor. '?tema=' gibi çalışmayan bir filtre
    bağlantısı kullanmıyoruz — site JavaScript'siz de tam çalışsın diye."""
    k = kac(derinlik)
    p = ['  <div class="akordeon-blok">', f'    <h2>{S(dil, "tema_baslik")}</h2>',
         '    <div class="akordeon">']
    for ad, _slug in TEMALAR:
        icinde = [x for x in kayitlar if ad in x.temalar]
        p.append('      <details>')
        p.append(f'        <summary><span>{html.escape(ad)}</span></summary>')
        p.append('        <div class="akordeon-govde">')
        if icinde:
            p.append('          <ul>')
            for x in icinde[:8]:
                p.append(f'            <li><a href="{k}{dil}/{x.klasor.as_posix()}/">'
                         f'{html.escape(x.tarih.yazi())} — '
                         f'{html.escape(x.baslik[:70])}</a></li>')
            p.append('          </ul>')
            if len(icinde) > 8:
                p.append('          <p class="metin-ikincil">'
                         + S(dil, "tema_dahasi", n=len(icinde) - 8, t=len(icinde))
                         + '</p>')
        else:
            p.append(f'          <p class="metin-ikincil">{S(dil, "tema_bos")}</p>')
        p.append('        </div>')
        p.append('      </details>')
    p += ['    </div>', '  </div>']
    return "\n".join(p)


def liste_sayfasi(dil, aktif, baslik, kayitlar, derinlik):
    yol = f"{aktif}/"
    ilk, kalan = kayitlar[:3], kayitlar[3:]
    p = [bas(dil, baslik, giris(dil)[:150], derinlik, yol),
         ust(dil, aktif, derinlik, yol), '<main class="kutu">']
    p.append(f'  <p class="giris">{giris(dil)}</p>')

    p.append(f'  <div class="bolum-ust"><h2>Latest {baslik}</h2>'
             f'<a class="daha" href="#hepsi">Load more ↓</a></div>')
    p.append('  <ul class="izgara izgara--iri">')
    p += [kart(dil, x, derinlik) for x in ilk]
    p.append('  </ul>')

    p.append(f'  <div class="bolum-ust" id="hepsi"><h2>All {baslik}</h2>'
             f'<span class="daha">{len(kayitlar)} {S(dil, "kayit")}</span></div>')
    p.append('  <ul class="izgara izgara--sik">')
    p += [kart(dil, x, derinlik) for x in kalan]
    p.append('  </ul>')

    p.append(tema_akordeonu(dil, kayitlar, derinlik))

    p.append('</main>')
    p.append(alt(dil, derinlik))
    return "\n".join(p)


def temalar_sayfasi(dil, ev, pr, derinlik=2):
    yol = "temalar/"
    p = [bas(dil, "Themes", "Beş ana tema.", derinlik, yol),
         ust(dil, "temalar", derinlik, yol),
         '<main class="kutu">', '  <div class="akordeon">']

    for i, (ad, slug) in enumerate(TEMALAR):
        e = [x for x in ev if ad in x.temalar]
        u = [x for x in pr if ad in x.temalar]
        metin = TEMA_METIN.get(ad, "")
        govde = (notlu(dil, f'<p>{metin}</p>') if metin
                 else f'<p class="prose-bos">{S(dil, "tema_metin_yok")}</p>')

        tipler = collections.Counter(t for x in e for t in x.tipler)
        utipler = collections.Counter(t for x in u for t in x.tipler)
        say = lambda c: ", ".join(f"{a} ({n})" for a, n in c.most_common(5)) or "—"

        p.append(f'    <details{" open" if i == 0 else ""}>')
        p.append(f'      <summary>{html.escape(ad)}</summary>')
        p.append(f'      <div class="akordeon-govde">{govde}')
        p.append(f'        <p class="metin-ikincil"><b>Activities:</b> {say(tipler)}'
                 f' &nbsp;·&nbsp; <b>Productions:</b> {say(utipler)}'
                 f' &nbsp;·&nbsp; {len(e)} {S(dil, "etkinlikler")}, '
                 f'{len(u)} {S(dil, "uretimler")}</p>')
        p.append('        <ul>')
        for x in (e + u)[:8]:
            p.append(f'          <li><a href="{kac(derinlik)}{dil}/{x.klasor.as_posix()}/">'
                     f'{html.escape(x.tarih.yazi())} — {html.escape(x.baslik[:70])}</a></li>')
        p.append('        </ul>')
        p.append('      </div>')
        p.append('    </details>')

    p.append('  </div>')

    p.append(f'  <div class="bolum-ust"><h2>{S(dil, "tema_cikan")}</h2>'
             f'<a class="daha" href="{kac(derinlik)}{dil}/etkinlikler/">'
             f'{S(dil, "hepsi_ok")}</a></div>')
    p.append('  <ul class="izgara izgara--orta">')
    p += [kart(dil, x, derinlik) for x in ev[:6]]
    p.append('  </ul>')

    p.append('</main>')
    p.append(alt(dil, derinlik))
    return "\n".join(p)


def iletisim_sayfasi(dil, derinlik=2):
    yol = "iletisim/"
    return bas(dil, "Connect", S(dil, "il_form"), derinlik, yol) \
        + ust(dil, "iletisim", derinlik, yol) + f"""<main class="kutu">
  <div class="giris">
    <h1 class="iletisim-baslik">{S(dil, "il_baslik")}</h1>
  </div>

  <div class="iletisim">
    <div class="iletisim-bilgi">
      <dl>
        <dt>{S(dil, "il_toplanti")}</dt>
        <dd>{S(dil, "il_toplanti_d")}</dd>
        <dt>{S(dil, "il_nerede")}</dt>
        <dd>{S(dil, "il_nerede_d")}</dd>
        <dt>Instagram</dt>
        <dd><a href="https://www.instagram.com/">@uncomfortablequestionsarch</a></dd>
        <dt>YouTube</dt>
        <dd><a href="https://www.youtube.com/@uncomfortablequestionsarch">@uncomfortablequestionsarch</a></dd>
        <dt>{S(dil, "il_eposta")}</dt>
        <dd><a href="mailto:merhaba@uqinarchi.com">merhaba@uqinarchi.com</a></dd>
      </dl>
    </div>

    <div class="iletisim-form">
      <h2>{S(dil, "il_form")}</h2>

      <!-- ÖNEMLİ: GitHub Pages statik bir sunucu, form verisini alacak bir
           arka uç YOK. Bu form şu an hiçbir yere göndermiyor.
           Çalışması için action'a bir form servisi adresi koymak gerekiyor
           (Formspree, Basin, Web3Forms gibi — ücretsiz planları var). -->
      <form action="" method="post">
        <div class="form-satir">
          <label>{S(dil, "f_ad")} <span aria-hidden="true">*</span>
            <input type="text" name="ad" required autocomplete="given-name">
          </label>
          <label>{S(dil, "f_soyad")}
            <input type="text" name="soyad" autocomplete="family-name">
          </label>
        </div>
        <div class="form-satir">
          <label>{S(dil, "f_eposta")} <span aria-hidden="true">*</span>
            <input type="email" name="eposta" required autocomplete="email">
          </label>
          <label>{S(dil, "f_kurum")}
            <input type="text" name="kurum" autocomplete="organization">
          </label>
        </div>
        <label>{S(dil, "f_ilgi")}
          <select name="ilgi">
            <option value="">{S(dil, "f_sec")}</option>
            <option>{S(dil, "f_i1")}</option>
            <option>{S(dil, "f_i2")}</option>
            <option>{S(dil, "f_i3")}</option>
            <option>{S(dil, "f_i4")}</option>
            <option>{S(dil, "f_i5")}</option>
          </select>
        </label>
        <label>{S(dil, "f_mesaj")}
          <textarea name="mesaj" rows="6" placeholder="{S(dil, "f_yer")}"></textarea>
        </label>
        <label class="form-onay">
          <input type="checkbox" name="onay" required>
          <span>{S(dil, "f_onay")}</span>
        </label>
        <button type="submit">{S(dil, "f_gonder")}</button>
        <p class="form-not">{S(dil, "f_not")}</p>
      </form>
    </div>
  </div>
</main>
""" + alt(dil, derinlik)


def etiket(no: str, ad: str) -> str:
    return f'  <div class="bolum-etiket"><span class="no">{no}</span><span>{ad}</span></div>'


# Uluslararası ağ — ülke, kurum
AG = [
    ("Avustralya", "Trade Unionists Landscape Architecture (TULA)"),
    ("Avustralya", "Professionals Australia Architects Division (PAA)"),
    ("Avustralya", "Parlour"),
    ("Avusturya", "ZKMB"),
    ("Belçika", "Dear Architects"),
    ("Belçika", "Belgian Architects United (BAU)"),
    ("Brezilya", "FNA"),
    ("Finlandiya", "KAIAIA"),
    ("Almanya", "Architekt innengewerkschaft"),
    ("Almanya", "Kntxtr"),
    ("Gürcistan", "Professional Union for Georgian Architects and Urbanists"),
    ("Yunanistan", "AKEA"),
    ("Endonezya", "sindikatdsn"),
    ("İtalya", "unione lavoratrici e lavoratori in architettura (ULLARC)"),
    ("Hollanda", "Better Landscape Architecture (BLA)"),
    ("Hollanda", "Netherlands Angry Architects (NAA!)"),
    ("Yeni Zelanda", "Architectural Ethics NZ"),
    ("Yeni Zelanda", "The Night School"),
    ("Yeni Zelanda", "NZIA"),
    ("Polonya", "antyRAMA"),
    ("Polonya", "Zawód na A"),
    ("Portekiz", "Sintarq"),
    ("İsviçre", "Stop Toxic Architectural Practices (STAP Network)"),
    ("İsviçre", "non-Swiss Architects"),
    ("İsviçre", "Research and Innovation On architecture, urban design and Territory"),
    ("Fransa", "Archi en Colère"),
    ("Birleşik Krallık", "Uncomfortable Questions in Architecture"),
    ("Birleşik Krallık", "Section of Architectural Workers (SAW)"),
    ("Birleşik Krallık", "Future Architects Front (FAF)"),
    ("ABD", "Just Transition Lobby (JTL)"),
    ("ABD", "Architectural Workers United"),
    ("ABD", "The Architecture Lobby (TAL)"),
]

TEMA_GORUNEN = [
    ("01", "ARCHI", "TECTURE &amp; PEDAGOGY", "mimarlik-ve-pedagoji"),
    ("02", "STUDIO", " CULTURE", "studyo-kulturu"),
    ("03", "CURRIC", "ULUM EXPOSURE", "mufredat-teshiri"),
    ("04", "CLASS", " &amp; LABOR", "sinif-ve-emek"),
    ("05", "GEN", "DER", "toplumsal-cinsiyet"),
]

# Manifesto bölümleri: (başlık, küçük, büyük, küçük)
MANIFESTO = [
    ("“Tutku” Maskesinin Deşifresi",
     "Mimarlık ortamında “portfolyo değeri”, “öğrenme süreci” veya “mesleki tutku” gibi "
     "kavramlar, sistematik emek sömürüsünü ve ücretsiz mesai pratiklerini maskelemek için "
     "birer araç olarak kullanılmaktadır.",
     "Tasarım süreçlerinin pürüzsüz estetiği, ofislerdeki ve şantiyelerdeki güvencesiz "
     "çalışma koşullarını ve mimarın bir “işçi-özne” olduğu gerçeğini görünmez kılmaktadır.",
     "Mimarlık emeğinin bir “tutku” gösterisi değil, karşılığı verilmesi gereken politik ve "
     "ekonomik bir hak olarak tanınmasını ve sömürüye dayalı tüm çalışma modellerinin terk "
     "edilmesini talep ediyoruz."),
    ("Üçlü İttifak: Öğrenci, Akademisyen ve Mimarlık İşçisi",
     "Sistem, mimarlık dünyasını yapay hiyerarşiler, unvanlar ve rekabet mekanizmalarıyla "
     "parçalara ayırarak bizleri yalnızlaştırmaktadır. Bizler bu sınırları reddediyoruz.",
     "Öğrenciler, Akademisyenler ve Mimarlık İşçileri olarak, aynı sömürü döngüsünün farklı "
     "özneleriyiz. Stüdyo kültüründeki hiyerarşik baskı, jürilerdeki mobbing, ofislerdeki "
     "ücretsiz mesai ve tutku adı altında meşrulaştırılan sömürü, aynı politik ekonominin "
     "iki yüzüdür.",
     "İnanıyoruz ki; mimarlık eğitimi ve meslek pratiği arasındaki bu kesintisiz sömürü "
     "zinciri, ancak bu üçlü yapının yatay, hiyerarşisiz ve kolektif örgütlenmesiyle "
     "kırılabilir. Dayanışmamız, profesyonel statülerin ötesinde bir sınıf bilincine dayanır."),
    ("Radikal Şeffaflık ve Hesap Verebilirlik",
     "Mimarlık ofislerindeki ve akademi içindeki kapalı kapılar, hiyerarşik sessizlikleri ve "
     "“star” kültürünün yarattığı dokunulmazlıkları radikal bir şeffaflıkla tartışmaya açıyoruz.",
     "Müfredatın ideolojik içeriğini, stüdyo kültüründeki baskı mekanizmalarını ve sektördeki "
     "hiyerarşik yapıları açık forumlar ve yayınlar yoluyla teşhir etmeye devam edeceğiz.",
     ""),
    ("Mimarlığın Ekonomi Politiği: Devlet ve Sermaye Politikaları",
     "Mimarlık eğitimi ve çalışma şartları, devletin neoliberal politikalarından ve sermaye "
     "birikim rejimlerinden bağımsız değerlendirmeyi reddediyoruz.",
     "Mekân üretimini yaşamı desteklemekten çıkarıp bir rant ve yatırım aracına dönüştüren "
     "devlet politikaları, hem üniversite müfredatlarını hem de çalışma koşullarını doğrudan "
     "şekillendirmektedir. Eğitim sistemi, eleştirel düşünceyi dışlayarak piyasanın ve "
     "devletin taleplerine itaatkâr “profesyoneller” yetiştiren bir üretim hattına dönüşmüştür.",
     "Mimarlık tarafsız değildir; her çizgi, her maket ve her yapı, devletin ideolojik "
     "aygıtlarının ve sermayenin önceliklerinin birer iz düşümüdür. Bizler, mimarlığı sadece "
     "bir “tasarım nesnesi” değil, bir sosyal üretim alanı olarak savunuyoruz."),
    ("Ekolojik Adalet ve Sistemsel Eleştiri",
     "Mimarlığın ekolojik krizle olan ilişkisini sadece “yeşil sertifikalar” veya malzeme "
     "seçimi üzerinden değil, yapısal bir sömürü sorunu olarak ele alıyoruz.",
     "Mekân üretiminin yaşamı desteklemekten çıkıp bir yatırım aracına dönüşmesinin, ekolojik "
     "yıkımın temel nedeni olduğunu saptıyoruz. Mimarlık, doğayı ve insanı sadece birer veri "
     "veya malzeme olarak gören, sermaye öncelikli bir yaklaşımın esiri haline getirilmiştir.",
     ""),
    ("Kurumlara Sızmak",
     "Bizler, sistemi dışarıdan izleyen pasif gözlemciler değil, kurumların içindeki "
     "“sızıntılarız”.",
     "Fakülteleri, stüdyoları ve ofisleri; hiyerarşiyi sarsan, sessizliği bozan ve mevcut "
     "yapıyı içeriden dönüştüren birer “hackleme” alanı olarak görüyoruz. Müfredatı teşhir "
     "ediyor, stüdyo kültürünü radikal bir şeffaflıkla tartışmaya açıyor ve bilginin "
     "mülkiyetini reddederek onu kolektifleştiriyoruz.",
     ""),
    ("Küresel Dayanışma ve Direniş",
     "",
     "Yerel huzursuzluklarımızı, küresel bir mücadele zeminiyle birleştiriyoruz. The "
     "Architecture Lobby ve ABC School gibi yapılarla kurduğumuz bağlar, mimarlık emeğinin "
     "sınırları aşan bir örgütlenme sorunu olduğunu teyit etmektedir.",
     ""),
]

MANIFESTO_ACILIS = TEMA_METIN["Mimarlık ve Pedagoji"]

MANIFESTO_KAPANIS = (
    "Bu manifesto bir sonuç değil, sürekli güncellenen bir başlangıçtır. Sadece binaları "
    "değil, mimarlığın yapılış biçimini, emeğin değerini ve eğitimin özünü değiştirmek "
    "isteyen herkesi; bu rahatsız edici soruları birlikte sormaya ve örgütlenmeye davet "
    "ediyoruz."
)


def ag_listesi() -> str:
    satir = "\n".join(
        f'    <li class="ag-satir"><span class="ag-ulke">{html.escape(u)}</span>'
        f'<span class="ag-ad">{html.escape(a)}</span></li>'
        for u, a in AG)
    return f'  <ul class="ag-liste">\n{satir}\n  </ul>'


def tema_listesi(dil, derinlik: int) -> str:
    k = kac(derinlik)
    p = ['  <ul class="tema-liste">']
    for no, kalin, ince, slug in TEMA_GORUNEN:
        p.append(f'    <li class="tema-satir"><a href="{k}{dil}/temalar/#{slug}">'
                 f'<span class="tema-no">{no}</span>'
                 f'<span class="tema-ad"><b>{kalin}</b>{ince}</span>'
                 f'<span class="tema-ok" aria-hidden="true">→</span></a></li>')
    p.append('  </ul>')
    return "\n".join(p)


def manifesto_sayfasi(dil, derinlik=2):
    yol = "manifesto/"
    p = [bas(dil, "Manifesto", MANIFESTO_ACILIS[:150], derinlik, yol),
         ust(dil, "manifesto", derinlik, yol), '<main class="kutu">']
    p.append(etiket("01", "Manifesto"))
    p.append(notlu(dil, f'  <p class="m-vurgu">{MANIFESTO_ACILIS}</p>'))

    for ad, k1, b, k2 in MANIFESTO:
        p.append('  <section class="m-bolum">')
        p.append(f'    <div class="m-baslik">{IKON}<h2>{html.escape(ad)}</h2></div>')
        p.append('    <div class="m-govde">')
        if k1:
            p.append(f'      <p class="m-kucuk">{k1}</p>')
        p.append(f'      <p class="m-buyuk">{b}</p>')
        if k2:
            p.append(f'      <p class="m-kucuk">{k2}</p>')
        p.append('    </div>')
        p.append('  </section>')

    p.append(f'  <p class="m-vurgu">{MANIFESTO_KAPANIS}</p>')

    # Ana sayfadaki soru bağlantısı buraya iniyor.
    p.append(f'  <div class="bolum-etiket" id="sorular"><span class="no">08</span>'
             f'<span>{S(dil, "soru_bolum", n=len(SORULAR))}</span></div>')
    p.append(soru_tablosu(dil))
    p.append('</main>')
    p.append(alt(dil, derinlik))
    return "\n".join(p)


def ana_sayfa(dil, ev, pr, derinlik=1):
    k = kac(derinlik)
    p = [bas(dil, S(dil, "ana_baslik"), giris(dil)[:150], derinlik, ""),
         ust(dil, "", derinlik, ""), '<main class="kutu">']

    p.append(f'  <p class="acilis">{giris(dil)}</p>')

    p.append(etiket("01", S(dil, "b_temalar")))
    p.append('  <div class="serit"><p class="prose-bos" style="margin:0;padding:3rem 0.9rem">'
             + S(dil, "foto_bekliyor") + '</p></div>')
    # Tema listesi kolonun tamamını kullanıyor: yanında açıklama kolonu ve
    # çerçeve yok, satırlar sıkışmasın diye.
    p.append(tema_listesi(dil, derinlik))

    p.append(etiket("02", S(dil, "b_nasil")))
    p.append('  <div class="yan-yana">')
    p.append(f'    <div class="yan-kucuk"><h3>{S(dil, "hack_baslik")}</h3>'
             f'<p>{S(dil, "hack_metin")}</p></div>')
    p.append(f'    <div><p class="prose-bos">{S(dil, "diyagram_bekliyor")}</p></div>')
    p.append('  </div>')

    p.append(etiket("03", S(dil, "b_manifesto")))
    p.append(notlu(dil, f'  <p class="acilis">{MANIFESTO_ACILIS}</p>'))
    p.append(f'  <p class="giris"><a class="daha" href="{k}{dil}/manifesto/">'
             f'{S(dil, "manifesto_tamami")}</a></p>')

    p.append(etiket("04", S(dil, "b_son")))
    p.append('  <ul class="izgara izgara--iri">')
    p += [kart(dil, x, derinlik) for x in ev[:3]]
    p.append('  </ul>')

    p.append(etiket("05", S(dil, "soru_bolum", n=len(SORULAR))))
    p.append(soru_tablosu(dil, sinir=30))
    p.append(f'  <p class="giris">{S(dil, "soru_ilk", n=30)} '
             f'<a class="daha" href="{k}{dil}/manifesto/#sorular">'
             f'{S(dil, "soru_tamami", n=len(SORULAR) - 30)}</a></p>')

    p.append(f'  <div class="bolum-etiket" id="network"><span class="no">06</span>'
             f'<span>{S(dil, "b_ag")}</span></div>')
    p.append(ag_listesi())

    p.append('</main>')
    p.append(alt(dil, derinlik))
    return "\n".join(p)


def kok_sayfasi() -> str:
    """Kökteki index.html — dil seçer ve yönlendirir.

    IP'ye bakmıyoruz: GitHub Pages statik, ziyaretçinin nereden geldiğini
    bilmez. Tarayıcının dil ayarına bakıyoruz — bu zaten kullanıcının kendi
    yazdığı bilgi ve IP'den daha doğru (Berlin'deki Türk öğrenci Türkçe,
    Ankara'daki Erasmus öğrencisi İngilizce görür). Daha önce seçim
    yapılmışsa o kazanır.

    JavaScript kapalıysa aşağıdaki iki bağlantı görünür ve site çalışır."""
    return f"""<!DOCTYPE html>
<html lang="{DILLER[0]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_AD}</title>
<link rel="icon" href="ikon.svg" type="image/svg+xml">
<link rel="alternate" hreflang="tr" href="tr/">
<link rel="alternate" hreflang="en" href="en/">
<link rel="alternate" hreflang="x-default" href="tr/">
<link rel="stylesheet" href="main.style.css">
<script>
(function () {{
  var d = "{DILLER[0]}";
  try {{
    var secili = localStorage.getItem("uqa-dil");
    if (secili === "tr" || secili === "en") {{
      d = secili;
    }} else {{
      var t = (navigator.languages && navigator.languages[0]) || navigator.language || "";
      d = t.toLowerCase().indexOf("tr") === 0 ? "tr" : "en";
    }}
  }} catch (e) {{ /* localStorage kapalı olabilir; varsayılan dil kalır */ }}
  // replace: geri düğmesi ziyaretçiyi buraya geri atıp döngüye sokmasın
  location.replace(d + "/");
}})();
</script>
</head>
<body>
<main class="kutu" style="padding:2rem 14px">
  <p class="giris" style="padding-left:0;padding-right:0">{SITE_AD}</p>
  <ul class="tema-liste" style="padding-left:0;padding-right:0">
    <li class="tema-satir"><a href="tr/" hreflang="tr" data-dil="tr">
      <span class="tema-no">TR</span>
      <span class="tema-ad"><b>TÜRK</b>ÇE</span>
      <span class="tema-ok" aria-hidden="true">→</span></a></li>
    <li class="tema-satir"><a href="en/" hreflang="en" data-dil="en">
      <span class="tema-no">EN</span>
      <span class="tema-ad"><b>ENG</b>LISH</span>
      <span class="tema-ok" aria-hidden="true">→</span></a></li>
  </ul>
</main>
<script src="main.js"></script>
</body>
</html>
"""


def main():
    a = argparse.ArgumentParser(description="Site sayfalarını üretir.")
    a.add_argument("--listele", action="store_true", help="yazma, ne üretileceğini göster")
    s = a.parse_args()

    ev, pr = oku()
    isler = [("index.html", kok_sayfasi())]
    for dil in DILLER:
        isler += [
            (f"{dil}/index.html", ana_sayfa(dil, ev, pr)),
            (f"{dil}/manifesto/index.html", manifesto_sayfasi(dil)),
            (f"{dil}/etkinlikler/index.html",
             liste_sayfasi(dil, "etkinlikler", "Events", ev, 2)),
            (f"{dil}/uretimler/index.html",
             liste_sayfasi(dil, "uretimler", "Works", pr, 2)),
            (f"{dil}/temalar/index.html", temalar_sayfasi(dil, ev, pr)),
            (f"{dil}/iletisim/index.html", iletisim_sayfasi(dil)),
        ]

    for yol, icerik in isler:
        p = KOK / yol
        if not s.listele:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(icerik, encoding="utf-8")
        print(f"  + {yol}  ({len(icerik):,} bayt)")

    if not s.listele:
        print("\nSıradaki: ./bump-version.sh && git add -A && git commit && git push")


if __name__ == "__main__":
    main()
