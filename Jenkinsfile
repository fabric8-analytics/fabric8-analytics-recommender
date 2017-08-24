#!/usr/bin/env groovy
@Library('github.com/msrb/cicd-pipeline-helpers')

def commitId
node('docker') {

    def image = docker.image('bayesian/analytics-training')

    stage('Checkout') {
        checkout scm
        commitId = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        dir('openshift') {
            stash name: 'template', includes: 'template.yaml'
        }
    }

    stage('Build') {
        dockerCleanup()
        docker.build(image.id, '-f Dockerfile.analytics-training --pull --no-cache .')
    }

    if (env.BRANCH_NAME == 'master') {
        stage('Push Images') {
            docker.withRegistry('https://push.registry.devshift.net/', 'devshift-registry') {
                image.push('latest')
                image.push(commitId)
            }
        }
    }
}

if (env.BRANCH_NAME == 'master') {
    node('oc') {
        stage('Deploy - dev') {
            unstash 'template'
            sh 'oc --context=dev delete job bayesian-analytics-training || :'
            sh "oc --context=dev process -v IMAGE_TAG=${commitId} -f template.yaml | oc --context=dev apply -f -"
        }

        //stage('Deploy - rh-idev') {
        //    unstash 'template'
        //    sh 'oc --context=rh-idev delete job bayesian-analytics-training || :'
        //    sh "oc --context=rh-idev process -v IMAGE_TAG=${commitId} -f template.yaml | oc --context=rh-idev apply -f -"
        //}
    }
}
