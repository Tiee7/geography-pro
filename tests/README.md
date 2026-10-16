# 第一章响应式回归检查

应用仍是静态网页，不需要构建或包管理器。测试使用 Python、Playwright 和 Chromium；云开发环境已安装这些工具。其他机器可安装 `playwright` 并执行 `python3 -m playwright install chromium`，再通过 `CHROMIUM_PATH` 指向浏览器可执行文件。

在仓库根目录用一个终端启动 `python3 -m http.server 8080`，另一个终端运行：

```sh
python3 tests/chapter01-responsive.py
```

可用 `GEOGRAPHY_TEST_URL` 指定测试服务器地址，`CHROMIUM_PATH` 指定 Chromium 路径（默认 `/usr/bin/chromium`）。可用 `GEOGRAPHY_TEST_VIEWPORTS=320x568,390x844` 只重跑受改动影响的尺寸。

脚本检查 9 种手机、平板和桌面尺寸：画布比例、横向溢出、分页、暂停、速率、日期、课程内容、所有图层、城市选择、视角和展开模式。390px 设备额外检查 Chromium 真实触控旋转、双指缩放及横竖屏切换；桌面额外检查分页键盘导航。截图输出至临时目录。

测试用 Python 的标准 HTTPS 校验和环境代理下载真实 CDN 资源，再交给浏览器加载，避免云浏览器自身信任库差异；未关闭 TLS 校验。场景状态读取通过测试路由临时注入，生产源码不暴露测试对象。
