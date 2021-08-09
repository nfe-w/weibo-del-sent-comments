# weibo-del-sent-comments

## 简介

可以「批量查询、导出、删除自己发出的微博评论」的小脚本，用于保护个人隐私及删除黑历史

请在执行删除前再三确认时间范围，防止误删！作者对误删的评论概不负责！

## 运行环境

- [Python 3](https://www.python.org/)

## 使用教程

#### 0. 获取cookie的说明

1. 使用chrome登录手机网页版微博，按`F12`调出控制台
2. 切换至`Network`页签下的`XHR`过滤
3. 点击任意链接或个人中心，在下方的请求列表中点击任一请求
4. 在右侧的`Headers`页签中的`Request Headers`部分，即可看到`cookie`，将其全部内容复制即可

#### 1. 修改config.json配置信息

- `cookie`需要从 https://m.weibo.cn 获取
- `start_page`起始页数（包含）
- `end_page`终止页数（包含）
- `start_date`起始日期，小日期（包含），格式为`2000-01-01`
- `end_date`终止日期，大日期（包含），格式为`2099-12-31`
- `enable_delete`是否启用删除功能
- `enable_out_excel`是否导出excel，导出路径为项目路径
- `enable_out_database`是否保存到数据库（MySQL），如为`false`则下方数据库相关参数可忽略
- `database_host`MySQL-ip
- `database_port`MySQL-端口
- `database_user`MySQL-用户名
- `database_password`MySQL-密码
- `database_db`MySQL-database

#### 2.安装依赖

`pip install -r requirements.txt -i https://pypi.douban.com/simple`

#### 3.运行

`python3 weibo_del_sent_comments.py`

## 一些说明

由于使用了`m.weibo.cn`的删除评论api，此api经过实测每`10`分钟仅可删除`60`条评论，所以删除评论的部分没有使用协程（确实没必要）

## 声明

- 本仓库发布的`weibo-del-sent-comments`项目中涉及的任何脚本，仅用于测试和学习研究，禁止用于商业用途
- `nfe-w`对任何脚本问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害
- 以任何方式查看此项目的人或直接或间接使用`weibo-del-sent-comments`项目的任何脚本的使用者都应仔细阅读此声明
- `weibo-del-sent-comments` 保留随时更改或补充此免责声明的权利。一旦使用并复制了任何相关脚本或`weibo-del-sent-comments`项目，则视为已接受此免责声明
- 本项目遵循`MIT LICENSE`协议，如果本声明与`MIT LICENSE`协议有冲突之处，以本声明为准
