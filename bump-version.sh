#!/bin/sh
# ---------------------------------------------------------------------------
# Cache-busting: yerel .css ve .js bağlantılarına ?v=YYYYMMDDHHMM damgası basar
# ---------------------------------------------------------------------------
# NEDEN
#   GitHub Pages her dosyaya "Cache-Control: max-age=600" gönderiyor ve bunu
#   değiştiremiyoruz — Pages özel header kabul etmiyor, .htaccess çalışmıyor.
#   O yüzden tek mekanizma adresteki ?v= damgası. Damga değişince tarayıcı
#   dosyayı yeni bir adres sayıp taze indiriyor.
#
# KULLANIM — sıra önemli
#   ./bump-version.sh
#   git add -A
#   git commit -m "..."
#   git push
#   Damgayı basmadan commit edersen hiçbir işe yaramaz.
#
# SINIR
#   Sadece .js ve .css damgalanır. GÖRSELLER VERSİYONLANMAZ: aynı adla bir
#   görseli değiştirirsen ziyaretçiye eskisi gider. Görseli değiştireceksen
#   dosyayı yeniden adlandır.
# ---------------------------------------------------------------------------

set -eu

DAMGA=$(date +%Y%m%d%H%M)
DEGISEN=0
BAKILAN=0

# ---------------------------------------------------------------------------
# NEDEN perl — sed DEĞİL, awk DEĞİL
#
# Git Bash'te awk'ın satır sonlarını bozduğu biliniyor. Ama ölçtük: bu ortamda
# GNU sed 4.9 de aynısını yapıyor.
#
#     printf 'a\r\nb\r\n' | sed -E -i 's|a|A|'
#     önce:  61 0d 0a 62 0d 0a
#     sonra: 41 0a    62 0a        <- dokunulmayan satırda bile \r silinmiş
#
# Çalışma kopyası CRLF olduğu için (core.autocrlf=true) bu, dosyaların baştan
# aşağı değişmiş görünmesine yol açar. perl aynı testte baytları koruyor:
#
#     perl -i -pe 's|a|A|'   ->  41 0d 0a 62 0d 0a
# ---------------------------------------------------------------------------

for f in $(find . -name '*.html' -not -path './.git/*' | sort); do
  BAKILAN=$((BAKILAN + 1))

  # Önce ele: damgalanacak yerel bir bağlantısı yoksa dosyayı hiç açma.
  # https?:// taşıyan satırlar elenir — CDN adresleri sürümü zaten yolunda
  # taşıyor (unpkg.com/leaflet@1.9.4/... gibi), onlara dokunmuyoruz.
  if ! grep -vE 'https?://' "$f" \
     | grep -qE '<(link[^>]+href|script[^>]+src)="[^"]*\.(css|js)'; then
    continue
  fi

  ONCE=$(cat "$f")

  DAMGA="$DAMGA" perl -i -pe '
    next if m{https?://};
    s{(<link[^>]+href=")([^"?]+\.css)(\?v=[0-9]+)?(")}{$1$2?v=$ENV{DAMGA}$4}g;
    s{(<script[^>]+src=")([^"?]+\.js)(\?v=[0-9]+)?(")}{$1$2?v=$ENV{DAMGA}$4}g;
  ' "$f"

  if [ "$ONCE" != "$(cat "$f")" ]; then
    DEGISEN=$((DEGISEN + 1))
    echo "  ~ ${f#./}"
  fi
done

echo "$DAMGA" > VERSION

echo ""
echo "Damga: $DAMGA   ($BAKILAN sayfa tarandı, $DEGISEN tanesi güncellendi)"
echo "Sıradaki: git add -A && git commit && git push"
