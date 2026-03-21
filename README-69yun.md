这是一个用来机场自动签到免费领取流量的GitHub Actions自动脚本
GitHub Actions使用方法
- 项目地址: https://github.com/amclubs/am-check-in
### ① 复制仓库代码
1. 把当前github的项目能过 use this template 复制创建到你的创建里。
### ② 设置 GitHub Actions 变量
1. Settings -> secrets and variables -> Actions -> Secrets -> New repository secrets
2. 设置对应的变量参数
      YUN69_DOMAIN            YUN69_USERNAME        YUN69_PASSWORD 
3. (可选)设置TG通知参数 TG_BOT_TOKEN、TG_CHAT_ID （详情参数看下面变量说明）
### ③ 设置定时任务时间
1. 进入代码.github/workflows -> check-in-job.yml 
2. 修改定时任务时间 cron (推荐修改成其它时间)
~~~
on:
  schedule:
    - cron: '0 0 * * *'  # 每天 00:00 UTC 执行，调整为你需要的时间
  workflow_dispatch:  # 允许手动触发
~~~
 
