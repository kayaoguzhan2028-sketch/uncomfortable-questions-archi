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


def bas(baslik: str, aciklama: str, derinlik: int) -> str:
    k = kac(derinlik)
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(baslik)} — {SITE_AD}</title>
<meta name="description" content="{html.escape(aciklama)}">
<link rel="icon" href="{k}ikon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{k}main.style.css">
</head>
<body>
"""


def ust(aktif: str, derinlik: int) -> str:
    """Üç satırlı çerçeveli nav. Bulunduğun sayfa siyah ve altı çizili."""
    k = kac(derinlik)
    baglar = []
    for etiket, yol, kimlik in NAV:
        hedef = f"{k}index.html{yol}" if yol.startswith("#") else f"{k}{yol}"
        simdi = ' aria-current="page"' if kimlik == aktif else ""
        baglar.append(f'<a href="{hedef}"{simdi}>{etiket}</a>')

    uretim_simdi = ' aria-current="page"' if aktif == "uretimler" else ""
    iletisim_simdi = ' aria-current="page"' if aktif == "iletisim" else ""

    return f"""<header class="ust kutu">
  <div class="ust-satir">
    <a class="ust-ikon" href="{k}" aria-label="Ana sayfa">{IKON}</a>
    <span class="ust-ad">{SITE_AD}</span>
    <a class="ust-sag" href="{k}iletisim/"{iletisim_simdi}>Connect</a>
  </div>
  <div class="ust-satir">
    {chr(10).join('    ' + b for b in baglar).strip()}
  </div>
  <div class="ust-satir">
    <a class="ust-genis" href="{k}uretimler/"{uretim_simdi}>Productions / Archive</a>
    <span></span>
    <a class="ust-sag" href="https://www.instagram.com/">Instagram</a>
  </div>
</header>
"""


def alt(derinlik: int) -> str:
    k = kac(derinlik)
    return f"""<footer class="alt kutu">
  <div class="ust-satir">
    <a class="ust-ikon" href="{k}" aria-label="Ana sayfa">{IKON}</a>
    <span class="ust-ad">Sen de bir soru sor</span>
    <a class="ust-sag" href="{k}iletisim/">Connect</a>
  </div>
  <div class="ust-satir">
    <a href="https://www.instagram.com/">Instagram</a>
    <a href="{k}iletisim/">Email</a>
    <span></span>
    <a class="ust-sag" href="{k}iletisim/">How to participate</a>
  </div>
  <p class="alt-metin">{ALT_METIN}</p>
  <div class="ust-satir">
    <a href="{k}#manifesto">Manifesto</a>
    <span></span>
    <a href="{k}temalar/">Themes</a>
    <a class="ust-sag" href="{k}#network">Network</a>
  </div>
  <div class="ust-satir alt-satir--6">
    <a href="{k}etkinlikler/?tip=konferans">Conferences</a>
    <a href="{k}etkinlikler/?tip=podcast">Podcasts</a>
    <a href="{k}etkinlikler/">Activity</a>
    <a href="{k}etkinlikler/?tip=forum">Events</a>
    <a href="{k}uretimler/">Archive</a>
    <a class="ust-sag" href="{k}uretimler/">News/Updates</a>
  </div>
  <div class="ust-satir alt-satir--3">
    <a href="{k}iletisim/">Terms</a>
    <span style="text-align:center">www.uqinarchi.com</span>
    <span class="ust-sag">©2026 All Rights Reserved</span>
  </div>
</footer>

<script src="{k}main.js"></script>
</body>
</html>
"""


def kart(kayit, derinlik: int) -> str:
    """Izgaradaki tek kayıt. Fotoğrafı varsa onu, yoksa soluk işareti gösterir."""
    k = kac(derinlik)
    yol = f"{k}{kayit.klasor.as_posix()}/"
    gorsel = KOK / kayit.klasor / "kapak.webp"
    ic = (f'<img src="{yol}kapak.webp" alt="" loading="lazy">'
          if gorsel.exists() else IKON)
    tip = " / ".join(kayit.tipler) or "—"
    return f"""      <li class="oge">
        <a href="{yol}">
          <span class="oge-gorsel">{ic}</span>
          <span class="oge-tarih">{html.escape(kayit.tarih.yazi())}</span><br>
          <span class="oge-tip">{html.escape(tip)}</span>
          <span class="oge-metin">{html.escape(kayit.baslik)}</span>
        </a>
      </li>"""


def liste_sayfasi(ad, aktif, baslik, kayitlar, derinlik):
    ilk, kalan = kayitlar[:3], kayitlar[3:]
    p = [bas(baslik, GIRIS[:150], derinlik), ust(aktif, derinlik), '<main class="kutu">']
    p.append(f'  <p class="giris">{GIRIS}</p>')

    p.append(f'  <div class="bolum-ust"><h2>Latest {baslik}</h2>'
             f'<a class="daha" href="#hepsi">Load more ↓</a></div>')
    p.append('  <ul class="izgara izgara--iri">')
    p += [kart(x, derinlik) for x in ilk]
    p.append('  </ul>')

    p.append(f'  <div class="bolum-ust" id="hepsi"><h2>All {baslik}</h2>'
             f'<span class="daha">{len(kayitlar)} kayıt</span></div>')
    p.append('  <ul class="izgara izgara--sik">')
    p += [kart(x, derinlik) for x in kalan]
    p.append('  </ul>')

    p.append('</main>')
    p.append(alt(derinlik))
    return "\n".join(p)


def temalar_sayfasi(ev, pr, derinlik=1):
    p = [bas("Themes", "Beş ana tema.", derinlik), ust("temalar", derinlik),
         '<main class="kutu">', '  <div class="akordeon">']

    for i, (ad, slug) in enumerate(TEMALAR):
        e = [x for x in ev if ad in x.temalar]
        u = [x for x in pr if ad in x.temalar]
        metin = TEMA_METIN.get(ad, "")
        govde = f'<p>{metin}</p>' if metin else \
            '<p class="prose-bos">Bu temanın metni henüz girilmedi.</p>'

        tipler = collections.Counter(t for x in e for t in x.tipler)
        utipler = collections.Counter(t for x in u for t in x.tipler)
        etiket = lambda c: ", ".join(f"{a} ({n})" for a, n in c.most_common(5)) or "—"

        p.append(f'    <details{" open" if i == 0 else ""}>')
        p.append(f'      <summary>{html.escape(ad)}</summary>')
        p.append(f'      <div class="akordeon-govde">{govde}')
        p.append(f'        <p class="metin-ikincil"><b>Activities:</b> {etiket(tipler)}'
                 f' &nbsp;·&nbsp; <b>Productions:</b> {etiket(utipler)}'
                 f' &nbsp;·&nbsp; {len(e)} etkinlik, {len(u)} üretim</p>')
        p.append(f'        <ul>')
        for x in (e + u)[:8]:
            p.append(f'          <li><a href="{kac(derinlik)}{x.klasor.as_posix()}/">'
                     f'{html.escape(x.tarih.yazi())} — {html.escape(x.baslik[:70])}</a></li>')
        p.append('        </ul>')
        p.append('      </div>')
        p.append('    </details>')

    p.append('  </div>')

    p.append('  <div class="bolum-ust"><h2>Bu temalardan çıkanlar</h2>'
             f'<a class="daha" href="{kac(derinlik)}etkinlikler/">Hepsi ↓</a></div>')
    p.append('  <ul class="izgara izgara--orta">')
    p += [kart(x, derinlik) for x in ev[:8]]
    p.append('  </ul>')

    p.append('</main>')
    p.append(alt(derinlik))
    return "\n".join(p)


def iletisim_sayfasi(derinlik=1):
    return bas("Connect", "İletişim ve katılım.", derinlik) + ust("iletisim", derinlik) + """<main class="kutu">
  <div class="giris">
    <h1 class="iletisim-baslik">Sen de bir soru sor.<br>Listeyi birlikte büyütelim.</h1>
  </div>

  <div class="iletisim">
    <div class="iletisim-bilgi">
      <dl>
        <dt>Toplantılar</dt>
        <dd>Açık. Üyelik yok, aidat yok, hiyerarşi yok.</dd>
        <dt>Nerede</dt>
        <dd>Ankara — ve çevrimiçi</dd>
        <dt>Instagram</dt>
        <dd><a href="https://www.instagram.com/">@uncomfortablequestionsarch</a></dd>
        <dt>YouTube</dt>
        <dd><a href="https://www.youtube.com/@uncomfortablequestionsarch">@uncomfortablequestionsarch</a></dd>
        <dt>E-posta</dt>
        <dd><a href="mailto:merhaba@uqinarchi.com">merhaba@uqinarchi.com</a></dd>
      </dl>
    </div>

    <div class="iletisim-form">
      <h2>Get in touch</h2>

      <!-- ÖNEMLİ: GitHub Pages statik bir sunucu, form verisini alacak bir
           arka uç YOK. Bu form şu an hiçbir yere göndermiyor.
           Çalışması için action'a bir form servisi adresi koymak gerekiyor
           (Formspree, Basin, Web3Forms gibi — ücretsiz planları var).
           Seçildiğinde tek satır: <form action="https://..." method="post"> -->
      <form action="" method="post">
        <div class="form-satir">
          <label>Ad <span aria-hidden="true">*</span>
            <input type="text" name="ad" required autocomplete="given-name">
          </label>
          <label>Soyad
            <input type="text" name="soyad" autocomplete="family-name">
          </label>
        </div>
        <div class="form-satir">
          <label>E-posta <span aria-hidden="true">*</span>
            <input type="email" name="eposta" required autocomplete="email">
          </label>
          <label>Kurum / okul
            <input type="text" name="kurum" autocomplete="organization">
          </label>
        </div>
        <label>Neyle ilgilisin?
          <select name="ilgi">
            <option value="">Seç…</option>
            <option>Toplantılara katılmak</option>
            <option>Bir soru önermek</option>
            <option>Üretime katkı (yazı, fanzin, podcast)</option>
            <option>Kendi okulumda etkinlik</option>
            <option>Diğer</option>
          </select>
        </label>
        <label>Mesajın
          <textarea name="mesaj" rows="6" placeholder="Sormak istediğin rahatsız edici soru…"></textarea>
        </label>
        <label class="form-onay">
          <input type="checkbox" name="onay" required>
          <span>Mesajımın kolektifle paylaşılmasını kabul ediyorum.</span>
        </label>
        <button type="submit">Gönder</button>
        <p class="form-not">
          Form şu an bir yere bağlı değil — kurulana kadar
          <a href="mailto:merhaba@uqinarchi.com">e-posta</a> ile yazabilirsin.
        </p>
      </form>
    </div>
  </div>
</main>
""" + alt(derinlik)


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


def tema_listesi(derinlik: int) -> str:
    k = kac(derinlik)
    p = ['    <ul class="tema-liste">']
    for no, kalin, ince, slug in TEMA_GORUNEN:
        p.append(f'      <li class="tema-satir"><a href="{k}etkinlikler/?tema={slug}">'
                 f'<span class="tema-no">{no}</span>'
                 f'<span class="tema-ad"><b>{kalin}</b>{ince}</span>'
                 f'<span class="tema-ok" aria-hidden="true">→</span></a></li>')
    p.append('    </ul>')
    return "\n".join(p)


def manifesto_sayfasi(derinlik=1):
    p = [bas("Manifesto", MANIFESTO_ACILIS[:150], derinlik),
         ust("manifesto", derinlik), '<main class="kutu">']
    p.append(etiket("01", "Manifesto"))
    p.append(f'  <p class="m-vurgu">{MANIFESTO_ACILIS}</p>')

    for i, (ad, k1, b, k2) in enumerate(MANIFESTO, start=2):
        p.append('  <section class="m-bolum">')
        p.append(f'    <div class="m-baslik">{IKON}<h2>{html.escape(ad)}</h2></div>')
        p.append('    <div class="m-govde">')
        if k1: p.append(f'      <p class="m-kucuk">{k1}</p>')
        p.append(f'      <p class="m-buyuk">{b}</p>')
        if k2: p.append(f'      <p class="m-kucuk">{k2}</p>')
        p.append('    </div>')
        p.append('  </section>')

    p.append(f'  <p class="m-vurgu">{MANIFESTO_KAPANIS}</p>')
    p.append('</main>')
    p.append(alt(derinlik))
    return "\n".join(p)


def ana_sayfa(ev, pr, derinlik=0):
    p = [bas("mimarlıkta rahatsız edici sorular", GIRIS[:150], derinlik),
         ust("", derinlik), '<main class="kutu">']

    p.append(f'  <p class="acilis">{GIRIS}</p>')

    p.append(etiket("01", "Themes"))
    p.append('  <div class="serit"><p class="prose-bos" style="margin:0;padding:3rem 0.9rem">'
             'Kolektif fotoğrafı buraya gelecek.</p></div>')

    p.append(etiket("02", "Nasıl çalışıyoruz"))
    p.append('  <div class="yan-yana">')
    p.append('    <div class="yan-kucuk"><h3>Hacking the institution</h3>'
             '<p>Kurumları dışarıdan izlemiyoruz; içeriden dönüştürüyoruz. '
             'Fakülteler, stüdyolar ve ofisler birer tartışma alanı.</p></div>')
    p.append('    <div><p class="prose-bos">Ağ diyagramı buraya gelecek.</p></div>')
    p.append('  </div>')

    p.append(etiket("03", "Manifesto"))
    p.append(f'  <p class="acilis">{MANIFESTO_ACILIS}</p>')
    p.append(f'  <p class="giris"><a class="daha" href="{kac(derinlik)}manifesto/">'
             'Manifestonun tamamı →</a></p>')

    p.append('  <div class="tema-blok">')
    p.append('    <div class="yan-kucuk"><p>Çalışmalarımız beş ana tema etrafında '
             'şekilleniyor. Her tema, disiplinin sessiz kaldığı bir noktaya açılan '
             'tartışma kapısıdır.</p></div>')
    p.append('    <div>')
    p.append(tema_listesi(derinlik))
    p.append('    </div>')
    p.append('  </div>')

    p.append(etiket("04", "Latest activities"))
    p.append('  <ul class="izgara izgara--iri">')
    p += [kart(x, derinlik) for x in ev[:3]]
    p.append('  </ul>')

    p.append(etiket("05", "80+ rahatsız edici soru"))
    p.append(f'  <p class="giris"><a class="daha" href="{kac(derinlik)}manifesto/#sorular">'
             'Soruların tamamı →</a></p>')

    p.append(etiket("06", "Our network"))
    p.append(ag_listesi())

    p.append('</main>')
    p.append(alt(derinlik))
    return "\n".join(p)


def main():
    a = argparse.ArgumentParser(description="Site sayfalarını üretir.")
    a.add_argument("--listele", action="store_true", help="yazma, ne üretileceğini göster")
    s = a.parse_args()

    ev, pr = oku()
    isler = [
        ("index.html", ana_sayfa(ev, pr)),
        ("manifesto/index.html", manifesto_sayfasi()),
        ("etkinlikler/index.html", liste_sayfasi("Activity", "etkinlikler", "Events", ev, 1)),
        ("uretimler/index.html", liste_sayfasi("Works", "uretimler", "Works", pr, 1)),
        ("temalar/index.html", temalar_sayfasi(ev, pr)),
        ("iletisim/index.html", iletisim_sayfasi()),
    ]

    for yol, icerik in isler:
        p = KOK / yol
        if s.listele:
            print(f"  + {yol}  ({len(icerik):,} bayt)")
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(icerik, encoding="utf-8")
        print(f"  + {yol}  ({len(icerik):,} bayt)")

    if not s.listele:
        print("\nSıradaki: ./bump-version.sh && git add -A && git commit && git push")


if __name__ == "__main__":
    main()
