# Yilena 个人主页使用说明

## 上传文件

将压缩包内容合入 `xie480/xie480` 的默认分支：`README.md`、完整 `assets/`、`.github/`、`tools/` 和 `doc/`。务必保留仓库已有的 `.github/workflows/snake.yml`，不要整目录删除后替换。

封面已原样使用用户提供的第二张黑发角色附件。计数器已改为用户指定的 rule34 配置（offset=0、scale=1.0），GitHub/Gitee 贪吃蛇和樱花 GIF 保留。Code & daydreams 已删除。

## 丰富统计：无需新增用户 secret

页面已包含真实获取的 6 类统计：贡献趋势、连续贡献、仓库语言、提交语言、基础指标、北京时间提交时段。初始图是 2026-10-27 获取的服务输出；上传后打开 **Actions → Profile statistics → Run workflow** 可立即刷新，之后每日北京时间 09:37 左右执行（GitHub 定时可能延迟）。

此工作流只 GET 固定的公开统计图片，不收集用户凭据。写回使用 Actions 自带 token 和 `contents: write`。若仓库策略禁止直接写默认分支，则需按仓库策略允许或改为 PR 流程；本次没有调整远程权限。

每张图独立验证 HTTP、MIME、XML、必要统计字段与调色。错误图或网络失败不覆盖上一份成功图。四张小卡生成桌面两列、手机单列两份组合图；Profile 也有手机上下排版，均保留真实数字与图形路径。

## 可选 Metrics：增加公开活动补充卡

1. 创建用于读取公开资料的 classic PAT，只使用公开资料时不勾选 scope。
2. 保存为此仓库的 Actions secret：`METRICS_TOKEN`。不要写入代码、README 或图片 URL。
3. 打开 **Actions → Profile metrics → Run workflow**。

成功后在现有统计下增加一张公开活动与社区统计卡，包含最近 30 天最多 4 条公开事件。现有六类统计不会被替换。未配置 secret 时正常跳过，页面不会出现占位错误图。

Metrics 的默认刷新时间为北京时间 09:17 左右；两个工作流共用 `profile-assets` 并发组。分支在生成期间前进时跳过发布，最后使用普通 fast-forward push，不会 force push 或覆盖远程新提交。

不要在 `METRICS:START/END` 中手动加入其他内容。该区域只允许初始空白或脚本自身生成的活动卡，避免自动覆盖用户编辑；丰富统计位于标记区外。

## UI 样式如何生效

博客、邮箱、章节标题和收尾使用本地 SVG 组件。SVG 内嵌 CSS 类控制背景与颜色，字形已转为路径，因此不需要浏览者加载外部字体。

`assets/ui/theme.css` 是对应样式参考。GitHub README 不会全局加载它；真正生效的样式在各个 SVG 的 `<style>` 中。修改单张 SVG 的类样式即可调整该组件；也可在 Windows 安装有 `fontTools` 的 Python 环境运行 `python tools/render-ui.py`，从生成脚本重新输出整套组件。该生成器读取本机 Georgia、宋体和微软雅黑；无需将字体文件提交到 GitHub。它不是工作流运行依赖。

README 只用允许的 HTML、链接和图片选择，不依赖网页 CSS 或 JavaScript。按钮支持真实链接与键盘访问；图片形式的 SVG 不提供网页按钮的 hover 动效。

## 数据口径与已知边界

Summary Cards 的托管接口按其自身规则汇总，部分卡统计的是按 stars 排序的最多 100 个仓库；语言图按仓库或提交的口径不同。Streak 按贡献图统计贡献与连续天数。服务存在缓存，贡献总量、commit 数和卡片请求时刻不应被当成同一个口径，也没有为统一数字改写数据。

统计组件的 MIT 许可证保存在 `assets/stats/licenses/`。计数器原 URL 中的 `num=3194927054` 被完整保留，本次不将它解读成真实访问量。

本地已验证图片、响应式选择、工作流语法、失败保留与内容保护。远程 GitHub 渲染、Actions 首次执行和 Metrics 真实生成仍需上传后确认。详细证据见 `doc/profile/readme/2026-10-27-GitHub个人主页视觉改版.md`。


## 2026-10-27 本地仓库更新

已直接安装到 `E:\YilenaCode\xie480`。封面下方独立的中文题句图片及其生成代码已移除；封面原图保持不变。计数器完整地址：

`https://count.getloli.com/@Yilena-INFO?theme=rule34&padding=1&offset=0&align=top&scale=1.0&pixelated=1&darkmode=auto&num=3194927054`
