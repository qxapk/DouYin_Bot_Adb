# 抖音群机器人，监控抖音群消息，去水印后自动上传百度网盘

[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badge/) [![MIT Licence](https://badges.frapsoft.com/os/mit/mit.svg?v=103)](https://opensource.org/licenses/mit-license.php)      

最近科技和狠活，总有视频莫名其妙被封，但视频做的特别好，为了避免视频消失、被封。

我开发了个抖音群机器人框架。全部开源


##  优点
对比其他去水印的优点，就是不用复制链接，不用看广告，更不用漫长的时间等待下载，且占用手机内存、流量

只需要转发到抖音群，全自动去水印，上传到该用户百度网盘



##  技术特性

- [x] **过滤字符串，各种乱七八糟的特殊符号**
- [x] **安卓模拟器，Adb循环命令**
- [x] **基于Adb，获取安卓系统级文件**
- [x] **自研发去水印函数**

## 原理

- 基于雷电模拟器adb
- 将多闪App缓存数据库文件复制到电脑
- 基于Python读取多闪数据库
- 根据多闪数据库开发机器人框架
- 基于百度网盘Api，上传文件

## 使用教程

- Python版本：3.0及以上
- 安装雷电模拟器，开启root，本地Adb
- 模拟器内安装：多闪、mt管理器
- 将模拟器安装目录例如：C:\leidian\LDPlayer9，加入环境变量
- 百度搜索：百度网盘上传APi 免费申请 `AppKey` 和 `AppID`
- user_duo_shan.db，文件看代码，放在对应目录中即可
- 用户只需要在群内回复以下消息：
- 昵称：小千哥，授权：ea58425d3e294b3260fd
- 即可将用户抖音id，绑定到用户的百度网盘之后该用户发到群里的视频都会上传到对应网盘


## 联系

微信公众号：小千哥

公众号时常分享前沿黑科技代码、思路，欢迎关注！