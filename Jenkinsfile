
//define variables
def staged_files
def prod_staged_files

pipeline {
	//run script on different agents
	agent none

	//reusable env variables
	environment {
		VERSION="0.1.${BUILD_NUMBER}"
		BASE_DIRECTORY='Backend/track_locator'
		REMOTE_USER='k8sdeployuser'
		REMOTE_DIR='STAGING_BACKEND_LOCATORAPP'
		REMOTE_FOLDER='Backend/track_locator'
		REMOTE_REPO_NAME='staging_backend_locator'
		DOCKER_ACCOUNT='paulgl721'
		K8S_DEPLOYMENT_FOLDER='z_k8s_deployment'
		K8S_HELM_CHARTS_FOLDER='helm_charts'
		K8S_HELM_CHART_TYPE_FOLDER='staging-locatorapp'
		K8S_RELEASE_NAME='locatorapp-staging'
		K8S_NAMESPACE='locator-app-staging'
		GIT_REPO='git@github.com:Paul-GL721/locator.git'
		GH_TOKENCRED=credentials('jenkins-post-pr-portfolio')
		ANSIBLE_HOST=credentials('locapp-ansible-host')
		ANSIBLE_USER=credentials('locapp-ansible-user')
		ANSIBLE_PRIVATE_KEY_PATH=credentials('locapp-ansible-privatekey')
		K8S_APPSECRET_YAML=credentials('k8s_locatorappsecrets_stage_yaml')
		K8S_DJANGO_APPSECRET_YAML=credentials('k8s_locatorapp-djangosecrets_stage_yaml')
		EMAIL_TO='team@paulgobero.com'
	}

	stages {
		stage('1. Run unit Tests') {
			//Execute tests if its development branch
			when {
				branch 'development'
			}
			//use jenkins testing node
			agent {
				label 'testnode'
			}
			steps {
                echo '..................Testing Code Pushed development................'
			}
		}

		stage('2. Merge development and staging branches') {
			//Execute if its the develpment branch
			when {
				branch 'development'
			}
			//where to execute
			agent {
				label 'buildnode'
			}
			steps {
				echo '..................Merging if anyfiles have changed................'
				
				//with github credentials stored in jenkins server
				sshagent (credentials: ['locator-app-jenkins-to-github']) {
					script {
						//make the merge script executable
						sh 'chmod +x ./${BASE_DIRECTORY}/jenkins-scripts/merge-code-step.sh'

						//Run the merge script to merge dev code into staging
						sh '''./${BASE_DIRECTORY}/jenkins-scripts/merge-code-step.sh '''

						/*//Uncomment if they are changes made and commited to the staging branch directly
						sh('git stash')
						sh('git pull')
						sh('git push ${GIT_REPO}')*/

						//Find the number of staged files 
						staged_files = sh(script: 'git diff --cached --numstat | wc -l', returnStdout: true) as Integer

						//if staged_files are more than zero, commit the files and push to remote repo
						if(staged_files > 0) {
							echo "They are ${staged_files} staged files"
							sh('git commit -m "Merged from development branch: Build version ${VERSION} " ')
							sh('git push ${GIT_REPO}')
						}
						else {
							echo "There no commits to make"
						}
					}
				}
			}
		}

		stage('3. Build and tag staging image') {
			//Execute if its the staging branch
			when {
				branch 'staging'
			}
			//build the docker image and push to aws ecr
			agent {
				//build on build agent
				label 'buildnode'
			}
			steps {
				echo '..............Building and Publishing Staging Docker Images................'
				echo 'Creating a taged image'

				//make the build script executable
				sh 'chmod +x ./${BASE_DIRECTORY}/jenkins-scripts/build-step.sh'

				//build the image
				sh '''./${BASE_DIRECTORY}/jenkins-scripts/build-step.sh '''+VERSION+''' '''
			}
		}

		stage('4. Deploy to the staging kubernetes cluster') {
			//Execute if its the staging branch
			when {
				branch 'staging'
			}
			//Using ansible to deploy on an EC2 instance
			agent {
				label 'deploynode'
			}
			steps {
				echo '..................Deploying with ansible................'
				script{
					//run ansible-playbook
					sh """
						ansible-playbook ./${BASE_DIRECTORY}/ansible/staging-playbook.yml \
						-i ./${BASE_DIRECTORY}/ansible/staging.ini \
						--extra-vars="REMOTE_USER=${env.REMOTE_USER} \
						GIT_REPO=${env.GIT_REPO} \
						VERSION=${env.VERSION} \
						DOCKER_ACCOUNT=${env.DOCKER_ACCOUNT} \
						REMOTE_HOST=${env.REMOTE_HOST} \
						REMOTE_DIR=${env.REMOTE_DIR} \
						REMOTE_FOLDER=${env.REMOTE_FOLDER} \
						REMOTE_REPO_NAME=${env.REMOTE_REPO_NAME} \
						K8S_DEPLOYMENT_FOLDER=${env.K8S_DEPLOYMENT_FOLDER} \
						K8S_HELM_CHARTS_FOLDER=${env.K8S_HELM_CHARTS_FOLDER} \
						K8S_HELM_CHART_TYPE_FOLDER=${env.K8S_HELM_CHART_TYPE_FOLDER} \
						K8S_RELEASE_NAME=${env.K8S_RELEASE_NAME} \
						ANSIBLE_HOST=${env.ANSIBLE_HOST} \
						ANSIBLE_USER=${env.ANSIBLE_USER} \
						ANSIBLE_PRIVATE_KEY_PATH=${env.ANSIBLE_PRIVATE_KEY_PATH} \
						K8S_DJANGO_APPSECRET_YAML=${env.K8S_DJANGO_APPSECRET_YAML} \
						K8S_APPSECRET_YAML=${env.K8S_APPSECRET_YAML} \
						K8S_NAMESPACE=${env.K8S_NAMESPACE}" \
						-vvv
					"""
				}
			}
		}

		stage('5. Create a pull request or Not') {
			//Execute if its the staging branch
			when {
				branch 'staging'
			}
			//Allow the user to either create a "pull request" to production or not
			agent any
			steps {
				echo '..........Would you like to create a Pull Request to Production?........'
				input 'would you like to create a pull request to production?'
				
			}
		}

		stage('6. Merge staging code into production branch') {
			//Execute if its the staging branch
			when {
				branch 'staging'
			}
			agent {
				//build on build agent
				label 'buildnode'
			}
			steps {
				//Use github credentials stored in jenkins server
				sshagent (credentials: ['locator-app-jenkins-to-github']) {
					script {
						echo '..............Creating temporary pull request branch................'
						//make the script executable
						sh 'chmod +x ./${BASE_DIRECTORY}/jenkins-scripts/merge-code-step.sh'

						//build the image
						sh '''./${BASE_DIRECTORY}/jenkins-scripts/merge-code-step.sh '''

						/*//Uncomment if they are changes made and commited to the production branch directly
						sh('git stash')
						sh('git pull')
						sh('git push ${GIT_REPO}')*/

						//Find the number of staged filess
						prod_staged_files = sh(script: 'git diff --cached --numstat | wc -l', returnStdout: true) as Integer

						//if they are (prod_staged_files) more than zero, commit the files and push to remote repo
						if(prod_staged_files > 0) {
							echo "They are ${prod_staged_files} staged files from staging branch"
							sh('git commit -m "Merged from staging branch: Build version ${VERSION} " ')
							sh('git push ${GIT_REPO}')
						}
						else {
							echo "There no commits to make"
						}
					}
				}
			}
		}

		stage('7. Create production temporary branch') {
			//Execute if its the production branch
			when {
				branch 'production'
			}
			agent {
				//build on build agent
				label 'buildnode'
			}
			steps {
				//with github credentials stored in jenkins server
				sshagent (credentials: ['locator-app-jenkins-to-github']) {
					script {
						echo '..............Creating temporary pull request branch................'
						echo 'Creating temp branch'

						//make the pr-branch executable
						sh 'chmod +x ./${BASE_DIRECTORY}/jenkins-scripts/pr-branches.sh'

						//Merge into the temporary branch
						sh '''./${BASE_DIRECTORY}/jenkins-scripts/pr-branches.sh '''+VERSION+''' '''
					}
				}
			}
		}

		stage('8. Create pull request from production to main branch') {
			//Execute if its the production branch
			when {
				branch 'production'
			}
			agent {
				label 'buildnode'
			}
			steps {
				script {
					echo '.............Creating pull request on production branch..........'
					//login, check githubcli pr status, create message and logout
					sh 'gh --version'					
					sh 'echo \$GH_TOKENCRED_PSW|gh auth login --hostname github.com --with-token'
					//sh 'echo $GH_TOKENCRED_PSW | gh auth login --hostname github.com --with-token'
					sh 'gh auth status'					
					echo '.............Creating pull request on main branch..........'
					sh 'gh pr create --title "Production branch v$VERSION was successful" --body "Production branch version$VERSION was successfully tested and deployed; needs to be merged into main" --base main --head tmpproductionV$VERSION'					
					sh 'gh auth logout --hostname github.com'
				}				
			}
		}

		stage('9. Build, tag, and push to remote storage') {
			///Execute if its the production branch
			when {
				branch 'main'
			}
			//build the docker image and push to dockerhub
			agent {
				//build on build agent
				label 'buildnode'
			}
			steps {
				echo '..............Building and Publishing Docker Images................'
				echo 'Creating a production taged image'

				//make the build script executable
				sh 'chmod +x ./${BASE_DIRECTORY}/jenkins-scripts/build-step.sh'

				//build the image
				sh '''./${BASE_DIRECTORY}/jenkins-scripts/build-step.sh '''+VERSION+''' '''
			}
		}

		stage('10. Deploy to production EC2 instance') {
			// Define environment variables
			environment {
				REMOTE_DIR = 'PRODUCTION_BACKEND_LOCATORAPP'
				REMOTE_REPO_NAME = 'locatorapp'
				K8S_HELM_CHART_TYPE_FOLDER = 'locatorapp'
				K8S_RELEASE_NAME = 'locatorapp'
				K8S_NAMESPACE = 'locator-app'
				K8S_APPSECRET_YAML = credentials('k8s_locatorappsecrets_yaml')
				K8S_DJANGO_APPSECRET_YAML==credentials('k8s_locatorapp-djangosecrets_yaml')
			}
			
			// Execute if it's the main branch
			when {
				branch 'main'
			}
			
			// Using Ansible to deploy on an EC2 instance
			agent {
				label 'deploynode'
			}
			
			steps {
				echo '..................Deploying with ansible................'
				script {
					// Run production ansible-playbook
					sh """
						ansible-playbook ./${BASE_DIRECTORY}/ansible/production-playbook.yml \
						-i ./${BASE_DIRECTORY}/ansible/production.ini \
						--extra-vars="REMOTE_USER=${env.REMOTE_USER} \
						GIT_REPO=${env.GIT_REPO} \
						VERSION=${env.VERSION} \
						DOCKER_ACCOUNT=${env.DOCKER_ACCOUNT} \
						REMOTE_HOST=${env.REMOTE_HOST} \
						REMOTE_DIR=${env.REMOTE_DIR} \
						REMOTE_FOLDER=${env.REMOTE_FOLDER} \
						REMOTE_REPO_NAME=${env.REMOTE_REPO_NAME} \
						K8S_DEPLOYMENT_FOLDER=${env.K8S_DEPLOYMENT_FOLDER} \
						K8S_HELM_CHARTS_FOLDER=${env.K8S_HELM_CHARTS_FOLDER} \
						K8S_HELM_CHART_TYPE_FOLDER=${env.K8S_HELM_CHART_TYPE_FOLDER} \
						K8S_RELEASE_NAME=${env.K8S_RELEASE_NAME} \
						ANSIBLE_HOST=${env.ANSIBLE_HOST} \
						ANSIBLE_USER=${env.ANSIBLE_USER} \
						ANSIBLE_PRIVATE_KEY_PATH=${env.ANSIBLE_PRIVATE_KEY_PATH} \
						K8S_DJANGO_APPSECRET_YAML=${env.K8S_DJANGO_APPSECRET_YAML} \
						K8S_APPSECRET_YAML=${env.K8S_APPSECRET_YAML} \
						K8S_NAMESPACE=${env.K8S_NAMESPACE}" \
						-vvv
					"""
				}
			}
		}
        
	}

	post {
		success {
			echo '...........JOB EXECUTED SUCCESSFULLY...........'
			emailext body: 'Your code successfully executed. Check console output at $BUILD_URL to view the results. ',
			subject: 'Stable build in Jenkins: $PROJECT_NAME - #$BUILD_NUMBER', 
            to: "${EMAIL_TO}" 
		}

		failure {
			echo '...........JOB WAS UNSUCCESSFULL................'
			emailext body: 'The commit you made failed. Check console output at $BUILD_URL to view the results. \n\n ${CHANGES} \n\n -------------------------------------------------- \n${BUILD_LOG, maxLines=100, escapeHtml=false}',
			subject: 'Unstable build in Jenkins: $PROJECT_NAME - #$BUILD_NUMBER', 
            to: "${EMAIL_TO}" 
		}
	} 
}