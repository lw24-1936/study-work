// 共享库（Shared Library）示例
//
// 目录结构（仓库根就是共享库根）：
//   vars/buildPython.groovy        <- 全局变量，Jenkinsfile 里直接 buildPython(...)
//   src/org/example/Utils.groovy   <- 普通 Groovy 类，可写单元测试（src/test/groovy）
//   resources/                     <- 非 Groovy 资源，libraryResource 读取
//
// 在「Manage Jenkins > System > Global Pipeline Libraries」里注册：
//   Name: my-shared-lib
//   Default version: main
//   Retrieval method: Modern SCM -> Git -> 仓库地址
//
// Jenkinsfile 里的用法见同目录 Jenkinsfile.sharedlib

def call(Map config = [:]) {
    def python = config.python ?: 'python3'
    def venv = config.venv ?: '.venv'
    def env = config.env ?: 'dev'

    pipeline {
        agent any
        stages {
            stage("构建（${env}）") {
                steps {
                    sh """
                        set -eux
                        ${python} -m venv ${venv}
                        ${venv}/bin/pip install -q -r requirements.txt
                    """
                }
            }
            stage('测试') {
                steps {
                    sh "${venv}/bin/python -m pytest -q --junitxml=reports/unit.xml"
                }
                post {
                    always {
                        junit 'reports/unit.xml'
                    }
                }
            }
        }
    }
}
