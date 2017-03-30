#!/usr/bin/env groovy

node('docker') {

    def image = docker.image('bayesian/analytics-training')

    stage('Checkout') {
        checkout scm
    }

    stage('Build') {
        dockerCleanup()
        docker.build(image.id, '-f Dockerfile.analytics-training --pull --no-cache .')
    }

    if (env.BRANCH_NAME == 'master') {
        stage('Push Images') {
            def commitId = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            docker.withRegistry('https://docker-registry.usersys.redhat.com/') {
                image.push('latest')
                image.push(commitId)
            }
            docker.withRegistry('https://registry.devshift.net/') {
                image.push('latest')
                image.push(commitId)
            }
        }
    }
}

if (env.BRANCH_NAME == 'master') {
    node('oc') {
        stage('Deploy - dev') {
            rerunOpenShiftJob {
                jobName = 'bayesian-analytics-training'
                cluster = 'dev'
			}
        }

        stage('Deploy - rh-idev') {
            rerunOpenShiftJob {
                jobName = 'bayesian-analytics-training'
                cluster = 'rh-idev'
            }
        }
    }
}
