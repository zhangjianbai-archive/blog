# 网站维护

地址：https://zhangjianbai-archive.github.io/blog/

运行 `python build.py` 构建（Python 3.12+，无第三方依赖）。GitHub Actions 在 main 更新后自动发布 docs/。

分类保存在 content/categories.json；12 份文档对应的标签保存在 content/tags.json。标签的 title 保存完整名称，label 用于侧栏短名称。content/features.json 保存各分类下的专题问题标题。

content/catalog.json 是独立的标题目录，目前有 135 个条目。字段包括 slug、title、author、authorSource、category、topic、tags、kind 和 source；source 保存原文档名、标题段落的零基序号及原始标题文本，便于核对。目录不保存正文、摘要、图片或文档下载地址，构建程序会拒绝额外的正文字段。只有带 article 字段的条目才链接到对应的已发布全文，其余显示“仅标题”，不生成空文章页。相同标题、不同作者的条目保留，例如两篇《简评清一给施畅的公开信》。作者未署名时保留空值；按合集名称归属的作者使用 authorSource=collection，明确署名使用 byline，文末署名使用 signature。

录入时合并被换行拆开的标题，去掉合集排列序号，保留原题措辞。DOCX 中的系列总标题、正文小标题、普通评论及引用的外部文章链接不作为独立文章。张乘风合集末尾有标题的短评单列并标记“短评”；茅箴合集中的《清一新教育的孩子的笑——背后的压抑》同样单列；前教师合集末尾的基金时间线标记“附记”；第 12 份材料标记“言论材料”。茅箴文件名虽为“7篇”，文内实际有 8 个具名条目，包含 1 则短评，按内容录入。

content/articles.json 收录 135 个正文条目（含短评、附记与言论材料）。132 个新转入条目的原文段落范围、文字散列与图片引用数保存在 content/import-audit.json。import_docx.py 使用全部目录条目确定边界，避免跳过已发布文章后把正文串入相邻文章。此次只修正两处主副标题拼接分隔及末尾杂字符，原始标题仍保留在 catalog 的 rawTitle。核对是转录一致性检查，不是对原文观点的独立事实认证。添加全文时，另行核对内容后写入此文件，并给 catalog 中对应条目添加 article 引用，避免重复录入标题。全文需提供 slug、title、author、category、tags（标签 slug 数组）以及 sections（heading 和 paragraphs）；excerpt 为首页原文节选，summary 为摘要。date、dateLabel、updatedAt 分别保存日期、日期性质及完整时间；不要将编辑时间当成首次发表时间。正文会进行 HTML 转义；段落也可以使用 image 和 alt 字段插入随文图片。

样式与搜索脚本位于 docs/assets/。首页最多五篇短节选，推荐帖子固定取前三篇。文章目录为统一筛选结果页，每页 20 条；q/category/topic/tag/author/readable/page 查询参数保存筛选状态。右侧链接在目录页内直接筛选，其他页面进入对应结果。支持组合筛选、单项清除、清空条件、浏览器前进后退，以及正文返回时恢复结果与滚动位置。手机端目录上方有可折叠选择器，正文有可折叠文章目录。分类与标签页只展示选择入口；旧的专题与标签地址仍可访问，并转入对应筛选。关于页独立渲染 content/who-is-zhang-jianbai.md 和 content/blog-introduction.md，README 保持原文。构建检查站内链接并清理生成的 HTML，不删除静态资源。

本地先运行 `python build.py`，再运行 `python preview.py`，访问 http://localhost:8765/blog/ 。预览服务将 /blog/ 映射到 docs/，与 GitHub Pages 的项目路径一致。直接用普通静态服务器挂载 docs/ 到根目录会导致 /blog/assets/ 样式路径失效。
