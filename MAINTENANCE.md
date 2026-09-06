# 网站维护

地址：https://zhangjianbai-archive.github.io/blog/

运行 `python build.py` 构建（Python 3.12+，无第三方依赖）。GitHub Actions 在 main 更新后自动发布 docs/。

分类保存在 content/categories.json；12 份文档对应的标签保存在 content/tags.json。content/articles.json 当前为空。每篇文章需提供 slug、title、author、category、tags（标签 slug 数组）以及 sections（heading 和 paragraphs）；可以补充 summary、type、date。正文会进行 HTML 转义。

样式与搜索脚本位于 docs/assets/。沿用第一版首页、文章栏与侧栏布局，分类页提供分类卡片和标签入口。没有关于页或示例阅读页。构建仅清理 docs/ 中生成的 HTML，并检查内部链接；不删除静态资源。README 保留原文，不随网站文案调整。

本地先运行 `python build.py`，再运行 `python preview.py`，访问 http://localhost:8765/blog/ 。预览服务将 /blog/ 映射到 docs/，与 GitHub Pages 的项目路径一致。直接用普通静态服务器挂载 docs/ 到根目录会导致 /blog/assets/ 样式路径失效。
