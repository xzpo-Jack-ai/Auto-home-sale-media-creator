#!/bin/bash
# Version bump script for Auto Home Sale Media Creator
# Usage: ./scripts/bump-version.sh [patch|minor|major]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version from package.json
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo -e "${YELLOW}Current version: $CURRENT_VERSION${NC}"

# Determine bump type
BUMP_TYPE=${1:-patch}

if [[ ! "$BUMP_TYPE" =~ ^(patch|minor|major)$ ]]; then
    echo -e "${RED}Error: Invalid bump type. Use 'patch', 'minor', or 'major'${NC}"
    exit 1
fi

# Calculate new version
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case $BUMP_TYPE in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo -e "${GREEN}New version: $NEW_VERSION${NC}"

# Update package.json
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
pkg.version = '$NEW_VERSION';
fs.writeFileSync('./package.json', JSON.stringify(pkg, null, 2) + '\n');
console.log('Updated package.json');
"

# Update apps/web package.json if exists
if [ -f "apps/web/package.json" ]; then
    node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('apps/web/package.json', 'utf8'));
    pkg.version = '$NEW_VERSION';
    fs.writeFileSync('apps/web/package.json', JSON.stringify(pkg, null, 2) + '\n');
    console.log('Updated apps/web/package.json');
    "
fi

# Update apps/api package.json if exists
if [ -f "apps/api/package.json" ]; then
    node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('apps/api/package.json', 'utf8'));
    pkg.version = '$NEW_VERSION';
    fs.writeFileSync('apps/api/package.json', JSON.stringify(pkg, null, 2) + '\n');
    console.log('Updated apps/api/package.json');
    "
fi

# Create version file for runtime access
echo "$NEW_VERSION" > VERSION
echo "Created VERSION file"

# Generate changelog entry
DATE=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [$NEW_VERSION] - $DATE

### Changes
- Version bump to $NEW_VERSION ($BUMP_TYPE)

"

# Prepend to CHANGELOG.md if it exists, otherwise create it
if [ -f "CHANGELOG.md" ]; then
    echo "$CHANGELOG_ENTRY$(cat CHANGELOG.md)" > CHANGELOG.md
else
    echo "# Changelog

$CHANGELOG_ENTRY" > CHANGELOG.md
fi
echo "Updated CHANGELOG.md"

# Git commit
git add package.json apps/*/package.json VERSION CHANGELOG.md 2>/dev/null || true
git add . 2>/dev/null || true
git commit -m "chore(release): bump version to $NEW_VERSION" || echo "Nothing to commit"

echo -e "${GREEN}✅ Version bumped to $NEW_VERSION${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git show HEAD"
echo "  2. Push to remote: git push origin main"
echo "  3. Create a tag: git tag v$NEW_VERSION"
echo "  4. Push tag: git push origin v$NEW_VERSION"
