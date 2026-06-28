# 昱丰保险 RED Content Engine

本项目是昱丰保险小红书内容运营系统的 Streamlit 应用，用于完成内容生成、合规初筛、发布排期、评论私信回复、数据复盘和反馈知识库沉淀。

## 功能

- 品牌知识库与用户洞察
- 小红书选题、标题、正文和封面文案生成
- 视觉 Prompt 生成
- 保险内容合规初筛
- 发布排期管理
- 评论私信回复建议
- 数据复盘可视化
- 反馈知识库保存

## 运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Cloud

如果从仓库根目录部署，入口文件填写：

```text
yufeng-red-content-system/app.py
```

并在 Streamlit Cloud 的 Secrets 中配置：

```toml
DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
```

## 目录

- `knowledge_base/`：品牌、产品、风格、合规、用户资料。
- `prompts/`：Prompt 模板。
- `data/`：发布排期和数据复盘的本地 CSV。
- `output/`：生成结果和 Excel。
- `app.py`：Streamlit 网页界面。
- `generate_content.py`：生成逻辑。

## 注意

生成内容仅作为运营初稿，正式发布前仍需人工及合规审核。不要把本地 API Key 文件上传到 GitHub。
