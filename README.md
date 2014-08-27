dmzj_comic
==========

Download all comics from manhua.dmzj.com(可下载动漫之家网所有漫画)

**依赖**:

* python3
* 第三方类库[requests](http://docs.python-requests.org/en/latest/user/install/#install)
* [python3-pyqt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5) (GUI依赖，不用GUI可不装)

ubuntu系列系统使用以下命令安装依赖：

    sudo apt-get update ; sudo apt-get install python3 python3-requests
    sudo apt-get install python3-pyqt5 #GUI依赖，不用GUI可不装

URL格式: 漫画首页的URL，如``http://mh.dmzj.com/shizhong/``(移动版) 或 ``http://manhua.dmzj.com/shizhong/``(PC版)

**命令行帮助**

```bash
./dmzjComic.py -h
usage: dmzjComic.py [-h] [-u URL] [-p PATH] [-l LIST]

*下载腾讯漫画，仅供学习交流，请勿用于非法用途*
空参运行进入交互式模式运行。

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     要下载的漫画的首页，可以下载以下类型的url: 
                        http://manhua.dmzj.com/shizhong/
                        http://mh.dmzj.com/shizhong/
  -p PATH, --path PATH  漫画下载路径。 默认: /home/***/dmzj_comic
  -l LIST, --list LIST  要下载的漫画章节列表，不指定则下载所有章节。格式范例: 
                        N - 下载具体某一章节，如-l 1, 下载第1章
                        N,N... - 下载某几个不连续的章节，如 "-l 1,3,5", 下载1,3,5章
                        N-N... - 下载某一段连续的章节，如 "-l 10-50", 下载[10,50]章
                        杂合型 - 结合上面所有的规则，如 "-l 1,3,5-7,11-111"
```

另有GUI版可用

附：本脚本借鉴了abcfy2的getComic，项目url：https://github.com/abcfy2/getComic
