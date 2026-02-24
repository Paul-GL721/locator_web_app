#!/bin/bash
set -e

############## REQUIRED ENV VARS ##############
# SOURCE_BRANCH - branch to merge from (e.g. development) ($1) and is passed first to the script
# TARGET_BRANCH - branch to merge into (e.g. staging or production) ($2) is passed second to the script
SOURCE_BRANCH=$1
TARGET_BRANCH=$2
CREATE_TEMP_BRANCH=${3:-false}
REMOTE="origin"


# check if both source and target branches are provided
if [ -z "$SOURCE_BRANCH" ] || [ -z "$TARGET_BRANCH" ]; then
  echo "Usage: ./merge-branches.sh <source> <target> [create_temp_branch]"
  exit 1
fi
echo "Source branch : $SOURCE_BRANCH"
echo "Target branch : $TARGET_BRANCH"
echo "Create temp   : $CREATE_TEMP_BRANCH"
echo "Remote        : $REMOTE"

############## DEFINE ENV-SPECIFIC EXCLUDES ##############
# Depending on the target branch, we may want to exclude certain files or folders that are only relevant 
# for development or staging and should not be merged into production. 
# We define these excludes in arrays based on the target branch.
EXCLUDE_PATHS=()

if [ "$TARGET_BRANCH" = "staging" ]; then
  EXCLUDE_PATHS=(
    "$BASE_DIRECTORY/devdocker-compose.yml"
    "$BASE_DIRECTORY/dev.Dockerfile"
  )
fi

if [ "$TARGET_BRANCH" = "production" ]; then
  EXCLUDE_PATHS=(
    "$BASE_DIRECTORY/jenkins-scripts/staging-merge-code-step.sh"
    "$BASE_DIRECTORY/stagingdocker-compose.yml"
    "$BASE_DIRECTORY/staging_config.json"
    "$BASE_DIRECTORY/ansible"
  )
fi

########## FETCH & RESET TARGET BRANCH ##########
echo "Fetching latest..."
git fetch $REMOTE

echo "Cleaning workspace..."
git reset --hard
git clean -fd


############## HANDLE TEMP BRANCH CREATION ##############
if [ "$CREATE_TEMP_BRANCH" = "true" ]; then

  if [ -z "$VERSION" ]; then
    echo "ERROR: VERSION environment variable not set"
    exit 1
  fi

  TEMP_BRANCH="tmpproductionV$VERSION"

  echo "Creating temporary branch: $TEMP_BRANCH"
  echo "Based on: $REMOTE/$SOURCE_BRANCH"

  # Create or reset temp branch from source branch
  git checkout -B "$TEMP_BRANCH" "$REMOTE/$SOURCE_BRANCH"

  TARGET_BRANCH="$TEMP_BRANCH"

else
  echo "Checking out existing target branch $TARGET_BRANCH"
  git checkout "$TARGET_BRANCH"
  git reset --hard "$REMOTE/$TARGET_BRANCH"
fi



######### MERGE WITHOUT COMMITTING (Jenkins will commit after tests/build) #########
# Take all commits in SOURCE_BRANCH that are not in TARGET_BRANCH and bring them over, 
# but do not commit yet (Jenkins will commit after running tests and build steps). 
# This allows us to run the full CI pipeline on the merged code before finalizing the merge with a commit.
echo "Merging $SOURCE_BRANCH into $TARGET_BRANCH..."

if ! git merge --no-ff --no-commit $REMOTE/$SOURCE_BRANCH; then
    echo "Merge conflicts detected. Resolving automatically..."

    # Prefer source branch for normal files
    git checkout --theirs .
    git add -A

    # For excluded paths, prefer target branch
    for path in "${EXCLUDE_PATHS[@]}"; do
        if git ls-files --unmerged | grep -q "$path"; then
            echo "Keeping target version of $path"
            git checkout --ours "$path" || true
            git add "$path" || true
        fi
    done
fi


# After removing excluded files, we stage the changes. 
# Jenkins will commit these staged changes after running tests and build steps.
git add -A

echo "--------------------------------------------------"
echo "Merge prepared successfully."
echo "Branch ready for Jenkins commit & push."
echo "--------------------------------------------------"
