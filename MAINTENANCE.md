# 网站维护

地址：https://zhangjianbai-archive.github.io/blog/

运行 `python build.py` 构建（Python 3.11+，无第三方依赖）。GitHub Actions 在 main 更新后自动发布 docs/。

分类名称与顺序保存在 content/categories.json，对应用户提供的 12 份文档。content/articles.json 当前为空，未导入文档。以后每篇文章需提供 slug、title、author、category 及 sections（heading 和 paragraphs）。正文会进行 HTML 转义。

样式与搜索脚本位于 docs/assets/。首页直接展示分类，不设关于或示例页面。构建仅清理 docs/ 中生成的 HTML，并检查内部链接；不删除静态资源。README 保留原文，不随网站文案调整。
