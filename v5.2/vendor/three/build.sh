#!/bin/sh
# Reconstruit vendor/three/three.min.js : sous-ensemble de three.js limité aux
# classes réellement utilisées par main.js, exposé en global THREE (comme
# l'ancien three.min.js de cdnjs). À relancer après tout ajout de THREE.Xxx.
set -e
cd "$(dirname "$0")"
VERSION=0.186.1
TMP=$(mktemp -d)
NAMES=$(grep -oE "THREE\.[A-Za-z0-9_]+" ../../main.js | sort -u | sed 's/THREE\.//' | paste -sd, -)
echo "export { $NAMES } from 'three';" > "$TMP/entry.js"
(cd "$TMP" && npm i --silent --no-audit --no-fund three@$VERSION esbuild)
"$TMP/node_modules/.bin/esbuild" "$TMP/entry.js" --bundle --minify --format=iife \
  --global-name=THREE --target=es2020 --legal-comments=inline --outfile=three.min.js
rm -rf "$TMP"
