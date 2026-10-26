#!/usr/bin/env bash
# Official 8.24.2 release archives; checksums verified against upstream release.
set -euo pipefail
case "$(uname -s)/$(uname -m)" in
  Linux/x86_64) platform=linux_x64; checksum=fa0500f6b7e41d28791ebc680f5dd9899cd42b58629218a5f041efa899151a8e ;;
  Linux/aarch64|Linux/arm64) platform=linux_arm64; checksum=574a6d52573c61173add7ddb5e3cc68c0e82cb0735818a1eeb9a0a2de1643fbc ;;
  Darwin/arm64) platform=darwin_arm64; checksum=90d13686937ac7429b97a3acbf1e1d0ce90d92ae2d0cf46a690bd8ae5230bea0 ;;
  Darwin/x86_64) platform=darwin_x64; checksum=bc3c46f8039ba716ba8461fa6745c9d1cfb90ca2f5f881d8d0cf66b7ba7b742c ;;
  *) echo 'Unsupported Gitleaks platform.' >&2; exit 1 ;;
esac
target="${SDI_TOOLS_DIR:-$HOME/.local/share/sdi/tools}/gitleaks-8.24.2-$platform"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl --fail --silent --show-error --location --max-time 120 \
  "https://github.com/gitleaks/gitleaks/releases/download/v8.24.2/gitleaks_8.24.2_$platform.tar.gz" -o "$tmp/archive.tar.gz"
if command -v sha256sum >/dev/null; then
  printf '%s  %s\n' "$checksum" "$tmp/archive.tar.gz" | sha256sum --check --status
else
  [[ "$(shasum -a 256 "$tmp/archive.tar.gz" | cut -d ' ' -f 1)" == "$checksum" ]]
fi
tar -xzf "$tmp/archive.tar.gz" -C "$tmp" gitleaks
mkdir -p "$(dirname "$target")"
install -m 755 "$tmp/gitleaks" "$target"
printf '%s\n' "$target"
