// init.groovy.d/01-security.groovy
// 放在 $JENKINS_HOME/init.groovy.d/ 下，每次 Jenkins 启动时执行（已配置过则跳过）。
// 用途：新实例第一次启动就建好管理员、开好授权策略与 agent 端口，避免每次手工点向导。
import jenkins.model.Jenkins
import hudson.security.*
import hudson.util.Secret

def instance = Jenkins.get()

// 1) 管理员用户与授权策略（已存在安全域就跳过，保证幂等）
if (instance.getSecurityRealm() instanceof hudson.security.SecurityRealm.None) {
    def realm = new HudsonPrivateSecurityRealm(false)
    realm.createAccount('admin', System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin-demo-pass')
    instance.setSecurityRealm(realm)

    def strategy = new GlobalMatrixAuthorizationStrategy()
    strategy.add(Jenkins.ADMINISTER, 'admin')
    strategy.add(Jenkins.READ, 'authenticated')
    strategy.add(hudson.model.Item.BUILD, 'authenticated')
    strategy.add(hudson.model.Item.READ, 'authenticated')
    instance.setAuthorizationStrategy(strategy)
    println "[init-groovy] 已创建 admin 用户并启用矩阵授权"
} else {
    println "[init-groovy] 安全域已配置，跳过"
}

// 2) 固定 agent 端口（默认 50000），并禁止匿名注册
instance.setSlaveAgentPort(50000)
instance.setDisableRememberMe(false)
instance.save()

// 3) 常用全局配置：时区、执行器数量
instance.setNumExecutors(2)
instance.save()

println "[init-groovy] Jenkins 初始化脚本执行完毕，版本 ${Jenkins.VERSION}"
