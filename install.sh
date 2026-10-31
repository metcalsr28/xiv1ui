#!/bin/bash
# xiv1ui installer for an Ashita v4 install inside Wine / CrossOver (macOS or Linux).
#
#   ./install.sh "<path to the Ashita folder>"        e.g. .../drive_c/CatsEyeXI/catseyexi-client/Ashita
#
# The Ashita folder is the one holding Ashita-cli.exe, addons/ and scripts/. The installer:
#   1. copies addons/xiv1ui into <Ashita>/addons/xiv1ui (replacing an older copy of it),
#   2. writes <Ashita>/scripts/xiv1ui.txt (loads the Nameplate plugin and xiv1ui),
#   3. adds "/include xiv1ui.txt" to <Ashita>/scripts/default.txt (once; backup default.txt.before-xiv1ui).
# Run it again to update. ./install.sh --uninstall "<Ashita>" removes all three.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
MODE=install
if [ "${1:-}" = "--uninstall" ]; then MODE=uninstall; shift; fi
ASHITA="${1:-}"
if [ -z "$ASHITA" ] || [ ! -f "$ASHITA/Ashita-cli.exe" ] || [ ! -d "$ASHITA/addons" ] || [ ! -d "$ASHITA/scripts" ]; then
    echo "usage: $0 [--uninstall] <Ashita folder>  (the folder with Ashita-cli.exe, addons/ and scripts/)" >&2
    exit 1
fi
DEFAULT="$ASHITA/scripts/default.txt"
SCRIPT="$ASHITA/scripts/xiv1ui.txt"
TARGET="$ASHITA/addons/xiv1ui"

if [ "$MODE" = uninstall ]; then
    rm -rf "$TARGET" "$SCRIPT"
    if [ -f "$DEFAULT" ]; then
        tmp="$(mktemp)"
        grep -v -i '^/include xiv1ui\.txt' "$DEFAULT" > "$tmp" || true
        cat "$tmp" > "$DEFAULT"; rm -f "$tmp"
    fi
    echo "xiv1ui removed. Restart the game (or /addon unload xiv1ui) to see FFXI's own interface again."
    exit 0
fi

if [ -L "$TARGET" ]; then
    echo "$TARGET is a symlink (a development install); not replacing it." >&2
    exit 1
fi

# 1. the addon
rm -rf "$TARGET.new"
cp -R "$HERE/addons/xiv1ui" "$TARGET.new"
rm -rf "$TARGET"
mv "$TARGET.new" "$TARGET"

# 2. the load script (CRLF, like Ashita's own scripts)
printf '%s\r\n' \
    '##########################################################################' \
    '# xiv1ui (FINAL FANTASY XIV 1.0 style interface). Included from default.txt.' \
    '##########################################################################' \
    '/load nameplate' \
    '/addon load xiv1ui' > "$SCRIPT"

# 3. include it from default.txt (once)
if [ ! -f "$DEFAULT" ]; then
    echo "warning: $DEFAULT not found; load xiv1ui by hand with /addon load xiv1ui" >&2
elif ! grep -qi '^/include xiv1ui\.txt' "$DEFAULT"; then
    [ -f "$DEFAULT.before-xiv1ui" ] || cp "$DEFAULT" "$DEFAULT.before-xiv1ui"
    # make sure the last line ends before appending
    if [ -s "$DEFAULT" ] && [ "$(tail -c 1 "$DEFAULT" | od -An -c | tr -d ' ')" != '\n' ]; then
        printf '\r\n' >> "$DEFAULT"
    fi
    printf '/include xiv1ui.txt\r\n' >> "$DEFAULT"
fi

echo "xiv1ui installed in $TARGET."
echo "Start (or restart) the game; xiv1ui loads by itself. In game: /addon reload xiv1ui after an update."
