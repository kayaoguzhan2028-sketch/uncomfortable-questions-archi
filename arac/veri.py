#!/usr/bin/env python3
"""
Excel'i okuyup düzgün kayıtlara çeviren ortak modül.

Diğer script'ler (iskele.py, sayfa.py) Excel'in kendisiyle uğraşmaz; hepsi
buradan okur. Excel'in dağınıklığı — tarih formatlarının üç farklı yazılışı,
tip sütununa sızmış ID'ler, eksik yıllar — TEK yerde, burada temizlenir.

Excel repoya girmiyor (.gitignore). Bu modül onu yerelde okur.
"""

import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent

# Kayıtların malzeme kökü. Sayfalar tr/ ve en/ altında üretilir;
# metin, ham fotoğraf ve webp burada tek kopya durur.
KAYNAK_KOK = "kayit"
EXCEL = KOK / "Activity List last.xlsx"

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

AY_NO = {ay.lower(): i + 1 for i, ay in enumerate(AYLAR)}

TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

# "Üretim Tipi" sütununa tip yerine aktivite ID'si sızmış birkaç satır var
# (UQA-010, UQA-011, UQA-048). Bunlar tip değil; boş sayılır.
ID_DESENI = re.compile(r"^UQA-\d+$", re.I)

# YouTube linkinden 11 karakterlik video kimliği. Link youtu.be/, watch?v=
# ya da embed/ biçiminde gelebiliyor, sonunda ?si=... takibi olabiliyor.
YT_DESENI = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]{11})")


def video_id(metin: str) -> str:
    """YouTube linkinden video kimliğini çıkarır. Bulamazsa boş döner."""
    m = YT_DESENI.search(metin or "")
    return m.group(1) if m else ""

# Sayfa klasör adı bu uzunluğu aşmasın — bazı podcast başlıkları 120 karakter.
SLUG_SINIR = 60


def slug(metin: str, sinir: int = SLUG_SINIR) -> str:
    """Başlığı klasör/URL adına çevirir. Uzunsa kelime sınırından keser."""
    metin = metin.translate(TR)
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    metin = re.sub(r"[^a-zA-Z0-9]+", "-", metin).strip("-").lower()
    if len(metin) > sinir:
        kesik = metin[:sinir].rsplit("-", 1)[0]
        metin = kesik or metin[:sinir]
    return metin.strip("-") or "isimsiz"


def kisa_ad(baslik: str, sinir: int = 42) -> str:
    """
    Başlıktan klasör adı üretir. Excel'deki başlıklar uzun ve tekrarlı:
      "Ankara, 10 Ekim, 15 Temmuz: Yas, Hafıza ve Mekan | ... Cevaplar #2"
    Bunu "yas-hafiza-ve-mekan"a indiriyoruz. Kural:
      - "|" sonrası seri adıdır, atılır
      - ":" varsa asıl konu sonrasındadır, o alınır
      - podcast bölümleri ayrı: bölüm numarası kaybolmasın
    """
    m = re.search(r"Podcast[iı]?\s*[-–]\s*(\d+)\s*[-–]\s*([^:]*)", baslik, re.I)
    if m:
        return f"podcast-{int(m.group(1)):02d}-{slug(m.group(2).strip(), 30)}"

    t = baslik.split("|")[0].strip()
    t = re.sub(r"^.*?:\s*", "", t, count=1)
    return slug(t, sinir)


def _link(deger: str) -> str:
    """Excel'de linklerin bir kısmı https:// olmadan yazılmış
    ('open.spotify.com/episode/...'). Tarayıcı onu göreli yol sanar."""
    deger = (deger or "").strip()
    if deger and not re.match(r"^[a-z]+://", deger, re.I):
        deger = "https://" + deger
    return deger


def _parcala(deger: str) -> list[str]:
    """Virgülle ayrılmış çoklu alanı listeye çevirir."""
    return [p.strip() for p in (deger or "").split(",") if p.strip()]


@dataclass
class Tarih:
    """Bir kaydın tarihi. Aralık olabilir, hiç olmayabilir."""
    yil: int | None = None
    ay: int | None = None
    gun: int | None = None
    bitis: tuple[int, int, int] | None = None   # aralıksa bitiş (y, a, g)
    ham: str = ""

    @property
    def var_mi(self) -> bool:
        return self.yil is not None

    def sirala(self) -> tuple:
        """Kronolojik sıralama anahtarı. Tarihsizler en sona."""
        if not self.var_mi:
            return (0, 0, 0)
        return (self.yil, self.ay or 0, self.gun or 0)

    def klasor(self) -> str:
        """Yıl içindeki klasör öneki: '05-17'. Alfabetik sıra = kronolojik sıra."""
        if self.ay and self.gun:
            return f"{self.ay:02d}-{self.gun:02d}"
        if self.ay:
            return f"{self.ay:02d}"
        return ""

    def yazi(self) -> str:
        """Sayfada görünecek hali: '17 Mayıs 2024', '19–20 Eylül 2026'."""
        if not self.var_mi:
            return "Tarih belirsiz"
        ay_adi = AYLAR[self.ay - 1] if self.ay else ""
        if self.bitis:
            by, ba, bg = self.bitis
            if (by, ba) == (self.yil, self.ay):
                return f"{self.gun}–{bg} {ay_adi} {self.yil}"
            b_ay = AYLAR[ba - 1] if ba else ""
            return f"{self.gun} {ay_adi} – {bg} {b_ay} {by}"
        if self.gun:
            return f"{self.gun} {ay_adi} {self.yil}"
        if self.ay:
            return f"{ay_adi} {self.yil}"
        return str(self.yil)

    def iso(self) -> str:
        """<time datetime="..."> için makine okuur hali."""
        if not self.var_mi:
            return ""
        if self.ay and self.gun:
            return f"{self.yil:04d}-{self.ay:02d}-{self.gun:02d}"
        if self.ay:
            return f"{self.yil:04d}-{self.ay:02d}"
        return f"{self.yil:04d}"


def _tek_tarih(parca: str) -> tuple[int, int | None, int | None] | None:
    """Tek bir tarihi çözer. Excel'de dört ayrı yazılış var, dördü de burada."""
    parca = parca.strip()
    m = re.match(r"^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$", parca)      # 17.05.2024
    if m:
        g, a, y = (int(x) for x in m.groups())
        return (y, a, g)
    m = re.match(r"^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})$", parca)      # 2025-04-02
    if m:
        y, a, g = (int(x) for x in m.groups())
        return (y, a, g)
    m = re.match(r"^(\d{4})[.\-/](\d{1,2})$", parca)                     # 2025-06 (gün yok)
    if m:
        y, a = (int(x) for x in m.groups())
        return (y, a, None)
    m = re.match(r"^(\d{4})$", parca)                                    # 2025 (sadece yıl)
    if m:
        return (int(m.group(1)), None, None)
    return None


def tarih_coz(tam: str, yil: str = "", ay: str = "", gun: str = "") -> Tarih:
    """
    Tam Tarih sütunu: '17.05.2024' | '2025-04-02' | '2025-11' |
    '19.09.2026-20.09.2026'. Eski Excel'de tarih ayrıca yıl/ay/gün diye üç
    sütuna bölünmüştü ('2024' | 'Mayıs' | '17.0'); yil/ay/gun onlar için,
    tam boşsa ya da çözülemezse kullanılır.
    """
    t = Tarih(ham=tam or "")

    if tam:
        # ÖNCE tümünü tek tarih olarak dene. Bu sıra önemli: '2025-04-02'
        # aralık ayıracına da uyuyor, bölersek yıl olarak okunup gün kaybolur.
        tek = _tek_tarih(tam.strip())
        if tek:
            t.yil, t.ay, t.gun = tek
            return t

        # Tek tarih değilse aralık olabilir: '19.09.2026-20.09.2026'
        parcalar = re.split(r"\s*[-–]\s*(?=\d{1,2}[.\-/]\d)", tam.strip())
        if len(parcalar) == 2:
            bas, son = _tek_tarih(parcalar[0]), _tek_tarih(parcalar[1])
            if bas:
                t.yil, t.ay, t.gun = bas
                if son and son != bas:
                    t.bitis = son
                return t

    # G yoksa / çözülemediyse D-E-F sütunlarına düş
    if yil and yil.strip().isdigit():
        t.yil = int(yil.strip())
    if ay:
        t.ay = AY_NO.get(ay.strip().lower())
    if gun:
        m = re.match(r"^(\d{1,2})", gun.strip())      # '17.0' -> 17
        if m:
            t.gun = int(m.group(1))

    # Yıl yoksa gün/ay tek başına anlamsız
    if t.yil is None:
        t.ay = t.gun = None

    return t


@dataclass
class Kayit:
    """Bir etkinlik ya da bir üretim."""
    tur: str                      # 'etkinlik' | 'uretim'
    baslik: str
    tarih: Tarih
    tipler: list[str] = field(default_factory=list)
    temalar: list[str] = field(default_factory=list)
    etiketler: list[str] = field(default_factory=list)
    network: str = ""
    # etkinliğe özel
    sehir: str = ""
    mekan: str = ""
    # sayfanın metni: özet başlığın altında, uzun yazı içeriğin altında
    ozet: str = ""
    uzun: str = ""
    # etkinliğe özel bağlantılar
    ig_link: str = ""
    spotify_link: str = ""
    # üretime özel
    yazar: str = ""
    dil: str = ""
    dosya_turu: str = ""
    pdf_link: str = ""
    anket_link: str = ""
    podcast_link: str = ""
    video: str = ""               # YouTube video kimliği (11 karakter)
    slug: str = ""

    @property
    def klasor(self) -> Path:
        """etkinlikler/2026-1-mayis-tandogan/  |  uretimler/tarihsiz-md-1927-sunumu/

        Tek seviye. Sıralama klasör adından değil, Excel'deki tarihten
        yapılıyor; o yüzden ada ay-gün koymaya gerek yok."""
        kok = "etkinlikler" if self.tur == "etkinlik" else "uretimler"
        yil = self.tarih.yil if self.tarih.var_mi else "tarihsiz"
        return Path(kok) / f"{yil}-{self.slug}"

    @property
    def kaynak(self) -> Path:
        """kayit/etkinlikler/2026-1-mayis-tandogan/

        Kaydın MALZEMESİ: yazi.md, ham/ ve webp çıktıları. Dilden bağımsız,
        çünkü fotoğraf iki dilde de aynı — tr/ ve en/ altına kopyalanırsa
        her fotoğraf repoda iki kere durur. Üretilen HTML tr/ ve en/ altına,
        malzeme buraya."""
        return Path(KAYNAK_KOK) / self.klasor

    @property
    def url(self) -> str:
        return "/" + self.klasor.as_posix() + "/"

    @property
    def derinlik(self) -> int:
        """Sayfadan köke kaç seviye çıkmak gerekiyor (CSS yolu için)."""
        return len(self.klasor.parts)


def _satirlar(z: zipfile.ZipFile, yol: str, ss: list[str]) -> list[dict]:
    out = []
    for row in ET.fromstring(z.read(yol)).iter(NS + "row"):
        hucre = {}
        for c in row.findall(NS + "c"):
            sutun = "".join(ch for ch in c.get("r") if ch.isalpha())
            t = c.get("t")
            v = c.find(NS + "v")
            isl = c.find(NS + "is")
            if t == "s" and v is not None:
                deger = ss[int(v.text)]
            elif isl is not None:
                deger = "".join(x.text or "" for x in isl.iter(NS + "t"))
            elif v is not None:
                deger = v.text or ""
            else:
                deger = ""
            if deger.strip():
                hucre[sutun] = deger.strip()
        if hucre:
            out.append(hucre)
    return out


def oku(excel: Path = EXCEL) -> tuple[list[Kayit], list[Kayit]]:
    """Excel'i okur, (etkinlikler, üretimler) döner. İkisi de en yeni önce sıralı."""
    if not excel.exists():
        raise SystemExit(f"Excel bulunamadı: {excel}")

    z = zipfile.ZipFile(excel)
    ss = ["".join(t.text or "" for t in si.iter(NS + "t"))
          for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si")]

    # "Activity List last.xlsx" sütunları. Sütun harfi değişirse SADECE
    # burası değişir; diğer script'ler Kayit alanlarını okur, harfleri değil.
    #
    # Etkinlikler: A no · B ad · C tam tarih · D bitiş · E şehir · F mekan ·
    #   G tip · H temalar · I etiketler · J network · K özet · L uzun ·
    #   M IG · N YouTube · O Spotify
    # Üretimler:   A etkinlik no · B ad · C tarih · D tip · E temalar ·
    #   F etiketler · G network · H yazar · I dil · J dosya türü · K özet ·
    #   L uzun · M pdf · N video · O anket · P podcast
    etkinlikler = []
    for r in _satirlar(z, "xl/worksheets/sheet1.xml", ss)[1:]:
        if not r.get("B"):
            continue
        tarih = tarih_coz(r.get("C", ""))
        # Bitiş ayrı sütunda da gelebilir; C zaten aralık değilse ekle.
        bitis = _tek_tarih(r.get("D", "")) if r.get("D", "") not in ("", "-") else None
        if bitis and not tarih.bitis and tarih.var_mi and bitis != (tarih.yil, tarih.ay, tarih.gun):
            tarih.bitis = bitis
        etkinlikler.append(Kayit(
            tur="etkinlik",
            baslik=r["B"],
            tarih=tarih,
            sehir=r.get("E", ""),
            mekan=r.get("F", ""),
            tipler=_parcala(r.get("G", "")),
            temalar=_parcala(r.get("H", "")),
            etiketler=_parcala(r.get("I", "")),
            network=r.get("J", ""),
            ozet=r.get("K", ""),
            uzun=r.get("L", ""),
            ig_link=_link(r.get("M", "")),
            video=video_id(r.get("N", "")),
            spotify_link=_link(r.get("O", "")),
        ))

    uretimler = []
    for r in _satirlar(z, "xl/worksheets/sheet2.xml", ss)[1:]:
        if not r.get("B"):
            continue
        tip = r.get("D", "")
        uretimler.append(Kayit(
            tur="uretim",
            baslik=r["B"],
            tarih=tarih_coz(r.get("C", "")),
            tipler=[] if ID_DESENI.match(tip) else _parcala(tip),
            temalar=_parcala(r.get("E", "")),
            etiketler=_parcala(r.get("F", "")),
            network=r.get("G", ""),
            yazar=r.get("H", ""),
            dil=r.get("I", ""),
            dosya_turu=r.get("J", ""),
            ozet=r.get("K", ""),
            uzun=r.get("L", ""),
            pdf_link=_link(r.get("M", "")),
            video=video_id(r.get("N", "") or r.get("P", "")),
            anket_link=_link(r.get("O", "")),
            podcast_link=_link(r.get("P", "")),
        ))

    for grup in (etkinlikler, uretimler):
        _slug_ata(grup)
        grup.sort(key=lambda k: k.tarih.sirala(), reverse=True)

    return etkinlikler, uretimler


def _slug_ata(kayitlar: list[Kayit]) -> None:
    """Slug üretir; aynı klasöre düşen iki kayıt olursa sonuna -2, -3 ekler."""
    kullanilan: set[str] = set()
    for k in kayitlar:
        temel = kisa_ad(k.baslik)
        aday, n = temel, 2
        while True:
            k.slug = aday
            yol = k.klasor.as_posix()
            if yol not in kullanilan:
                kullanilan.add(yol)
                break
            aday = f"{temel}-{n}"
            n += 1


if __name__ == "__main__":
    ev, pr = oku()
    print(f"{len(ev)} etkinlik, {len(pr)} üretim okundu.\n")
    print("--- En yeni 3 etkinlik ---")
    for k in ev[:3]:
        print(f"  {k.tarih.yazi():24} {k.klasor}")
    print("\n--- Tarihsiz üretimler ---")
    for k in pr:
        if not k.tarih.var_mi:
            print(f"  {k.klasor}")
