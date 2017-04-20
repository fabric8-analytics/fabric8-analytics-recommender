#!/usr/bin/env groovy

node('docker') {

    def image = docker.image('bayesian/analytics-training')
    def commitId

    stage('Checkout') {
        checkout scm
        commitId = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
    }

    stage('Build') {
        dockerCleanup()
        docker.build(image.id, '-f Dockerfile.analytics-training --pull --no-cache .')
    }

    if (env.BRANCH_NAME == 'master') {
        stage('Push Images') {
            docker.withRegistry('https://docker-registry.usersys.redhat.com/') {
                image.push('latest')
                image.push(commitId)
            }
            docker.withRegistry('https://registry.devshift.net/') {
                image.push('latest')
                image.push(commitId)
            }
        }
        stage('Prepare Template') {
            dir('openshift') {
                sh "sed -i \"/image-tag\$/ s|latest|${commitId}|\" template.yaml"
                stash name: 'template', includes: 'template.yaml'
                archiveArtifacts artifacts: 'template.yaml'
            }
        }
    }
}

if (env.BRANCH_NAME == 'master') {
    node('oc') {
        stage('Deploy - dev') {
            unstash 'template'
            sh 'oc --context=dev delete job bayesian-analytics-training || :'
            sh 'oc --context=dev process -f template.yaml | oc --context=dev apply -f -'
        }

        stage('Deploy - rh-idev') {
            unstash 'template'
            sh 'oc --context=rh-idev delete job bayesian-analytics-training || :'
            sh 'oc --context=rh-idev process -f template.yaml | oc --context=rh-idev apply -f -'
        }
    }
}
