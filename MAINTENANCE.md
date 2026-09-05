# 网站维护

本站是 GitHub Pages 项目站点，地址为 https://zhangjianbai-archive.github.io/blog/ 。

## 本地构建

安装 Python 3.11 或更新版本后，在仓库根目录运行 `python build.py`，无需第三方依赖。输出为 `docs/`。CSS、JS、图标直接维护在 `docs/assets/`。

GitHub Actions 会在 main 更新时自动构建并发布，无需手工提交生成的 HTML。README 保留用户原文；维护文档单独存放。

## 内容

`content/articles.json` 保存条目。每篇包含唯一 `slug`、`title`、`summary`、`author`、`date`、`type`、`sample` 以及 `sections`（每节的 `heading` 和 `paragraphs`）。当前只有站务示例，未导入任何 Word 文档。

这是首版展示用的数据结构。导入正式材料前扩充来源 URL、原始发表日期、收录日期、修订记录字段，并对应修改阅读页。不要仅把 `sample` 改成 false：当前阅读页的示例与来源说明也是示例专用，需要同步更新模板。

示例阅读页设为 noindex 且不进入 sitemap。栏目入口开放索引。项目站点无法控制域名根目录的 robots.txt；不在 /blog/ 放置无效的 robots.txt。

## 验证与发布

构建自动检查所有站内绝对链接和资源是否存在。Pages 配置使用 GitHub Actions。每次发布成功后检查首页、文章搜索、文章目录锚点和移动端布局。

网站不收集访客数据，无评论后台、外部字体或追踪脚本。更正入口使用仓库 Issues。
