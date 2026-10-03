"""RTF <-> düz kod dönüştürücü (Webflow embed'leri için).

Gelen RTF'ler Mac TextEdit'in düz metin olarak kaydettiği kod. Bu araç:
  python lab/rtf.py oku   dosya.rtf          -> kodu ekrana basar
  python lab/rtf.py ver   lab/sayfa.html     -> EMBED işaretleri arasındaki kodu
                                                lab/cikti/sayfa.html ve .rtf olarak yazar

Sayfalarda Webflow'a gidecek kısım şu iki işaretin arasındadır; dışındaki her
şey sadece önizleme içindir ve geri gönderilmez:
  <!-- EMBED BAŞLA -->
  <!-- EMBED BİTİR -->
"""
import os
import re
import sys

BS = "\\"
BASLA = "<!-- EMBED BAŞLA -->"
BITIR = "<!-- EMBED BİTİR -->"

# Gelen dosyalardaki başlığın birebir aynısı
HEADER = (
    r"{\rtf1\ansi\ansicpg1252\cocoartf2822" "\n"
    r"\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}" "\n"
    r"{\colortbl;\red255\green255\blue255;}" "\n"
    r"{\*\expandedcolortbl;;}" "\n"
    r"\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0" "\n"
    r"\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0" "\n"
    "\n"
    r"\f0\fs24 \cf0 "
)


def rtf_to_text(rtf):
    body = rtf.split(BS + "cf0 ", 1)[1]
    out, i, n = [], 0, len(body)
    while i < n:
        c = body[i]
        if c == BS:
            nxt = body[i + 1] if i + 1 < n else ""
            if nxt in "\\{}":
                out.append(nxt); i += 2
            elif nxt == "\n":
                out.append("\n"); i += 2
            elif nxt == "'":
                out.append(bytes([int(body[i + 2:i + 4], 16)]).decode("cp1252")); i += 4
            else:
                m = re.match(r"\\([a-z]+)(-?\d+)? ?", body[i:])
                word, num = m.group(1), m.group(2)
                if word == "u":
                    v = int(num)
                    out.append(chr(v + 65536 if v < 0 else v))
                elif word in ("tab",):
                    out.append("\t")
                # \uc0 ve diğer biçim komutları atlanır
                i += m.end()
        elif c == "}" and i == n - 1:
            i += 1  # belgeyi kapatan son süslü parantez
        else:
            out.append(c); i += 1
    return "".join(out)


def text_to_rtf(text):
    out = []
    uc_set = False
    for ch in text:
        if ch in "\\{}":
            out.append(BS + ch)
        elif ch == "\n":
            out.append(BS + "\n")
            uc_set = False  # TextEdit \uc0'ı her satırda yeniden yazar
        elif ch == "\t":
            out.append(BS + "tab ")
        elif ord(ch) < 128:
            out.append(ch)
        else:
            try:
                b = ch.encode("cp1252")
                out.append("%s'%02x" % (BS, b[0]))
            except UnicodeEncodeError:
                v = ord(ch)
                if v > 32767:
                    v -= 65536
                out.append(("" if uc_set else BS + "uc0") + "%su%d " % (BS, v))
                uc_set = True
    return HEADER + "".join(out) + "}"


def embed_from_page(html):
    a = html.index(BASLA) + len(BASLA)
    b = html.index(BITIR)
    return html[a:b].strip("\n") + "\n"


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    sys.stdout.reconfigure(encoding="utf-8")
    sys.dont_write_bytecode = True
    if cmd == "oku":
        print(rtf_to_text(open(path, encoding="latin-1").read()), end="")
    elif cmd == "ver":
        code = embed_from_page(open(path, encoding="utf-8").read()).rstrip("\n")
        name = os.path.splitext(os.path.basename(path))[0]
        outdir = os.path.join(os.path.dirname(os.path.abspath(path)), "cikti")
        os.makedirs(outdir, exist_ok=True)
        rtf = text_to_rtf(code)
        assert rtf_to_text(rtf) == code, "RTF gidiş-dönüş tutmadı"
        open(os.path.join(outdir, name + ".html"), "w", encoding="utf-8", newline="\n").write(code + "\n")
        open(os.path.join(outdir, name + ".rtf"), "w", encoding="ascii", newline="\n").write(rtf)
        print("yazıldı:", os.path.join(outdir, name + ".rtf"), "+ .html")
    else:
        sys.exit("komut: oku | ver")


if __name__ == "__main__":
    main()
