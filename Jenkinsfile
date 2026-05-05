pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'siddheshinde1/devops-dashboard'
        DOCKER_TAG   = "${BUILD_NUMBER}"
        K8S_DEPLOY   = 'devops-dashboard'
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                echo "Verifying dependencies inside Docker..."
                sh '''
                    docker run --rm \
                        -v "$(pwd)/requirements.txt:/requirements.txt" \
                        python:3.11-slim \
                        pip install --quiet -r /requirements.txt
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh """
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    echo "Build complete: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                """
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo "Pushing image to Docker Hub..."
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                        docker logout
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo "Deploying to Kubernetes cluster..."
                sh """
                    kubectl apply -f k8s/rbac.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl set image deployment/${K8S_DEPLOY} dashboard=${DOCKER_IMAGE}:${DOCKER_TAG} --record || true
                    kubectl rollout status deployment/${K8S_DEPLOY} --timeout=60s
                """
            }
        }

        stage('Verify Deployment') {
            steps {
                echo "Verifying deployment..."
                sh """
                    kubectl get pods -l app=devops-dashboard
                    kubectl get svc devops-dashboard-service
                """
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS — Build #${BUILD_NUMBER} deployed."
        }
        failure {
            echo "Pipeline FAILED — Check logs above."
        }
        always {
            sh 'docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true'
        }
    }
}
