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
EXCEL = KOK / "Activity List.xlsx"

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

AY_NO = {ay.lower(): i + 1 for i, ay in enumerate(AYLAR)}

TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

# "Üretim Tipi" sütununa tip yerine aktivite ID'si sızmış birkaç satır var
# (UQA-010, UQA-011, UQA-048). Bunlar tip değil; boş sayılır.
ID_DESENI = re.compile(r"^UQA-\d+$", re.I)

# Video kayıtlarında YouTube linki kendi sütununda değil, "Aktivite Drive Adı"
# sütununa "YT_link: https://..." diye yazılmış. Oradan çekiyoruz.
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


def tarih_coz(tam: str, yil: str, ay: str, gun: str) -> Tarih:
    """
    Excel'de tarih üç ayrı yerde ve üç ayrı formatta duruyor:
      G (Tam Tarih): '17.05.2024' | '2025-04-02' | '19.09.2026-20.09.2026'
      D/E/F        : '2024' | 'Mayıs' | '17.0'
    Hangisi doluysa ondan çıkarıyoruz; G önceliklidir çünkü aralıkları o taşıyor.
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
    # üretime özel
    yazar: str = ""
    dil: str = ""
    dosya_turu: str = ""
    kaynak_link: str = ""
    kontrol_notu: str = ""
    drive_adi: str = ""
    video: str = ""               # YouTube video kimliği (11 karakter)
    slug: str = ""

    @property
    def klasor(self) -> Path:
        """etkinlikler/2024/05-17-baslik/  |  uretimler/tarihsiz/baslik/"""
        kok = "etkinlikler" if self.tur == "etkinlik" else "uretimler"
        if not self.tarih.var_mi:
            return Path(kok) / "tarihsiz" / self.slug
        onek = self.tarih.klasor()
        ad = f"{onek}-{self.slug}" if onek else self.slug
        return Path(kok) / str(self.tarih.yil) / ad

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

    etkinlikler = []
    for r in _satirlar(z, "xl/worksheets/sheet1.xml", ss)[1:]:
        if not r.get("C"):
            continue
        etkinlikler.append(Kayit(
            tur="etkinlik",
            baslik=r["C"],
            tarih=tarih_coz(r.get("G", ""), r.get("D", ""), r.get("E", ""), r.get("F", "")),
            sehir=r.get("H", ""),
            mekan=r.get("I", ""),
            tipler=_parcala(r.get("J", "")),
            temalar=_parcala(r.get("K", "")),
            etiketler=_parcala(r.get("L", "")),
            network=r.get("M", ""),
            drive_adi=r.get("B", ""),
        ))

    uretimler = []
    for r in _satirlar(z, "xl/worksheets/sheet2.xml", ss)[1:]:
        if not r.get("C"):
            continue
        tip = r.get("H", "")
        b = r.get("B", "")
        vid = video_id(b)
        uretimler.append(Kayit(
            video=vid,
            tur="uretim",
            baslik=r["C"],
            tarih=tarih_coz(r.get("G", ""), r.get("D", ""), r.get("E", ""), r.get("F", "")),
            tipler=[] if ID_DESENI.match(tip) else _parcala(tip),
            temalar=_parcala(r.get("I", "")),
            etiketler=_parcala(r.get("J", "")),
            network=r.get("K", ""),
            yazar=r.get("L", ""),
            dil=r.get("M", ""),
            dosya_turu=r.get("N", ""),
            kaynak_link=r.get("O", ""),
            kontrol_notu=r.get("P", ""),
            drive_adi="" if vid else b,
        ))

    for grup in (etkinlikler, uretimler):
        _slug_ata(grup)
        grup.sort(key=lambda k: k.tarih.sirala(), reverse=True)

    return etkinlikler, uretimler


def _slug_ata(kayitlar: list[Kayit]) -> None:
    """Slug üretir; aynı klasöre düşen iki kayıt olursa sonuna -2, -3 ekler."""
    kullanilan: set[str] = set()
    for k in kayitlar:
        temel = slug(k.baslik)
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
