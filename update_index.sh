#!/bin/bash
# Update tag-based release indexes on the 'gh-pages' branch.

set -ev

# Override locally via e.g., 'GH_HOST=git@github.com: ./update_index.sh'
GH_HOST="${GH_HOST:-https://${GH_OAUTH_TOKEN}@github.com/}"

GH_OWNER="zopefoundation"
GH_PROJECT_NAME="Zope"
GH_REPO="${GH_HOST}${GH_OWNER}/${GH_PROJECT_NAME}" 

# Only update index if we are on Travis and have a tag #
if [[ -n "${TRAVIS_TAG}" ]]; then
  echo "Rebuilding release index on tag: ${TRAVIS_TAG}."
else
  echo "No tag, nothing to do."
  exit
fi

# Adding GitHub pages branch. `git submodule add` checks it
# out at HEAD.
GH_PAGES_DIR="ghpages"
git submodule add -q -b gh-pages ${GH_REPO} ${GH_PAGES_DIR}

# Update gh-pages with the generated release docs.
cd ${GH_PAGES_DIR}
./build_index.sh

# Update the files push to gh-pages.
git add -A
git status

if [[ -z "$(git status --porcelain)" ]]; then
    echo "Nothing to commit. Exiting without pushing changes."
    exit
fi

# Commit to gh-pages branch to apply changes.
git config --global user.email "travis@travis-ci.org"
git config --global user.name "travis-ci"
git commit -m "Update release index on tag: ${TRAVIS_TAG}."
git push -q ${GH_REPO} HEAD:gh-pages
