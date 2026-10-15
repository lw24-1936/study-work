// Job DSL 示例：用代码批量生成任务，适合「几十个同构任务」的团队。
// 用法：新建一个「Pipeline script」任务，脚本内容 buildJobDsl()，它会执行这里定义的 DSL。
// 或在 seed job 里直接用 jobDsl 步骤：jobDsl targets: 'jenkins/jobs/**/*.groovy'

// 1) 单分支流水线任务：把 Jenkinsfile 放在仓库里，任务只描述「在哪拉、拉哪个分支」
pipelineJob('demo-pipeline-jdsl') {
    description('由 Job DSL 生成，配置进 Git，改配置走代码评审')
    parameters {
        choiceParam('ENVIRONMENT', ['dev', 'staging', 'prod'], '部署环境')
        stringParam('BRANCH', 'main', '构建分支')
    }
    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('file:///demo/repo.git')
                    }
                    branch('*/main')
                }
            }
            scriptPath('Jenkinsfile')
            lightweight(true)
        }
    }
    logRotator {
        numToKeep(30)
        artifactNumToKeep(10)
    }
}

// 2) 多分支流水线：按仓库里的分支/PR 自动建任务，配合 Jenkinsfile 就是「一个 Jenkinsfile 管所有分支」
multibranchPipelineJob('demo-multibranch') {
    branchSources {
        git {
            id('demo-repo')
            remote('file:///demo/repo.git')
        }
    }
    orphanedItemStrategy {
        discardOldItems {
            numToKeep(5)
        }
    }
}

// 3) 定时任务（cron 语法与 Linux crontab 略有差异：五段，H 表示散列）
freeStyleJob('demo-nightly') {
    triggers {
        // 每天 02:30，H 让 Jenkins 自己挑一个时间点，避免全公司同一秒开跑
        cron('H 2 * * *')
    }
    steps {
        shell('echo "nightly build at $(date)"')
    }
    publishers {
        // 保留最近 7 天的构建
        buildDiscarder {
            strategy {
                logRotator {
                    daysToKeepStr('7')
                    numToKeepStr('50')
                }
            }
        }
    }
}
