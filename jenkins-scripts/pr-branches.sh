#!/bin/bash

###Script to merge devlopment branch code into the staging branch###

#set git username and email
git config --global user.name "server2"
git config --global user.email lwangapaul23@gmail.com
echo The branches are:
git branch
git checkout -b tmpproductionV$VERSION

#If any of these files or folder changes in the production branch
#merge them into the main branch

# Define the list of Django apps
APPS=("locator")

# Define the files to include for each app
FILES=("admin.py" "apps.py" "forms.py" "models.py" "tests.py" "urls.py" "views.py" "serializers.py")
FOLDERS=("static" "templates")

# Checkout selected files in a loop
for app in "${APPS[@]}"; do
    for file in "${FILES[@]}"; do
        if [ -f "$BASE_DIRECTORY/$app/$file" ]; then
            echo "Checking out: $BASE_DIRECTORY/$app/$file"
            git checkout origin/production "$BASE_DIRECTORY/$app/$file"
        else
            echo "Skipping: $BASE_DIRECTORY/$app/$file (file does not exist)"
        fi
    done
done
# Checkout selected folders using a loop a loop
for app in "${APPS[@]}"; do
    for folder in "${FOLDERS[@]}"; do
        full_path="$BASE_DIRECTORY/$app/$folder"
        echo "Checking out: $full_path"
        git checkout origin/staging -- "$full_path" || echo "Warning: $full_path not found in origin/staging"
    done
done


# Checkout additional necessary files
git checkout origin/production $BASE_DIRECTORY/track_locator $BASE_DIRECTORY/.gitignore \
    $BASE_DIRECTORY/Dockerfile $BASE_DIRECTORY/entrypoint.sh $BASE_DIRECTORY/docker-compose.yml \ 
    $BASE_DIRECTORY/manage.py $BASE_DIRECTORY/Pipfile $BASE_DIRECTORY/Pipfile.lock \
    $BASE_DIRECTORY/README.md $BASE_DIRECTORY/templates $BASE_DIRECTORY/static \ 
    $BASE_DIRECTORY/z_k8s_deployment $BASE_DIRECTORY/jenkins-scripts/build-step.sh \
    $BASE_DIRECTORY/ansible $BASE_DIRECTORY/Jenkinsfile 

git push --set-upstream origin tmpproductionV$VERSION

git status
#git remote -v