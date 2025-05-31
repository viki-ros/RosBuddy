#!/usr/bin/env bash
# copy_placeholder_icons.sh
# Copies placeholder SVGs for missing standard icons into the icons directory.
# Usage: ./copy_placeholder_icons.sh /path/to/icons/dir

set -e

ICON_DIR="${1:-$(dirname "$0")}"  # Default to script's directory if not provided

# List of standard icon filenames
ICONS=(
  document-new.svg
  document-open.svg
  application-exit.svg
  package-x-generic.svg
  system-run.svg
  edit-clear.svg
  utilities-terminal.svg
  system-launch.svg
  process-stop.svg
  view-refresh.svg
  edit-find.svg
  folder.svg
  text-x-generic.svg
)

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
