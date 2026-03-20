#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# Titan-X — .deb Package Builder (Full Pre-Configured Installer)
#
# Assembles the titan-x Debian package. Default mode bundles everything
# including pre-built Cuttlefish images (~3-4 GB package).
#
# Usage:
#   ./build-deb.sh                  # Full pre-configured (~3-4 GB)
#   ./build-deb.sh --code-only      # Code only, no images (~1 MB)
#   ./build-deb.sh --skip-image-build  # Bundle existing images, don't rebuild
#
# Output: dist/titan-x_<version>_amd64.deb
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}"
VERSION="12.0.0"
PACKAGE="titan-x"
ARCH="amd64"
INSTALL_PREFIX="/opt/titan"

STAGING="${SRC_DIR}/dist/.staging"
DEB_OUT="${SRC_DIR}/dist/${PACKAGE}_${VERSION}_${ARCH}.deb"

CODE_ONLY=0
SKIP_IMAGE_BUILD=0

for arg in "$@"; do
    case "$arg" in
        --code-only)         CODE_ONLY=1 ;;
        --skip-image-build)  SKIP_IMAGE_BUILD=1 ;;
        --help|-h)
            echo "Usage: $0 [--code-only] [--skip-image-build]"
            echo "  --code-only          Build code-only package (~1 MB, no images)"
            echo "  --skip-image-build   Bundle existing images without rebuilding"
            exit 0
            ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

echo "═══════════════════════════════════════════════════════════"
echo "  Building ${PACKAGE} v${VERSION} (${ARCH})"
echo "  Mode: $(if [[ $CODE_ONLY -eq 1 ]]; then echo 'CODE-ONLY'; else echo 'FULL PRE-CONFIGURED'; fi)"
echo "═══════════════════════════════════════════════════════════"

# ─── Clean staging ────────────────────────────────────────────────────
rm -rf "${STAGING}"
mkdir -p "${STAGING}/DEBIAN"
mkdir -p "${STAGING}${INSTALL_PREFIX}"

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Build Android images (unless --code-only or --skip-image-build)
# ═══════════════════════════════════════════════════════════════════════
IMAGE_TARBALL="/opt/titan/images/titan-android14-cf-x86_64.tar.gz"

if [[ $CODE_ONLY -eq 0 ]]; then
    if [[ $SKIP_IMAGE_BUILD -eq 0 ]]; then
        echo ""
        echo "[0/8] Building Android 14 images (GApps + Magisk + Zygisk)..."
        echo "  This downloads ~3 GB and takes 10-30 minutes."
        echo ""
        if [[ -f "${SRC_DIR}/build/build-image.sh" ]]; then
            bash "${SRC_DIR}/build/build-image.sh" || {
                echo ""
                echo "ERROR: Image build failed."
                echo "  Fix errors above, or build with --code-only for code-only package."
                echo "  You can also build images separately and use --skip-image-build."
                exit 1
            }
        else
            echo "ERROR: build/build-image.sh not found"
            exit 1
        fi
    else
        echo "[0/8] Skipping image build (--skip-image-build)"
        if [[ ! -f "$IMAGE_TARBALL" ]]; then
            echo "  WARNING: No image tarball found at $IMAGE_TARBALL"
            echo "  Run build/build-image.sh first, or pass --code-only"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════
# STEP 2: DEBIAN control files
# ═══════════════════════════════════════════════════════════════════════
echo "[1/8] Writing DEBIAN control files..."

cp "${SRC_DIR}/debian/control"   "${STAGING}/DEBIAN/control"
cp "${SRC_DIR}/debian/preinst"   "${STAGING}/DEBIAN/preinst"
cp "${SRC_DIR}/debian/postinst"  "${STAGING}/DEBIAN/postinst"
cp "${SRC_DIR}/debian/prerm"     "${STAGING}/DEBIAN/prerm"
cp "${SRC_DIR}/debian/postrm"    "${STAGING}/DEBIAN/postrm"
cp "${SRC_DIR}/debian/conffiles" "${STAGING}/DEBIAN/conffiles"

chmod 755 "${STAGING}/DEBIAN/preinst"
chmod 755 "${STAGING}/DEBIAN/postinst"
chmod 755 "${STAGING}/DEBIAN/prerm"
chmod 755 "${STAGING}/DEBIAN/postrm"
chmod 644 "${STAGING}/DEBIAN/control"
chmod 644 "${STAGING}/DEBIAN/conffiles"

# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Core application files → /opt/titan/
# ═══════════════════════════════════════════════════════════════════════
echo "[2/8] Copying core application..."

# Python core modules
rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='_deprecated' \
    "${SRC_DIR}/core/" "${STAGING}${INSTALL_PREFIX}/core/"

# FastAPI server
rsync -a --exclude='__pycache__' --exclude='*.pyc' \
    "${SRC_DIR}/server/" "${STAGING}${INSTALL_PREFIX}/server/"

# Web console
rsync -a --exclude='*.bak' --exclude='*.bak2' \
    "${SRC_DIR}/console/" "${STAGING}${INSTALL_PREFIX}/console/"

# Build scripts (Magisk, Zygisk modules, image builder)
rsync -a "${SRC_DIR}/build/" "${STAGING}${INSTALL_PREFIX}/build/"
chmod +x "${STAGING}${INSTALL_PREFIX}/build/"*.sh 2>/dev/null || true

# Cuttlefish config templates
rsync -a "${SRC_DIR}/cuttlefish/" "${STAGING}${INSTALL_PREFIX}/cuttlefish/"

# Project metadata
for f in pyproject.toml requirements.txt README.md CHANGELOG.md; do
    [[ -f "${SRC_DIR}/${f}" ]] && cp "${SRC_DIR}/${f}" "${STAGING}${INSTALL_PREFIX}/"
done

# .env.example (template — postinst seeds .env from this)
[[ -f "${SRC_DIR}/.env.example" ]] && cp "${SRC_DIR}/.env.example" "${STAGING}${INSTALL_PREFIX}/"

# Server requirements.txt (for pip install in postinst)
if [[ -f "${SRC_DIR}/server/requirements.txt" ]]; then
    cp "${SRC_DIR}/server/requirements.txt" "${STAGING}${INSTALL_PREFIX}/requirements.txt"
fi

# ═══════════════════════════════════════════════════════════════════════
# STEP 4: Scripts, Docker, Desktop
# ═══════════════════════════════════════════════════════════════════════
echo "[3/8] Copying scripts, Docker, and desktop configs..."

# Deployment/setup scripts
mkdir -p "${STAGING}${INSTALL_PREFIX}/scripts"
rsync -a --exclude='__pycache__' --exclude='*.pyc' \
    "${SRC_DIR}/scripts/" "${STAGING}${INSTALL_PREFIX}/scripts/"
chmod +x "${STAGING}${INSTALL_PREFIX}/scripts/"*.sh 2>/dev/null || true

# Docker configs (nginx, compose files)
mkdir -p "${STAGING}${INSTALL_PREFIX}/docker"
for f in nginx.conf docker-compose.yml docker-compose.prod.yml; do
    [[ -f "${SRC_DIR}/docker/${f}" ]] && cp "${SRC_DIR}/docker/${f}" "${STAGING}${INSTALL_PREFIX}/docker/"
done
mkdir -p "${STAGING}${INSTALL_PREFIX}/docker/ssl"

# GApps overlay configs
if [[ -d "${SRC_DIR}/docker/gapps" ]]; then
    rsync -a "${SRC_DIR}/docker/gapps/" "${STAGING}${INSTALL_PREFIX}/docker/gapps/"
fi
if [[ -d "${SRC_DIR}/docker/init.d" ]]; then
    rsync -a "${SRC_DIR}/docker/init.d/" "${STAGING}${INSTALL_PREFIX}/docker/init.d/"
fi

# Desktop (Electron — optional)
if [[ -d "${SRC_DIR}/desktop" ]]; then
    mkdir -p "${STAGING}${INSTALL_PREFIX}/desktop"
    for f in main.js preload.js package.json start.sh setup.html titan-console.desktop; do
        [[ -f "${SRC_DIR}/desktop/${f}" ]] && cp "${SRC_DIR}/desktop/${f}" "${STAGING}${INSTALL_PREFIX}/desktop/"
    done
    [[ -d "${SRC_DIR}/desktop/assets" ]] && \
        rsync -a "${SRC_DIR}/desktop/assets/" "${STAGING}${INSTALL_PREFIX}/desktop/assets/"
fi

# ═══════════════════════════════════════════════════════════════════════
# STEP 5: CLI tools → /usr/bin/
# ═══════════════════════════════════════════════════════════════════════
echo "[4/8] Installing CLI tools..."

mkdir -p "${STAGING}/usr/bin"
cp "${SRC_DIR}/bin/titan-x" "${STAGING}/usr/bin/titan-x"
chmod 755 "${STAGING}/usr/bin/titan-x"

mkdir -p "${STAGING}${INSTALL_PREFIX}/bin"
for cli_tool in titan-keybox titan-console; do
    if [[ -f "${SRC_DIR}/bin/${cli_tool}" ]]; then
        cp "${SRC_DIR}/bin/${cli_tool}" "${STAGING}${INSTALL_PREFIX}/bin/${cli_tool}"
        chmod 755 "${STAGING}${INSTALL_PREFIX}/bin/${cli_tool}"
        ln -sf "${INSTALL_PREFIX}/bin/${cli_tool}" "${STAGING}/usr/bin/${cli_tool}"
    fi
done

# ═══════════════════════════════════════════════════════════════════════
# STEP 6: System configs (systemd, kernel modules)
# ═══════════════════════════════════════════════════════════════════════
echo "[5/8] Installing systemd services and kernel configs..."

mkdir -p "${STAGING}/etc/systemd/system"
for unit in titan-api.service titan-scrcpy.service titan-nginx.service; do
    cp "${SRC_DIR}/debian/${unit}" "${STAGING}/etc/systemd/system/${unit}"
    chmod 644 "${STAGING}/etc/systemd/system/${unit}"
done

mkdir -p "${STAGING}/etc/modules-load.d"
mkdir -p "${STAGING}/etc/modprobe.d"
cp "${SRC_DIR}/debian/titan-x.modules-load.conf" "${STAGING}/etc/modules-load.d/titan-x.conf"
cp "${SRC_DIR}/debian/titan-x.modprobe.conf"     "${STAGING}/etc/modprobe.d/titan-x.conf"
chmod 644 "${STAGING}/etc/modules-load.d/titan-x.conf"
chmod 644 "${STAGING}/etc/modprobe.d/titan-x.conf"

# ═══════════════════════════════════════════════════════════════════════
# STEP 7: Bundle pre-built images (full mode)
# ═══════════════════════════════════════════════════════════════════════
if [[ $CODE_ONLY -eq 0 ]]; then
    echo "[6/8] Bundling pre-built Cuttlefish images + modules..."

    mkdir -p "${STAGING}${INSTALL_PREFIX}/images"

    if [[ -f "$IMAGE_TARBALL" ]]; then
        cp "$IMAGE_TARBALL" "${STAGING}${INSTALL_PREFIX}/images/"
        IMGSIZE=$(du -sh "$IMAGE_TARBALL" | awk '{print $1}')
        echo "  Bundled image archive: ${IMGSIZE}"
    else
        echo "  WARNING: Image tarball not found at $IMAGE_TARBALL"
        echo "  Building code-only package (images download at runtime)"
    fi

    # Also bundle pre-downloaded GApps APKs if available
    GAPPS_SRC="${TITAN_DATA:-/opt/titan/data}/gapps"
    if [[ -d "$GAPPS_SRC" ]] && [[ -n "$(ls -A "$GAPPS_SRC"/*.apk 2>/dev/null)" ]]; then
        mkdir -p "${STAGING}${INSTALL_PREFIX}/gapps"
        cp "$GAPPS_SRC"/*.apk "${STAGING}${INSTALL_PREFIX}/gapps/" 2>/dev/null || true
        echo "  Bundled $(ls "${STAGING}${INSTALL_PREFIX}/gapps/"*.apk 2>/dev/null | wc -l) GApps APKs"
    fi

    # Bundle keybox if present (NEVER in public builds)
    KEYBOX_SRC="${TITAN_DATA:-/opt/titan/data}/keybox/keybox.xml"
    if [[ -f "$KEYBOX_SRC" ]]; then
        mkdir -p "${STAGING}${INSTALL_PREFIX}/data/keybox"
        cp "$KEYBOX_SRC" "${STAGING}${INSTALL_PREFIX}/data/keybox/"
        echo "  Bundled keybox.xml (PRIVATE BUILD ONLY)"
    fi
else
    echo "[6/8] Skipping images (--code-only mode)"
fi

# ═══════════════════════════════════════════════════════════════════════
# STEP 8: Finalize and build .deb
# ═══════════════════════════════════════════════════════════════════════
echo "[7/8] Finalizing package..."

# Compute actual installed size (in KB)
INSTALLED_SIZE=$(du -sk "${STAGING}" | awk '{print $1}')
sed -i "s/^Installed-Size:.*/Installed-Size: ${INSTALLED_SIZE}/" "${STAGING}/DEBIAN/control"
# Update version in control file
sed -i "s/^Version:.*/Version: ${VERSION}/" "${STAGING}/DEBIAN/control"

# Strip __pycache__ that may have snuck in
find "${STAGING}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${STAGING}" -name '*.pyc' -delete 2>/dev/null || true

# Fix permissions
find "${STAGING}" -type d -exec chmod 755 {} +
find "${STAGING}" -type f -exec chmod 644 {} +
# Re-set executables
chmod 755 "${STAGING}/DEBIAN/preinst" "${STAGING}/DEBIAN/postinst"
chmod 755 "${STAGING}/DEBIAN/prerm" "${STAGING}/DEBIAN/postrm"
chmod 755 "${STAGING}/usr/bin/titan-x"
find "${STAGING}${INSTALL_PREFIX}/bin" -type f -exec chmod 755 {} + 2>/dev/null || true
find "${STAGING}${INSTALL_PREFIX}/build" -name '*.sh' -exec chmod 755 {} + 2>/dev/null || true
find "${STAGING}${INSTALL_PREFIX}/scripts" -name '*.sh' -exec chmod 755 {} + 2>/dev/null || true

echo "[8/8] Building .deb package..."
mkdir -p "${SRC_DIR}/dist"
dpkg-deb --build --root-owner-group "${STAGING}" "${DEB_OUT}"

rm -rf "${STAGING}"

# ═══════════════════════════════════════════════════════════════════════
SIZE_MB=$(du -sm "${DEB_OUT}" | awk '{print $1}')
SIZE_HUMAN=$(du -sh "${DEB_OUT}" | awk '{print $1}')
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  BUILD COMPLETE"
echo ""
echo "  Package:  ${DEB_OUT}"
echo "  Size:     ${SIZE_HUMAN} (${SIZE_MB} MB)"
echo "  Version:  ${VERSION}"
echo "  Mode:     $(if [[ $CODE_ONLY -eq 1 ]]; then echo 'CODE-ONLY'; else echo 'FULL PRE-CONFIGURED'; fi)"
echo ""
echo "  Install:  sudo dpkg -i ${DEB_OUT}"
echo "  Fix deps: sudo apt-get install -f"
echo ""
if [[ $CODE_ONLY -eq 0 ]] && [[ $SIZE_MB -gt 100 ]]; then
    echo "  ✓ Images bundled — device boots immediately after install"
else
    echo "  ⚠ Code-only — run 'titan-x setup-cuttlefish' after install"
fi
echo "═══════════════════════════════════════════════════════════"
