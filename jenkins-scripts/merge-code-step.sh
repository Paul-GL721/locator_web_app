#!/bin/bash

###Script to merge devlopment branch code into the staging branch###

#set git username and email
git config --global user.name "server2"
git config --global user.email lwangapaul23@gmail.com
echo The branches are:
git branch
git checkout -f staging

#If any of these files or folder changes in the development branch
#merge them into the staging branch

# Define the list of Django apps
APPS=("locator")

# Define the files to include for each app
FILES=("admin.py" "apps.py" "forms.py" "models.py" "tests.py" "urls.py" "views.py")

# Checkout selected files in a loop
for app in "${APPS[@]}"; do
    for file in "${FILES[@]}"; do
        if [ -f "$BASE_DIRECTORY/$app/$file" ]; then
            echo "Checking out: $BASE_DIRECTORY/$app/$file"
            git checkout origin/development "$BASE_DIRECTORY/$app/$file"
        else
            echo "Skipping: $BASE_DIRECTORY/$app/$file (file does not exist)"
        fi
    done
done


# Checkout additional necessary files
git checkout origin/development $BASE_DIRECTORY/track_locator $BASE_DIRECTORY/.gitignore $BASE_DIRECTORY/Jenkinsfile $BASE_DIRECTORY/manage.py $BASE_DIRECTORY/Pipfile $BASE_DIRECTORY/Pipfile.lock $BASE_DIRECTORY/README.md $BASE_DIRECTORY/templates $BASE_DIRECTORY/static

git status
#git remote -v 
