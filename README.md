# 昱丰保险小红书内容运营系统

面向昱丰保险内容运营的小红书本地工作台，用于完成从内容生产、合规初筛、发布排期、评论私信回复、数据复盘到反馈知识库沉淀的完整流程。

## 在线访问

Streamlit Cloud 链接：部署完成后在这里填写线上地址

## 部署信息

- GitHub 仓库：昱丰保险小红书内容运营系统
- 入口文件：`yufeng-red-content-system/app.py`
- 依赖文件：`yufeng-red-content-system/requirements.txt`
- Python 运行方式：Streamlit

## 功能模块

- 内容生产：生成小红书选题、标题、封面文案、正文、视觉 Prompt 和合规初筛结果
- 发布排期：记录待发布内容、发布时间、发布账号、栏目、状态和链接
- 评论私信：根据用户问题生成合规回复建议，并提示人工确认风险
- 数据复盘：录入或检索内容数据，生成阅读率、互动率、收藏率、咨询率等可视化分析
- 反馈知识库：沉淀用户真实问题、高频异议、高表现选题、高转化标题和合规风险提醒

## 本地运行

进入项目目录后运行：

```bash
cd yufeng-red-content-system
pip install -r requirements.txt
streamlit run app.py
```

打开浏览器访问：

```text
http://localhost:8501
```

## Streamlit Cloud 部署

1. 把本项目上传到 GitHub。
2. 登录 Streamlit Community Cloud。
3. 选择对应 GitHub 仓库和分支。
4. Main file path 填写：

```text
yufeng-red-content-system/app.py
```

5. 在 Secrets 中配置：

```toml
DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
```

6. 点击 Deploy。

## 注意事项

- 不要上传本地的 `DEEPSEEK_API_KEY.env`、`OPENAI_API_KEY.env` 或 `.env` 文件。
- `data/` 和 `output/` 里的内容属于本地运行数据，不建议上传到公开仓库。
- 系统生成内容只作为运营初稿，正式发布前仍需人工复核和合规审核。
