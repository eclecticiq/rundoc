pipeline {
  agent {
    //predefined docker template on Jenkins Master
    node { label 'python3-node' }
   }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '30', daysToKeepStr: '30'))
   }

stages {

    stage('Build rundoc') {
      steps {
            sh "pip3 install -U ."
          }
        }
    stage('Test rundoc') {
      steps {
            sh " export LC_ALL=C.UTF-8 ; export LANG=C.UTF-8 ; export PATH=$PATH:~/.local/bin; ./tests/all.sh"
          }
        }
  } //stages

  post {
    failure {
      slackSend(
        channel: '#ft-delivery',
        color: 'bad',
        message: "Rundoc failed to build - Logs available at ${BUILD_URL}"
        )
      }
    } //post
} //pipeline
