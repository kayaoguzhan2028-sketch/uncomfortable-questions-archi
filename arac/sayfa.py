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

# Kolektifin adı iki dilde. İngilizcesi "disturbing" DEĞİL — kolektifin
# kendi kullandığı ad "Uncomfortable Questions in Architecture".
SITE_ADI = {
    "tr": "Mimarlıkta Rahatsız Edici Sorular",
    "en": "Uncomfortable Questions in Architecture",
}

# Açılıştaki iri başlığın satır kırılması. Tarayıcıya bırakırsak kolon
# genişliğine göre rastgele yerden kırıyor; ad iki parça olarak okunmalı.
SITE_SATIR = {
    "tr": ["Mimarlıkta", "Rahatsız Edici Sorular"],
    "en": ["Uncomfortable Questions", "in Architecture"],
}
SITE_AD = SITE_ADI["tr"]

# SAYFALAR — dil başına dört tane. manifesto ve temalar ayrı sayfa değil,
# ana sayfanın bölümleri; nav onlara çapa (#) ile iniyor.
# Yayındaki dosya adları İngilizce — nav'daki sekmelerle aynı kelimeler.
# Kaynak ağacı (kayit/) Türkçe kalıyor: orası depo, yayın değil.
# index.html SADECE ana sayfa; sunucu bir klasör istendiğinde onu servis
# ettiği için adı zorunlu, diğerlerinin değil.
SAYFA_ILETISIM = "contact.html"   # tek gerçek ayrı sayfa

# Ana sayfadaki sekmelerin çapaları. Sekme = ayrı sayfa DEĞİL: aynı
# index.html içindeki pano, :target ile açılıyor. JavaScript gerekmiyor,
# adres çubuğunda kalıyor, geri düğmesi ve paylaşma çalışıyor.
SEKME_ACILIS = "about"

# Nav'daki sekmeler. Her biri ana sayfada bir GÖRÜNÜM açıyor: ana akış
# gizleniyor, o görünüm tek başına kalıyor. Yeni sayfa yüklenmiyor,
# sayfa aşağı da kaymıyor.
# (metin anahtarı, çapa). Etiket burada YAZILI DEĞİL: iki dilde de aynı
# olsun diye METIN sözlüğünden geliyor.
SEKMELER = [
    ("n_temalar", "temalar"),
    ("n_manifesto", "manifesto"),
    ("n_activity", "activity"),
    ("n_network", "network"),
    ("n_archive", "archive"),
]

# kayit/ içindeki bölüm adı -> yayındaki klasör adı
BOLUM_YOL = {"etkinlikler": "activity", "uretimler": "archive"}


def sayfa_yolu(kayit) -> str:
    """activity/2026-1-mayis-tandogan.html — kaydın yayındaki adresi."""
    bolum, ad = kayit.klasor.parts
    return f"{BOLUM_YOL[bolum]}/{ad}.html"

# Site iki dilde üretiliyor: tr/ ve en/. İlk dil varsayılan.
# Site şu an TEK DİL üretiliyor. İngilizce makinesi (METIN sözlüğünün "en"
# kanadı, hreflang, nav'daki dil düğmesi) olduğu gibi duruyor — silinmedi,
# sadece üretimden çıkarıldı. Çeviriler hazır olduğunda burada "en" eklemek
# yetiyor; kayıtların İngilizce metni kendi klasöründe yazi.en.md olarak
# bekliyor.
DILLER = ("tr",)
TEK_DIL = len(DILLER) == 1

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
        "kunye": "2024 Ankara bağımsız kolektif",
        "alt_iletisim": "iletişim",
        "hepsi_baslik": "Tamamı",
        "b_etkinlikler": "etkinlikler",
        "b_latest": "latest",
        "b_next": "next",
        "soru_baslik": "2024 yılında sorduğumuz rahatsız edici sorular",
        "b_activity": "etkinlikler",
        "b_archive": "üretimler",
        "geri": "← kapat",
        "siniflanmamis": "sınıflandırılmamış",
        "n_home": "ana sayfa",
        "n_temalar": "temalar",
        "n_manifesto": "manifesto",
        "n_activity": "etkinlikler",
        "n_network": "ağ",
        "n_archive": "üretimler",
        "n_sorular": "sorular",
        "n_contact": "iletişim",
        "n_orneklem": "örneklem",
        "n_menu": "menü",
        "n_sartlar": "Koşullar",
        "ag_gorsel_notu": "Buraya ağ diyagramı görseli gelecek.",
        "tema_hepsi": "Temaların tamamı →",
        "ag_yerel": "yerel ağ",
        "ag_yerel_not": "Türkiye'de birlikte çalıştığımız yapılar:",
        "b_uretimler": "üretimler",
        "tema_not": "Çalışmalarımız beş ana tema etrafında şekilleniyor. Her tema, "
                    "disiplinin sessiz kaldığı bir noktaya açılan tartışma kapısıdır.",
        "manifesto_not": "Bu manifesto bir sonuç değil, sürekli güncellenen bir başlangıç.",
        "ag_uluslararasi": "uluslararası ağ",
        "ag_not": "Mimarlık emeği sınırları aşan bir örgütlenme sorunu. "
                  "Bağ kurduğumuz yapılar:",
        "son_not": "En yeni etkinlikler. Tamamı arşivde.",
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
        "kunye": "2024 Ankara independent collective",
        "alt_iletisim": "get in touch",
        "hepsi_baslik": "All of it",
        "b_etkinlikler": "events",
        "b_latest": "latest",
        "b_next": "next",
        "soru_baslik": "The uncomfortable questions we asked in 2024",
        "b_activity": "activities",
        "b_archive": "works",
        "geri": "← close",
        "siniflanmamis": "unclassified",
        "n_home": "home",
        "n_temalar": "themes",
        "n_manifesto": "manifesto",
        "n_activity": "activity",
        "n_network": "network",
        "n_archive": "works",
        "n_sorular": "questions",
        "n_contact": "connect",
        "n_orneklem": "samples",
        "n_menu": "menu",
        "n_sartlar": "Terms &amp; Conditions",
        "ag_gorsel_notu": "The network diagram image goes here.",
        "tema_hepsi": "All themes →",
        "ag_yerel": "local network",
        "ag_yerel_not": "The structures we work alongside in Turkey:",
        "b_uretimler": "works",
        "tema_not": "Our work takes shape around five themes. Each opens a door onto "
                    "a point where the discipline has kept quiet.",
        "manifesto_not": "This manifesto is not a conclusion but a beginning kept "
                         "under revision.",
        "ag_uluslararasi": "international network",
        "ag_not": "Architectural labour is a question of organising across borders. "
                  "The structures we are tied to:",
        "son_not": "The most recent activities. All of them are in the archive.",
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
# Şemadaki sekmeler, küçük harfle. CSS'te text-transform YOK — metnin
# kendisi küçük yazılı (büyük harfe çevirmek Türkçe'de i/İ'yi bozuyor).
# İlk ikisi ve sonuncusu ana sayfadaki bölüme iniyor, ayrı sayfa yok.
# İlk dördü ana sayfadaki sekme, beşincisi gerçek sayfa.
NAV = ([(anahtar, f"index.html#{capa}", capa) for anahtar, capa in SEKMELER]
       # Örneklem sitenin kökünde, dil ağacının dışında: tek kopya,
       # tr/ ve en/ aynı sayfaya bağlanıyor. Yolun başındaki "/" bunu söylüyor.
       + [("n_orneklem", "/orneklem/index.html", "orneklem")])

# Sağ üstteki "menu" panelinde duranlar — nav'a sığmayan her şey.
MENU = [
    ("n_home", "index.html"),
    ("n_temalar", "index.html#temalar"),
    ("n_sorular", "index.html#sorular"),
    ("n_manifesto", "index.html#manifesto"),
    ("n_activity", "index.html#activity"),
    ("n_network", "index.html#network"),
    ("n_archive", "index.html#archive"),
    ("n_contact", SAYFA_ILETISIM),
    ("n_orneklem", "/orneklem/index.html"),
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
    # Tek dilde hreflang yazmıyoruz: var olmayan bir dile işaret eden
    # alternatif, arama motoruna kırık bir adres bildirmek olur.
    if TEK_DIL:
        alternatif = ""
    else:
        ot = S(dil, "oteki")
        alternatif = (
            f'<link rel="alternate" hreflang="{dil}" href="{k}{dil}/{yol}">' + chr(10)
            + f'<link rel="alternate" hreflang="{ot}" href="{k}{ot}/{yol}">' + chr(10))
    return f"""<!DOCTYPE html>
<html lang="{dil}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(baslik)} — {SITE_ADI[dil]}</title>
<meta name="description" content="{html.escape(aciklama)}">
<link rel="icon" href="{k}ikon.svg" type="image/svg+xml">
<link rel="icon" href="{k}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{k}apple-touch-icon.png">
{alternatif}<link rel="stylesheet" href="{k}main.style.css">
</head>
<body>
"""


def ust(dil: str, aktif: str, derinlik: int, yol: str) -> str:
    """Tek satır nav: solda işaret, ortada sekmeler, sağda menü.

    yol: dil kökünden sonraki kısım ('', 'iletisim.html', ...). Dil düğmesi
    öteki dilde AYNI sayfaya gitsin diye lazım."""
    k = kac(derinlik)
    if TEK_DIL:
        dil_dugmesi = ""
    else:
        ot, ot_ad = S(dil, "oteki"), S(dil, "oteki_ad")
        dil_dugmesi = (
            '      <hr>' + chr(10)
            + f'      <a class="ust-dil" href="{k}{ot}/{yol}" data-dil="{ot}"'
            + f' hreflang="{ot}">{ot_ad} — {S(ot, 'dil_ad')}</a>' + chr(10))

    bu_sayfa = yol or "index.html"

    def hedefle(hedef_yol):
        """Hedef zaten bulunduğumuz sayfaysa SADECE çapa yaz.

        '../tr/index.html#temalar' yazarsak tarayıcı bunu yeni bir adres
        sayıp sayfayı baştan yüklüyor: tıklayınca sayfa kaydırmak yerine
        sıfırlanıyor ve bir an ham HTML görünüyor."""
        # "/" ile başlayan hedef dil ağacının DIŞINDA, sitenin kökünde
        # (örneklem böyle: tek kopya, tr/ ve en/ ikisi de ona bağlanıyor).
        if hedef_yol.startswith("/"):
            return f"{k}{hedef_yol[1:]}"
        dosya, _, capa = hedef_yol.partition("#")
        if (dosya or "index.html") == bu_sayfa:
            return f"#{capa}" if capa else "#"
        return f"{k}{dil}/{hedef_yol}"

    baglar = []
    for anahtar, hedef_yol, kimlik in NAV:
        simdi = ' aria-current="page"' if kimlik == aktif else ""
        baglar.append(f'<a href="{hedefle(hedef_yol)}"{simdi}>'
                      f'{S(dil, anahtar)}</a>')

    menu = [f'      <a href="{hedefle(h)}">{S(dil, e)}</a>' for e, h in MENU]

    return f"""<header class="ust kutu">
  <a class="ust-ikon" href="{k}{dil}/index.html" aria-label="{SITE_ADI[dil]}">{IKON}</a>
  <nav class="ust-nav">
    {(chr(10) + '    ').join(baglar)}
  </nav>
  <details class="menu">
    <summary>{S(dil, "n_menu")}</summary>
    <div class="menu-panel">
{chr(10).join(menu)}
      <hr>
      <a href="https://www.instagram.com/">instagram</a>
      <a href="mailto:merhaba@uqinarchi.com">email</a>
{dil_dugmesi}    </div>
  </details>
</header>
"""


def alt(dil: str, derinlik: int) -> str:
    k = kac(derinlik)
    # Footer üstü şerit görsel. Dosya yoksa etiket hiç yazılmıyor — kırık
    # görsel ya da boş yer tutucu bırakmıyoruz.
    serit = (f'<div class="alt-gorsel kutu"><img src="{k}alt-gorsel.webp" alt=""></div>'
             if (KOK / "alt-gorsel.webp").exists() else "")
    return serit + f"""
<footer class="alt kutu">
  <div class="alt-ust">
    <div class="alt-cagri">
      <a href="{k}{dil}/{SAYFA_ILETISIM}">{S(dil, "alt_soru")} →</a>
      <a href="{k}{dil}/{SAYFA_ILETISIM}">{S(dil, "alt_iletisim")} →</a>
    </div>
    <div class="alt-baglar">
      <a href="{k}{dil}/index.html#temalar">{S(dil, "n_temalar")}</a>
      <a href="{k}{dil}/index.html#manifesto">{S(dil, "n_manifesto")}</a>
      <a href="{k}{dil}/index.html#archive">{S(dil, "n_archive")}</a>
      <a href="{k}{dil}/index.html#network">{S(dil, "n_network")}</a>
      <a href="{k}{dil}/index.html#activity">{S(dil, "n_activity")}</a>
      <span class="bosluk"></span>
      <a href="https://www.instagram.com/">instagram</a>
      <a href="mailto:merhaba@uqinarchi.com">email</a>
      <a href="https://www.facebook.com/">facebook</a>
      {IKON}
    </div>
  </div>
  <p class="alt-metin">{alt_metin(dil)}</p>
  <div class="alt-kunye">
    <span>©2026 All Rights Reserved</span>
    <a href="{k}{dil}/{SAYFA_ILETISIM}">{S(dil, "n_sartlar")}</a>
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
    sayfa = f"{k}{dil}/{sayfa_yolu(kayit)}"
    gorsel = KOK / kayit.kaynak / "kapak.webp"
    ic = (f'<img src="{k}{kayit.kaynak.as_posix()}/kapak.webp" alt="" loading="lazy">'
          if gorsel.exists() else IKON)
    # Kalın satır kaydın ADI. (Önce tipi yazıyordu: ızgarada yan yana on
    # kart "Açık Ders / Atölye" diyordu, hangisi olduğu okunmuyordu. Tip
    # zaten grubun başlığı — kartta tekrar etmesine gerek yok.)
    # En altta temaların etiketleri: kart neye dair olduğunu kendi söylüyor.
    # Excel'in tema sütununda sitenin beş teması dışında serbest etiketler de
    # var (Örgütlenme, Kent, Mekan…) ve dokuz kayıtta beş-yedi tanesi birden.
    # HEPSİ yazılıyor, kesilmiyor: kaydın hangi temalarda durduğu kartta
    # eksiksiz görünsün. Sıra: önce sitenin kendi temaları, sonra ötekiler.
    resmi = [a for a, _ in TEMALAR]
    sirali = sorted(kayit.temalar, key=lambda t: (t not in resmi, kayit.temalar.index(t)))
    etiketler = "".join(f'<span class="oge-tema">{html.escape(t)}</span>'
                        for t in sirali)
    tema_satiri = f'\n          <span class="oge-temalar">{etiketler}</span>' if etiketler else ""
    return f"""      <li class="oge">
        <a href="{sayfa}">
          <span class="oge-gorsel">{ic}</span>
          <span class="oge-tip">{html.escape(kayit.baslik)}
            <span class="oge-ok" aria-hidden="true">→</span></span>
          <span class="oge-tarih">{html.escape(kayit.tarih.yazi())}</span>{tema_satiri}
        </a>
      </li>"""


def tema_akordeonu(dil, ev, pr, derinlik):
    """Temaların açılır listesi. Gerçek kayıtlara açılıyor: '?tema=' gibi
    çalışmayan bir filtre bağlantısı kullanmıyoruz — site JavaScript'siz
    de tam çalışsın diye."""
    k = kac(derinlik)
    p = ['      <div class="akordeon">']
    for (ad, slug), (no, _b, _i, _s) in zip(TEMALAR, TEMA_GORUNEN):
        e = [x for x in ev if ad in x.temalar]
        u = [x for x in pr if ad in x.temalar]
        # Summary'deki küçük kapak: temanın KENDİ görseli yok — o temadaki
        # en yeni kaydın kapağını gösteriyoruz. Yani temayı temsil etmiyor,
        # "bu temada en son şu yapıldı" diyor. Temaya ait bir görsel
        # üretilirse burası ona bakacak şekilde değişir.
        kapakli = next((x for x in (e + u)
                        if (KOK / x.kaynak / "kapak.webp").exists()), None)
        kucuk = (f'<span class="akordeon-kapak">'
                 f'<img src="{k}{kapakli.kaynak.as_posix()}/kapak.webp" alt="" loading="lazy">'
                 f'</span>' if kapakli else '<span class="akordeon-kapak"></span>')
        p.append(f'        <details id="tema-{slug}">')
        p.append(f'          <summary>{kucuk}<span>{no} &nbsp; {html.escape(ad)}</span></summary>')
        p.append('          <div class="akordeon-govde">')
        metin = TEMA_METIN.get(ad, "")
        if metin:
            p.append(notlu(dil, f'            <p>{metin}</p>'))
        p.append(f'            <p class="metin-ikincil">{len(e)} {S(dil, "etkinlikler")}'
                 f' &nbsp;·&nbsp; {len(u)} {S(dil, "uretimler")}</p>')
        hepsi = (e + u)[:10]
        if hepsi:
            p.append('            <ul>')
            for x in hepsi:
                p.append(f'              <li><a href="{k}{dil}/{sayfa_yolu(x)}">'
                         f'{html.escape(x.tarih.yazi())} — '
                         f'{html.escape(x.baslik[:70])}</a></li>')
            p.append('            </ul>')
        else:
            p.append(f'            <p class="metin-ikincil">{S(dil, "tema_bos")}</p>')
        p.append('          </div>')
        p.append('        </details>')
    p.append('      </div>')
    return "\n".join(p)


def arsiv_sayfasi(dil, ev, pr, derinlik=1):
    """archive.html — 128 kaydın tamamı. Etkinlikler ve üretimler ayrı
    bölümlerde, ama tek sayfada: 'arşiv' ikisini birden kastediyor."""
    yol = SAYFA_URETIM
    p = [bas(dil, "Archive", giris(dil)[:150], derinlik, yol),
         ust(dil, "uretimler", derinlik, yol), '<main class="kutu">']

    p.append('  <div class="blok">')
    p.append(f'    <div><h1 class="blok-etiket">archive</h1>'
             f'<p class="blok-not">{len(ev) + len(pr)} {S(dil, "kayit")}</p></div>')
    p.append(f'    <p class="acilis">{giris(dil)}</p>')
    p.append('  </div>')

    for baslik, grup in ((S(dil, "b_etkinlikler"), ev), (S(dil, "b_uretimler"), pr)):
        p.append('  <div class="blok">')
        p.append(f'    <div><h2 class="blok-etiket">{baslik}</h2>'
                 f'<p class="blok-not">{len(grup)} {S(dil, "kayit")}</p></div>')
        p.append('    <div>')
        p.append('      <ul class="izgara izgara--iri">')
        p += [kart(dil, x, derinlik) for x in grup[:6]]
        p.append('      </ul>')
        p.append('      <ul class="izgara izgara--sik">')
        p += [kart(dil, x, derinlik) for x in grup[6:]]
        p.append('      </ul>')
        p.append('    </div>')
        p.append('  </div>')

    p.append('</main>')
    p.append(alt(dil, derinlik))
    return "\n".join(p)


def iletisim_sayfasi(dil, derinlik=1):
    yol = SAYFA_ILETISIM
    return bas(dil, S(dil, "n_contact"), S(dil, "il_form"), derinlik, yol) \
        + ust(dil, "iletisim", derinlik, yol) + f"""<main class="kutu">
  <div class="blok">
    <p class="blok-etiket">connect</p>
    <h1 class="hero-baslik">{S(dil, "il_baslik")}</h1>
  </div>

  <div class="blok">
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

# Yerel ağ — şemada uluslararası ağın altında ikinci bir grup var.
# Kurum listesi henüz verilmedi; boş kaldığı sürece bölüm HİÇ yazılmıyor.
# Uydurma kurum adı koymuyoruz. Liste gelince buraya eklenecek, tek satır.
AG_YEREL = []

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


def ag_grubu(baslik, not_, kurumlar, kirp=46) -> str:
    """Tek ağ grubu.

    Adlar önce 90° döndürülmüş dikey yazıydı; o hâl yatay kaydırma çubuğu
    getiriyordu ve listenin sağı ekran dışında kalıyordu. Artık sarmalayan
    düz bir liste: kaydırma yok, hepsi tek bakışta görünüyor."""
    satir = []
    for u, a in kurumlar:
        kisa = a if len(a) <= kirp else a[:kirp - 1].rstrip() + "…"
        satir.append(
            f'      <li><span class="ag-ulke">{html.escape(u)}</span>'
            f'<span class="ag-ad" title="{html.escape(a)}">'
            f'{html.escape(kisa)}</span></li>')
    return f"""  <div class="blok">
    <div>
      <h2 class="blok-etiket">{baslik}</h2>
      <p class="blok-not">{not_}</p>
    </div>
    <ul class="ag-liste">
{chr(10).join(satir)}
    </ul>
  </div>"""


def ag_listesi(dil) -> str:
    p = [gorsel_notu(S(dil, "ag_gorsel_notu")),
         ag_grubu(S(dil, "ag_uluslararasi"), S(dil, "ag_not"), AG)]
    if AG_YEREL:
        p.append(ag_grubu(S(dil, "ag_yerel"), S(dil, "ag_yerel_not"), AG_YEREL))
    return "\n".join(p)


def tema_listesi(dil, derinlik: int) -> str:
    k = kac(derinlik)
    p = ['    <div class="blok">',
         f'    <div><h2 class="blok-etiket">{S(dil, "b_temalar")}</h2>'
         f'<p class="blok-not">{S(dil, "tema_not")}</p></div>',
         '    <ul class="tema-liste">']
    for no, kalin, ince, slug in TEMA_GORUNEN:
        p.append(f'      <li class="tema-satir"><a href="#tema-{slug}">'
                 f'<span class="tema-no">{no}</span>'
                 f'<span class="tema-ad"><b>{kalin}</b>{ince}</span>'
                 f'<span class="tema-ok" aria-hidden="true">→</span></a></li>')
    p += ['    </ul>', '    </div>']
    return "\n".join(p)


def manifesto_bolumu(dil):
    """Ana sayfadaki manifesto bölümü. Ayrı sayfa değil — nav oraya iniyor."""
    # id dıştaki <section>'da duruyor. Burada tekrar yazsak aynı id iki kere
    # geçer; HTML geçersiz olur ve tarayıcı çapayı ilkine bağlar.
    p = ['  <div class="blok">',
         f'    <div><h2 class="blok-etiket">{S(dil, "b_manifesto")}</h2>'
         f'<p class="blok-not">{S(dil, "manifesto_not")}</p></div>',
         '    <div>']
    p.append(notlu(dil, f'      <p class="m-vurgu">{MANIFESTO_ACILIS}</p>'))
    for ad, k1, b, k2 in MANIFESTO:
        p.append('      <section class="m-bolum">')
        p.append(f'        <div class="m-baslik">{IKON}<h3>{html.escape(ad)}</h3></div>')
        p.append('        <div class="m-govde">')
        if k1:
            p.append(f'          <p class="m-kucuk">{k1}</p>')
        p.append(f'          <p class="m-buyuk">{b}</p>')
        if k2:
            p.append(f'          <p class="m-kucuk">{k2}</p>')
        p.append('        </div>')
        p.append('      </section>')
    p.append(f'      <p class="m-vurgu">{MANIFESTO_KAPANIS}</p>')
    p += ['    </div>', '  </div>']
    return "\n".join(p)


def gorsel_yeri(ad, k, bekleme_metni, girinti="      ") -> str:
    """Kök dizindeki bir görseli basar; yoksa kesikli yer tutucu.

    Dosya gelmeden <img> yazmıyoruz: kırık görsel simgesi, boş bir kutudan
    daha kötü görünür ve ziyaretçi bunu hata sanar."""
    varmi = (KOK / ad).exists()
    if varmi:
        return (f'{girinti}<div class="hero-foto">'
                f'<img src="{k}{ad}" alt="" loading="lazy"></div>')
    return (f'{girinti}<div class="hero-foto"><p class="prose-bos" '
            f'style="margin:0;padding:5rem 1rem;text-align:center">'
            f'{bekleme_metni} <code>{ad}</code></p></div>')


def gorunum(capa, baslik, icerik, dil, k) -> str:
    """Tek başına açılan görünüm.

    :target ile açılıyor: adres çubuğunda kalıyor, geri düğmesi çalışıyor,
    bağlantısı paylaşılabiliyor ve JavaScript gerekmiyor."""
    return "\n".join([
        f'  <section class="gorunum" id="{capa}">',
        '    <div class="gorunum-ust">',
        f'      <h1>{baslik}</h1>',
        f'      <a class="gorunum-kapat" href="#">{S(dil, "geri")}</a>',
        '    </div>',
        icerik,
        '  </section>',
    ])


def taksonomi(dil, kayitlar, derinlik, anahtar):
    """Kayıtları bir ölçüte göre gruplar ve her grubu kendi ızgarasında verir.

    anahtar: kayıttan etiket listesi çıkaran fonksiyon. Bir kayıt birden
    fazla gruba girebilir (bir etkinlik hem 'Konferans' hem 'Atölye'
    olabiliyor) — kopyalamıyoruz, gerçekten ikisinde de duruyor."""
    gruplar = collections.defaultdict(list)
    for x in kayitlar:
        # Tipi boş kayıtlar da bir gruba girmeli, yoksa listeden düşerler.
        # Excel'de 13 kayıt henüz sınıflandırılmamış durumda.
        for e in (anahtar(x) or [S(dil, "siniflanmamis")]):
            gruplar[e].append(x)

    # Her grup açılıp kapanıyor: 20 grubun hepsi birden açıkken sayfa
    # metrelerce uzuyordu, aranan tip görünmüyordu. <details> ile —
    # akordeondaki gibi tarayıcının kendi işi, JavaScript yok, klavyeyle
    # de açılıyor. En kalabalık grup açık başlıyor ki sayfa boş görünmesin.
    p = []
    for i, ad in enumerate(sorted(gruplar, key=lambda a: (-len(gruplar[a]), a))):
        icinde = gruplar[ad]
        acik = " open" if i == 0 else ""
        p.append(f'    <details class="blok blok--katlanir"{acik}>')
        p.append(f'      <summary><div><h2 class="blok-etiket">{html.escape(ad)}</h2>'
                 f'<p class="blok-not">{len(icinde)} {S(dil, "kayit")}</p></div>'
                 f'<span class="blok-arti" aria-hidden="true"></span></summary>')
        p.append('      <ul class="izgara izgara--orta">')
        p += [kart(dil, x, derinlik) for x in icinde]
        p.append('      </ul>')
        p.append('    </details>')
    return "\n".join(p)


def ozet_bagi(dil, capa, anahtar) -> str:
    """Ana akıştaki özetin altındaki 'tamamı' bağlantısı — görünümü açar."""
    return ('  <div class="blok"><div></div>'
            f'<p><a class="daha" href="#{capa}">{S(dil, anahtar)}</a></p></div>')


def gorsel_notu(metin) -> str:
    """'Buraya görsel gelecek' notu. Taslak sunumunda neyin eksik olduğu
    belli olsun diye; görsel gelince bu satır silinir."""
    return ('  <div class="blok"><div></div>'
            f'<p class="gorsel-notu">{metin}</p></div>')


def ana_sayfa(dil, ev, pr, derinlik=1):
    """Ana sayfa.

    Varsayılan hali: uzun akış, her bölüm ÖZET. Nav'daki bir sekmeye
    basılınca bu akış gizleniyor ve o sekmenin tam görünümü tek başına
    açılıyor — yeni sayfa yüklenmiyor, sayfa aşağı da kaymıyor."""
    k = kac(derinlik)
    p = [bas(dil, SITE_ADI[dil], giris(dil)[:150], derinlik, ""),
         ust(dil, "", derinlik, ""), '<main class="kutu">']

    # ===================== ANA AKIŞ (varsayılan) =====================
    p.append('<div class="ana-akis">')

    p.append('  <div class="blok">')
    p.append(f'    <p class="blok-etiket">{S(dil, "kunye")}</p>')
    p.append('    <div>')
    p.append('      <h1 class="hero-baslik">'
             + "<br>".join(SITE_SATIR[dil]) + '</h1>')
    p.append(gorsel_yeri("kolektif.webp", k, S(dil, "foto_bekliyor")))
    p.append('    </div>')
    p.append('  </div>')

    p.append(f'  <section class="blok" id="{SEKME_ACILIS}">')
    p.append('    <h2 class="blok-etiket">about</h2>')
    p.append('    <div>')
    p.append(f'      <p class="acilis">{giris(dil)}</p>')
    p.append(f'      <p class="alt-metin">{alt_metin(dil)}</p>')
    p.append('    </div>')
    p.append('  </section>')

    # Temalar — 5 satır, devamı görünümde
    p.append(tema_listesi(dil, derinlik))
    p.append(ozet_bagi(dil, "temalar", "tema_hepsi"))

    # Sorular
    p.append('  <div class="blok">')
    p.append('    <div></div>')
    p.append(gorsel_yeri("sorular.webp", k, S(dil, "foto_bekliyor"), "    "))
    p.append('  </div>')
    p.append('  <div class="blok" id="sorular">')
    p.append(f'    <h2 class="blok-etiket">{S(dil, "soru_bolum", n=len(SORULAR))}</h2>')
    p.append('    <div>')
    p.append(f'      <h3 class="bolum-baslik">{S(dil, "soru_baslik")}</h3>')
    p.append(soru_tablosu(dil))
    p.append('    </div>')
    p.append('  </div>')

    # Manifesto — açılış paragrafı, tamamı görünümde
    p.append('  <div class="blok">')
    p.append(f'    <div><h2 class="blok-etiket">{S(dil, "b_manifesto")}</h2>'
             f'<p class="blok-not">{S(dil, "manifesto_not")}</p></div>')
    p.append('    <div>')
    p.append(notlu(dil, f'      <p class="m-vurgu">{MANIFESTO_ACILIS}</p>'))
    p.append('    </div>')
    p.append('  </div>')
    p.append(ozet_bagi(dil, "manifesto", "manifesto_tamami"))

    # Ağ
    p.append(ag_listesi(dil))

    # Son işler
    p.append('  <div class="blok">')
    p.append(f'    <div><h2 class="blok-etiket">{S(dil, "b_latest")}</h2>'
             f'<p class="blok-not">{S(dil, "son_not")}</p></div>')
    p.append('    <div>')
    p.append('      <ul class="izgara izgara--iri">')
    p += [kart(dil, x, derinlik) for x in ev[:8]]
    p.append('      </ul>')
    p.append('    </div>')
    p.append('  </div>')
    p.append(ozet_bagi(dil, "activity", "hepsi_ok"))

    p.append('</div>')

    # ===================== GÖRÜNÜMLER =====================
    tema_ic = "\n".join([
        tema_listesi(dil, derinlik),
        '    <div class="blok">', '      <div></div>', '      <div>',
        tema_akordeonu(dil, ev, pr, derinlik),
        '      </div>', '    </div>',
    ])
    p.append(gorunum("temalar", S(dil, "b_temalar"), tema_ic, dil, k))

    p.append(gorunum("manifesto", S(dil, "b_manifesto"),
                     manifesto_bolumu(dil), dil, k))

    p.append(gorunum("activity", S(dil, "b_activity"),
                     taksonomi(dil, ev, derinlik, lambda x: x.tipler), dil, k))

    p.append(gorunum("network", S(dil, "ag_uluslararasi"),
                     ag_listesi(dil), dil, k))

    arsiv_ic = "\n".join([
        taksonomi(dil, pr, derinlik, lambda x: x.tipler),
    ])
    p.append(gorunum("archive", S(dil, "b_archive"), arsiv_ic, dil, k))

    p.append('</main>')
    p.append(alt(dil, derinlik))
    return "\n".join(p)


def kok_sayfasi() -> str:
    """Kokteki index.html.

    Site su an TEK DIL. Burada secilecek bir sey olmadigi icin sayfa
    dogrudan tr/'ye yonlendiriyor; eskiden duran TR/EN secici kaldirildi.

    Ikinci dil acildiginda buraya secici geri gelecek: tercih (localStorage),
    sonra tarayicinin dili, sonra varsayilan. IP'ye bakmiyoruz -- GitHub
    Pages statik, ziyaretcinin nereden geldigini bilmez.

    JavaScript kapaliysa asagidaki baglanti gorunur ve site calisir."""
    d = DILLER[0]
    return f"""<!DOCTYPE html>
<html lang="{d}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_ADI[d]}</title>
<link rel="icon" href="ikon.svg" type="image/svg+xml">
<link rel="icon" href="favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="canonical" href="{d}/index.html">
<meta http-equiv="refresh" content="0; url={d}/index.html">
<script>
// replace: geri dugmesi ziyaretciyi buraya geri atip donguye sokmasin
location.replace("{d}/index.html");
</script>
<link rel="stylesheet" href="main.style.css">
</head>
<body>
<main class="kutu" style="padding:2rem 14px">
  <p class="giris" style="padding-left:0;padding-right:0">{SITE_AD}</p>
  <ul class="tema-liste" style="padding-left:0;padding-right:0">
    <li class="tema-satir"><a href="{d}/index.html" hreflang="{d}">
      <span class="tema-no">01</span>
      <span class="tema-ad"><b>SİTEYE</b> GİR</span>
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
            (f"{dil}/{SAYFA_ILETISIM}", iletisim_sayfasi(dil)),
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
