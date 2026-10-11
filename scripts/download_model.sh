#!/usr/bin/env bash
# Download the Vosk small Hindi model (Apache-2.0, ~42 MB) into ./model.
set -euo pipefail

MODEL_NAME="vosk-model-small-hi-0.22"
MODEL_URL="https://alphacephei.com/vosk/models/${MODEL_NAME}.zip"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-${ROOT}/model}"

if [ -f "${TARGET}/am/final.mdl" ] && [ -f "${TARGET}/graph/HCLr.fst" ]; then
  echo "Model already present at ${TARGET}"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

echo "Downloading ${MODEL_URL}"
if command -v wget >/dev/null 2>&1; then
  wget -q --show-progress -O "${TMP}/model.zip" "${MODEL_URL}"
else
  curl -fL -o "${TMP}/model.zip" "${MODEL_URL}"
fi
unzip -q "${TMP}/model.zip" -d "${TMP}"

rm -rf "${TARGET}"
mv "${TMP}/${MODEL_NAME}" "${TARGET}"
echo "Model installed at ${TARGET}"
