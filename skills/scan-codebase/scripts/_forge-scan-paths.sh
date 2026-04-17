# shellcheck shell=bash
# Forge scan-codebase: per-run artifact directory for phase1/3.5/4/5/5.6 temp files.
#
# Set FORGE_SCAN_RUN_DIR before sourcing (e.g. tools/forge_scan_run.py creates a
# dedicated directory and exports it). Default remains /tmp for ad-hoc script use.
#
# FORGE_SCAN_TMP is the directory where forge_scan_*.txt files are written; it
# defaults to FORGE_SCAN_RUN_DIR. Override only if you need a different layout.

: "${FORGE_SCAN_RUN_DIR:=/tmp}"
export FORGE_SCAN_RUN_DIR

: "${FORGE_SCAN_TMP:=$FORGE_SCAN_RUN_DIR}"
export FORGE_SCAN_TMP

mkdir -p "${FORGE_SCAN_TMP}"
