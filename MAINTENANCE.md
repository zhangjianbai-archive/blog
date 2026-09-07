# 网站维护

地址：https://zhangjianbai-archive.github.io/blog/

运行 `python build.py` 构建（Python 3.12+，无第三方依赖）。GitHub Actions 在 main 更新后自动发布 docs/。

分类保存在 content/categories.json；12 份文档对应的标签保存在 content/tags.json。标签的 title 保存完整名称，label 用于侧栏短名称。content/articles.json 当前只收录三篇精选文章，其余文档未导入。每篇文章需提供 slug、title、author、category、tags（标签 slug 数组）以及 sections（heading 和 paragraphs）；excerpt 为首页原文节选，summary 为摘要。date、dateLabel、updatedAt 分别保存日期、日期性质及完整时间；不要将编辑时间当成首次发表时间。正文会进行 HTML 转义；段落也可以使用 image 和 alt 字段插入随文图片。

样式与搜索脚本位于 docs/assets/。首页为三篇文章的节选列表，左上角搜索，右侧为专题、分类、标签链接；专题标题保存在 content/features.json。分类页列出文章，文章页面包含完整正文、随文图片和章节目录。搜索涵盖标题、作者、正文、分类与标签。关于页从 README 渲染博客介绍，仅转换 Markdown 格式；README 本身保持原文。没有示例阅读页。构建仅清理 docs/ 中生成的 HTML，并检查内部链接；不删除静态资源。

本地先运行 `python build.py`，再运行 `python preview.py`，访问 http://localhost:8765/blog/ 。预览服务将 /blog/ 映射到 docs/，与 GitHub Pages 的项目路径一致。直接用普通静态服务器挂载 docs/ 到根目录会导致 /blog/assets/ 样式路径失效。
