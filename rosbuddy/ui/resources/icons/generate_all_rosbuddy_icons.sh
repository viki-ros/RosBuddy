#!/usr/bin/env bash
# generate_all_rosbuddy_icons.sh
# Generate placeholder SVGs for all required ROSBuddy icons (activity bar, sidebar, toolbar, file types, etc.)
# Usage: ./generate_all_rosbuddy_icons.sh /path/to/icons/dir

set -e

ICON_DIR="${1:-$(dirname "$0")}"  # Default to script's directory if not provided

# Parse icon names from the QRC template
QRC_TEMPLATE="$(dirname "$0")/icons.qrc.template"
ICONS=($(grep -oP '<file>[^<]+' "$QRC_TEMPLATE" | sed 's/<file>//'))

# Qt-compatible placeholder SVG content (UTF-8, valid structure)
placeholder_svg() {
  local name="$1"
  cat <<EOF
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="24" height="24" fill="#b0b0b0"/>
  <g>
    <text x="12" y="16" font-size="7" text-anchor="middle" fill="#23272e" font-family="Arial, sans-serif" alignment-baseline="middle">${name%%.*}</text>
  </g>
</svg>
EOF
}

mkdir -p "$ICON_DIR"

for icon in "${ICONS[@]}"; do
  icon_path="$ICON_DIR/$icon"
  if [[ ! -f "$icon_path" ]]; then
    echo "Creating placeholder: $icon_path"
    placeholder_svg "$icon" > "$icon_path"
  else
    echo "Exists: $icon_path"
  fi
done
