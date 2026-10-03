"""Dünya haritası SVG'sini üretir: python lab/harita.py  ->  lab/dunya.svg

Veri: Natural Earth 1:50m (kamu malı). İlk çalışmada lab/.ne/ içine indirilir.
Projeksiyon: Miller. manifesto-map.html içindeki xy() ile AYNI formül; biri
değişirse öbürü de değişmeli, yoksa noktalar haritadan kayar.

Avrupa-Türkiye kutusunda kıyılar ince, dünyanın geri kalanında kaba tutulur.
"""
import json, math, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".ne")
URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/%s.geojson"

K = 10                                    # 1 derece = 10 birim -> dünya 3600 birim genişlik
TOP, BOTTOM = 84, -56                     # Antarktika dışarıda
INCE = (-15, 60, 25, 72)                  # boylam/enlem kutusu: ince detay
TOL_INCE, TOL_KABA = 1.5, 20                # birim cinsinden sadeleştirme eşiği (kıyı)
HASSAS = 2                                # ince kutuda koordinatlar 1/HASSAS birime yuvarlanır
TOL_SINIR = 6                             # ülke sınırları soluk, daha kaba olabilir
MIN_ADA = 300                             # Avrupa dışında bundan küçük adalar atılır (birim²)
LAND, BORDER, BORDER_W = "#ecebe6", "#c8c4bc", 0.56 # sınır: sayfada piksel, resim olarak açılırsa birim


def miller(lat):
    return 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat)))


Y0 = miller(TOP)
SY = K * 180 / math.pi
W, H = 360 * K, round((Y0 - miller(BOTTOM)) * SY)


def xy(lon, lat):
    lat = max(BOTTOM, min(TOP, lat))
    return (lon + 180) * K, (Y0 - miller(lat)) * SY


def load(name):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name + ".geojson")
    if not os.path.exists(p):
        urllib.request.urlretrieve(URL % name, p)
    return json.load(open(p, encoding="utf-8"))


def ince(lon, lat):
    return INCE[0] <= lon <= INCE[1] and INCE[2] <= lat <= INCE[3]


def sadelestir(coords, closed, sabit=None):
    out, last = [], None
    for i, (lon, lat) in enumerate(coords):
        x, y = xy(lon, lat)
        q = HASSAS if ince(lon, lat) and not sabit else 1
        p = (round(x * q) / q, round(y * q) / q)
        tol = sabit or (TOL_INCE if q > 1 else TOL_KABA)
        son = i == len(coords) - 1
        if last is None or son or abs(p[0] - last[0]) + abs(p[1] - last[1]) >= tol:
            if p != last:
                out.append(p)
                last = p
    return out


def alan(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2


def d(pts, closed):
    s = "M" + " ".join("%g %g" % p for p in pts)
    return s + "Z" if closed else s


def geoms(gj):
    for f in gj["features"]:
        g = f["geometry"]
        if g["type"] in ("Polygon", "LineString"):
            yield g["type"], [g["coordinates"]]
        else:
            yield g["type"].replace("Multi", ""), g["coordinates"]


def main():
    land = []
    for kind, parts in geoms(load("ne_50m_land")):
        for poly in parts:
            for ring in poly:
                if max(la for _, la in ring) < -58:
                    continue
                pts = sadelestir(ring, True)
                if len(pts) < 4:
                    continue
                if not any(ince(lo, la) for lo, la in ring) and alan(pts) < MIN_ADA:
                    continue
                land.append(d(pts, True))
    borders = []
    for kind, parts in geoms(load("ne_50m_admin_0_boundary_lines_land")):
        for line in parts:
            if not any(ince(lo, la) for lo, la in line):
                continue  # sınırları sadece Avrupa-Türkiye kutusunda çiz
            pts = sadelestir(line, False, TOL_SINIR)
            if len(pts) >= 2:
                borders.append(d(pts, False))
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
        f'<path fill="{LAND}" d="{"".join(land)}"/>'
        f'<path fill="none" stroke="{BORDER}" stroke-width="{BORDER_W}" vector-effect="non-scaling-stroke" stroke-linejoin="round" d="{"".join(borders)}"/>'
        "</svg>\n"
    )
    out = os.path.join(HERE, "dunya.svg")
    open(out, "w", encoding="utf-8", newline="\n").write(svg)
    print("lab/dunya.svg: %d KB, %dx%d birim" % (len(svg) // 1024, W, H))


if __name__ == "__main__":
    main()
