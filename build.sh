#!/usr/bin/env bash
# ==========================================================
#  SkyRiseBank - skrypt budowania
#  Autor: SkyRise
#
#  Wymagania: JDK 25 (kompilacja) + Maven 3.9+
#  Wynikowy jar jest zgodny z Javą 21 (--release 21).
#  Wynik: release/SkyRiseBank.jar (wersja pluginu nadal w plugin.yml)
# ==========================================================
set -euo pipefail

cd "$(dirname "$0")"

# JDK 25 (API FancyNpcs jest zbudowane dla Javy 25), jeżeli JAVA_HOME nie jest ustawione
if [ -z "${JAVA_HOME:-}" ]; then
    for jdk in /usr/lib/jvm/java-25-openjdk-amd64 /usr/lib/jvm/java-25-openjdk /usr/lib/jvm/jdk-25*; do
        if [ -d "$jdk" ]; then
            export JAVA_HOME="$jdk"
            break
        fi
    done
fi
[ -n "${JAVA_HOME:-}" ] && echo "==> JAVA_HOME=$JAVA_HOME"

echo "==> Budowanie SkyRiseBank..."
mvn -B clean package "$@"

VERSION="$(grep -oP '(?<=<plugin.version>)[^<]+' pom.xml)"
JAR="target/SkyRiseBank.jar"

if [ ! -f "$JAR" ]; then
    echo "!! Nie znaleziono artefaktu: $JAR" >&2
    exit 1
fi

mkdir -p release
cp "$JAR" release/
echo "==> Gotowe: release/SkyRiseBank.jar (wersja pluginu: ${VERSION})"
echo "==> Wrzuć jar do katalogu plugins/ na serwerze Purpur 1.21.10."
