pipeline {
    agent any

    stages {

        // Stage 1 - Se ejecuta primero, de forma secuencial
        stage('Merge en local') {
            steps {
                echo 'Haciendo merge de WorkingBranch sobre Develop...'
                // En un caso real: git merge origin/WorkingBranch
            }
        }

        // Stages 2 y 3 - Se ejecutan en paralelo
        stage('Compilacion y Tests') {
            parallel {

                stage('Compilacion') {
                    steps {
                        echo 'Compilando codigo de produccion...'
                        // En un caso real: sh 'pip install -r requirements.txt'
                    }
                }

                stage('Tests Unitarios') {
                    steps {
                        echo 'Ejecutando tests unitarios...'
                        // En un caso real: sh 'pytest tests/'
                    }
                }

            }
        }

    }
}