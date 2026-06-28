from __future__ import annotations

from datetime import date, time
from html import escape
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from generate_content import (
    OUTPUT_DIR,
    build_cover_visual_prompt,
    export_to_excel,
    generate_content_batch,
    load_dotenv,
    load_config,
)


LOGO_ICON = Path(__file__).resolve().parents[1] / "SVG" / "昱丰保险logo.svg"


st.set_page_config(
    page_title="YFG RED Content Engine",
    page_icon=str(LOGO_ICON),
    layout="wide",
)


TEXT = {
    "zh": {
        "language": "语言 / Language",
        "sidebar_title": "YFG 控制台",
        "sidebar_desc": "把品牌知识库、选题、文案、视觉 Prompt 和合规初筛串成一个本地内容流程。",
        "params": "生成参数",
        "api_ready": "云端生成：DeepSeek Cloud ready",
        "api_missing": "云端生成：未配置 DeepSeek API key，当前会使用本地回退",
        "product": "产品方向",
        "audience": "目标人群",
        "content_type": "内容类型",
        "count": "生成数量",
        "export_passed": "只导出合规评分80分以上内容",
        "generate": "生成内容批次",
        "eyebrow": "YFG Prestige content operations",
        "hero_title": "RED Content Engine",
        "hero_desc": "一个面向昱豐保险内容运营的本地工作台。选择产品方向、人群与内容类型后，系统生成小红书标题、封面文案、正文、视觉 Prompt 与合规初审结果，再导出为可复核的内容表。",
        "empty_title": "从一组参数开始生成内容",
        "empty_desc": "左侧选择产品方向、目标人群和内容类型。第一版会先用本地知识库和规则模板生成可演示初稿，适合做内部流程验证和老板演示。",
        "workflow": [
            ("1 品牌知识库", "品牌资料、产品资料、合规规则"),
            ("2 用户洞察", "目标人群、痛点、内容入口"),
            ("3 选题策划", "主题矩阵、标题方向、栏目"),
            ("4 小红书笔记生成", "标题、封面、正文、标签"),
            ("5 视觉 Prompt", "封面和长图画面提示"),
            ("6 合规审查", "风险评分、修改建议、复核提醒"),
            ("7 发布排期", "发布时间、账号、栏目、状态"),
            ("8 评论私信回复", "用户意图、回复建议、人工提醒"),
            ("9 数据复盘优化", "阅读率、互动率、咨询率"),
            ("10 反馈知识库", "高频问题、爆款经验、风险提醒"),
        ],
        "results": "生成结果预览",
        "metric_count": "内容数量",
        "metric_avg": "平均合规评分",
        "metric_pass": "80分以上",
        "metric_review": "建议人工复核",
        "download": "导出内容日历 Excel",
        "tab_cards": "内容审阅",
        "tab_table": "表格数据",
        "item": "项目",
        "score": "合规评分",
        "risk": "风险等级",
        "format": "内容形式",
        "goal": "目标",
        "source": "生成来源",
        "cover": "封面文案",
        "body": "正文",
        "tags": "标签",
        "visual_prompt": "封面图 Prompt",
        "risk_revision": "合规风险与修改后版本",
        "revised": "修改后版本",
        "chips": ["Brand KB", "Topic strategy", "XHS note draft", "Visual prompt", "Compliance screen"],
    },
    "en": {
        "language": "Language / 语言",
        "sidebar_title": "YFG Console",
        "sidebar_desc": "A local workflow connecting the brand knowledge base, topics, copy, visual prompts, and compliance screening.",
        "params": "Generation Settings",
        "api_ready": "Cloud generation: DeepSeek Cloud ready",
        "api_missing": "Cloud generation: no DeepSeek API key configured, using local fallback",
        "product": "Product Direction",
        "audience": "Target Audience",
        "content_type": "Content Type",
        "count": "Number of Drafts",
        "export_passed": "Export only content scored 80+",
        "generate": "Generate Batch",
        "eyebrow": "YFG Prestige content operations",
        "hero_title": "RED Content Engine",
        "hero_desc": "A local content workspace for Yu Fung Broker. Choose the product direction, audience, and content type, then generate Xiaohongshu titles, cover copy, note drafts, visual prompts, and initial compliance results for review.",
        "empty_title": "Start From One Set Of Parameters",
        "empty_desc": "Choose a product direction, audience, and content type from the left panel. The first version uses the local knowledge base and rule templates to create reviewable drafts for internal workflow validation.",
        "workflow": [
            ("1 Brand KB", "Brand facts, product notes, compliance rules"),
            ("2 User Insight", "Audience pain points and entry angles"),
            ("3 Topic Plan", "Topic matrix, title direction, columns"),
            ("4 XHS Draft", "Title, cover, body, tags"),
            ("5 Visual Prompt", "Cover and long-image prompts"),
            ("6 Compliance", "Risk score and review notes"),
            ("7 Publish Plan", "Time, account, column, status"),
            ("8 Replies", "Intent, reply suggestion, human review"),
            ("9 Data Review", "Read, engagement, inquiry rates"),
            ("10 KB Feedback", "Questions, learnings, risk reminders"),
        ],
        "results": "Generated Content Preview",
        "metric_count": "Drafts",
        "metric_avg": "Avg. Compliance Score",
        "metric_pass": "80+ Score",
        "metric_review": "Manual Review",
        "download": "Export Content Calendar Excel",
        "tab_cards": "Content Review",
        "tab_table": "Table Data",
        "item": "ITEM",
        "score": "Compliance Score",
        "risk": "Risk Level",
        "format": "Format",
        "goal": "Goal",
        "source": "Source",
        "cover": "Cover Copy",
        "body": "Body",
        "tags": "Tags",
        "visual_prompt": "Cover Image Prompt",
        "risk_revision": "Compliance Risks And Revised Version",
        "revised": "Revised Version",
        "chips": ["Brand KB", "Topic strategy", "XHS note draft", "Visual prompt", "Compliance screen"],
    },
}


OPTION_LABELS = {
    "en": {
        "香港保险": "Hong Kong Insurance",
        "IUL": "IUL",
        "家庭保障": "Family Protection",
        "子女教育金": "Children's Education Fund",
        "财富传承": "Wealth Succession",
        "企业主保险规划": "Business Owner Insurance Planning",
        "高端医疗": "High-End Medical",
        "员工福利": "Employee Benefits",
        "信托与CRS": "Trust And CRS",
        "保险小白": "Insurance Beginner",
        "中产家庭": "Middle-Class Family",
        "年轻父母": "Young Parents",
        "企业主": "Business Owner",
        "高净值客户": "High-Net-Worth Client",
        "银行合作客户": "Bank Channel Client",
        "小白科普": "Beginner Education",
        "避坑清单": "Pitfall Checklist",
        "情绪共鸣": "Emotional Resonance",
        "案例场景": "Scenario Case",
        "品牌专业观点": "Brand Expert View",
        "评论区FAQ": "Comment FAQ",
        "低": "Low",
        "中": "Medium",
        "高": "High",
        "图文笔记": "Image-Text Note",
        "长图/轮播": "Long Image / Carousel",
        "场景案例": "Scenario Case",
        "品牌观点": "Brand View",
        "问答笔记": "Q&A Note",
        "建立认知": "Build Awareness",
        "收藏+转发": "Save + Share",
        "评论互动": "Comment Engagement",
        "私信咨询": "DM Inquiry",
        "建立信任": "Build Trust",
        "降低疑虑": "Reduce Concerns",
        "收藏": "Save",
    }
}


def t(lang: str, key: str):
    return TEXT[lang][key]


def display_label(value: str, lang: str) -> str:
    if lang == "zh":
        return value
    return OPTION_LABELS["en"].get(value, value)


def inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #041E42;
            --gold: #8F5A39;
            --gold-soft: #C8A878;
            --paper: #F5F5F6;
            --ink: #292C2D;
            --muted: #6C7280;
            --line: rgba(4, 30, 66, 0.12);
        }

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        .stApp {
            background:
                linear-gradient(135deg, rgba(4, 30, 66, 0.045), transparent 34%),
                linear-gradient(180deg, #FBFAF7 0%, #F5F5F6 100%) !important;
            color: var(--ink) !important;
        }

        header[data-testid="stHeader"] {
            height: 0 !important;
            min-height: 0 !important;
            background: transparent !important;
            border-bottom: 0 !important;
            pointer-events: none;
            visibility: hidden;
        }

        div[data-testid="stToolbar"],
        .stDeployButton,
        #MainMenu {
            display: none !important;
            visibility: hidden !important;
        }

        footer {
            display: none !important;
            visibility: hidden !important;
        }

        .stApp {
            background:
                linear-gradient(135deg, rgba(4, 30, 66, 0.045), transparent 34%),
                linear-gradient(180deg, #FBFAF7 0%, #F5F5F6 100%);
            color: var(--ink);
        }

        .main,
        section.main,
        div[data-testid="stMain"],
        div[data-testid="stVerticalBlock"] {
            background: transparent !important;
        }

        .block-container {
            padding: 2rem 2.4rem 3rem;
            max-width: 1440px;
        }

        div[data-baseweb="tab-list"],
        [role="tablist"] {
            position: static !important;
            z-index: 1 !important;
            background: transparent !important;
            margin: 10px 0 18px;
            border-bottom: 1px solid rgba(4, 30, 66, 0.10);
        }

        [role="tab"] {
            min-height: 2.75rem;
            padding-top: 0.55rem !important;
            padding-bottom: 0.55rem !important;
        }

        h1,
        h2,
        h3,
        h4,
        [data-testid="stHeadingWithActionElements"] {
            scroll-margin-top: 32px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071F43 0%, #04152D 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.10);
            top: 0 !important;
            height: 100vh !important;
        }

        section[data-testid="stSidebar"] * {
            color: rgba(255, 255, 255, 0.92);
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stSlider label {
            color: rgba(255, 255, 255, 0.78) !important;
            font-size: 0.84rem;
            letter-spacing: 0;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"],
        section[data-testid="stSidebar"] .stSlider {
            color: var(--ink);
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="select"] [role="button"],
        section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"] {
            background: #FFFFFF !important;
            border-color: rgba(255, 255, 255, 0.14) !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"] * {
            color: #1D2733 !important;
            fill: #1D2733 !important;
        }

        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"] {
            background: #FFFFFF !important;
            color: #1D2733 !important;
        }

        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"] *,
        ul[role="listbox"] * {
            color: #1D2733 !important;
            fill: #1D2733 !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 6px;
            border: 1px solid rgba(143, 90, 57, 0.42);
            background: linear-gradient(135deg, #8F5A39 0%, #B99064 100%);
            color: #FFFFFF;
            font-weight: 700;
            letter-spacing: 0;
            min-height: 2.8rem;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: #D7B989;
            box-shadow: 0 10px 24px rgba(4, 30, 66, 0.14);
            color: #FFFFFF;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
        }

        div[data-testid="stMetricValue"] {
            color: var(--navy);
            font-weight: 800;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        .hero {
            position: relative;
            overflow: hidden;
            padding: 28px 30px;
            border: 1px solid rgba(4, 30, 66, 0.14);
            border-radius: 8px;
            background:
                linear-gradient(120deg, rgba(255,255,255,0.94) 0%, rgba(251,250,247,0.90) 58%, rgba(200,168,120,0.16) 100%);
            box-shadow: 0 18px 54px rgba(4, 30, 66, 0.08);
            margin-bottom: 20px;
        }

        .hero:after {
            content: "";
            position: absolute;
            right: 30px;
            top: 28px;
            width: 272px;
            height: 112px;
            border: 1px solid rgba(200, 168, 120, 0.24);
            border-left: 0;
            background:
                repeating-linear-gradient(0deg, rgba(4, 30, 66, 0.07) 0 1px, transparent 1px 20px),
                linear-gradient(90deg, transparent 0 14%, rgba(200,168,120,0.20) 14% 14.5%, transparent 14.5% 100%);
            clip-path: polygon(0 78%, 10% 72%, 22% 74%, 34% 58%, 45% 62%, 56% 42%, 68% 48%, 82% 25%, 100% 32%, 100% 100%, 0 100%);
            opacity: 0.58;
        }

        .eyebrow {
            color: var(--gold);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .hero h1 {
            color: var(--navy);
            font-size: clamp(2rem, 4vw, 4.1rem);
            line-height: 0.98;
            margin: 0 0 12px;
            letter-spacing: 0;
        }

        .hero p {
            max-width: 760px;
            color: #46505D;
            font-size: 1.02rem;
            line-height: 1.7;
            margin: 0;
        }

        .chip-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 18px;
        }

        .chip {
            border: 1px solid rgba(4, 30, 66, 0.12);
            border-radius: 6px;
            padding: 7px 11px;
            background: rgba(255, 255, 255, 0.72);
            color: #314156;
            font-size: 0.82rem;
            font-weight: 650;
        }

        .panel-title {
            color: var(--navy);
            font-size: 1.18rem;
            font-weight: 800;
            margin: 22px 0 10px;
        }

        .empty-panel {
            border: 1px solid rgba(4, 30, 66, 0.12);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.68);
            padding: 24px;
        }

        .workflow {
            display: grid;
            grid-template-columns: repeat(5, minmax(130px, 1fr));
            gap: 10px;
            margin-top: 16px;
        }

        .workflow-step {
            border: 1px solid rgba(4, 30, 66, 0.10);
            border-radius: 8px;
            background: #FFFFFF;
            padding: 14px;
            min-height: 92px;
        }

        .workflow-step b {
            color: var(--navy);
            display: block;
            margin-bottom: 6px;
        }

        .workflow-step span {
            color: var(--muted);
            font-size: 0.88rem;
        }

        .content-card {
            position: relative;
            border: 1px solid rgba(4, 30, 66, 0.12);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.86);
            padding: 18px 18px 18px 24px;
            margin-bottom: 16px;
            box-shadow: 0 12px 30px rgba(4, 30, 66, 0.06);
        }

        .content-card:before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 5px;
            background: linear-gradient(180deg, var(--navy), var(--gold-soft));
            border-radius: 8px 0 0 8px;
        }

        .card-kicker {
            color: var(--gold);
            font-size: 0.75rem;
            letter-spacing: 0;
            text-transform: uppercase;
            font-weight: 800;
        }

        .card-title {
            color: var(--navy);
            font-size: 1.34rem;
            font-weight: 850;
            line-height: 1.35;
            margin: 4px 0 12px;
        }

        .meta-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(120px, 1fr));
            gap: 8px;
            margin-bottom: 12px;
        }

        .meta {
            border: 1px solid rgba(4, 30, 66, 0.08);
            border-radius: 6px;
            padding: 9px 10px;
            background: #FBFAF7;
        }

        .meta span {
            display: block;
            color: var(--muted);
            font-size: 0.74rem;
        }

        .meta b {
            color: var(--navy);
            font-size: 0.94rem;
        }

        .cover-box {
            border-left: 3px solid var(--gold-soft);
            background: #FBFAF7;
            padding: 12px 14px;
            border-radius: 6px;
            color: var(--ink);
            white-space: pre-wrap;
            font-weight: 650;
        }

        .reply-card {
            position: relative;
            border: 1px solid rgba(4, 30, 66, 0.12);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.88);
            padding: 18px 18px 18px 24px;
            margin: 14px 0 18px;
            box-shadow: 0 12px 30px rgba(4, 30, 66, 0.06);
            overflow: hidden;
        }

        .reply-card:before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 5px;
            background: linear-gradient(180deg, var(--navy), var(--gold-soft));
        }

        .reply-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }

        .reply-title {
            color: var(--navy);
            font-size: 1.15rem;
            font-weight: 850;
            line-height: 1.35;
        }

        .reply-badge {
            flex: 0 0 auto;
            border: 1px solid rgba(143, 90, 57, 0.30);
            border-radius: 6px;
            background: rgba(200, 168, 120, 0.14);
            color: var(--gold);
            padding: 6px 10px;
            font-size: 0.78rem;
            font-weight: 800;
        }

        .reply-text {
            border-left: 3px solid var(--gold-soft);
            border-radius: 6px;
            background: #FBFAF7;
            padding: 14px 16px;
            color: var(--ink);
            line-height: 1.75;
            font-weight: 650;
            white-space: pre-wrap;
            margin-bottom: 12px;
        }

        .reply-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(140px, 1fr));
            gap: 8px;
        }

        .reply-meta {
            border: 1px solid rgba(4, 30, 66, 0.08);
            border-radius: 6px;
            background: rgba(251, 250, 247, 0.86);
            padding: 10px 12px;
            min-height: 74px;
        }

        .reply-meta span {
            display: block;
            color: var(--muted);
            font-size: 0.74rem;
            margin-bottom: 5px;
        }

        .reply-meta b {
            color: var(--navy);
            font-size: 0.94rem;
            line-height: 1.45;
        }

        .reply-note {
            border-radius: 6px;
            background: rgba(4, 30, 66, 0.07);
            color: #244A7A;
            padding: 12px 14px;
            margin-top: 12px;
            font-weight: 700;
            line-height: 1.6;
        }

        .risk-low {
            color: #0E6B4F;
            font-weight: 800;
        }

        .risk-mid {
            color: #8F5A39;
            font-weight: 800;
        }

        .risk-high {
            color: #9A2E2E;
            font-weight: 800;
        }

        .sidebar-brand {
            border-bottom: 1px solid rgba(255,255,255,0.14);
            padding-bottom: 14px;
            margin-bottom: 18px;
        }

        .sidebar-brand h2 {
            color: #FFFFFF;
            font-size: 1.16rem;
            margin: 0 0 5px;
        }

        .sidebar-brand p {
            color: rgba(255,255,255,0.66);
            font-size: 0.82rem;
            line-height: 1.5;
            margin: 0;
        }

        @media (max-width: 900px) {
            .workflow,
            .meta-grid,
            .reply-grid {
                grid-template-columns: 1fr;
            }
            .reply-header {
                display: block;
            }
            .reply-badge {
                display: inline-block;
                margin-top: 8px;
            }
            .block-container {
                padding: 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def risk_class(level: str) -> str:
    if level == "低":
        return "risk-low"
    if level == "中":
        return "risk-mid"
    return "risk-high"


def render_hero(lang: str) -> None:
    chips = "".join(f'<div class="chip">{escape(chip)}</div>' for chip in t(lang, "chips"))
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{escape(t(lang, "eyebrow"))}</div>
            <h1>{escape(t(lang, "hero_title"))}</h1>
            <p>{escape(t(lang, "hero_desc"))}</p>
            <div class="chip-row">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(lang: str) -> None:
    steps = "".join(
        f'<div class="workflow-step"><b>{escape(title)}</b><span>{escape(desc)}</span></div>'
        for title, desc in t(lang, "workflow")
    )
    st.markdown(
        f"""
        <div class="empty-panel">
            <div class="panel-title" style="margin-top:0;">{escape(t(lang, "empty_title"))}</div>
            <p style="color:#596273; line-height:1.7; margin:0;">
                {escape(t(lang, "empty_desc"))}
            </p>
            <div class="workflow">{steps}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_visual_prompt(item: dict) -> str:
    return build_cover_visual_prompt(
        title=str(item.get("title", "")),
        cover_copy=str(item.get("cover_copy", "")),
        product_type=str(item.get("product_type", "")),
        audience_type=str(item.get("audience_type", "")),
        content_type=str(item.get("content_type", "")),
    )


def render_card(item: dict, lang: str) -> None:
    risk = str(item["risk_level"])
    risk_css = risk_class(risk)
    st.markdown(
        f"""
        <div class="content-card">
            <div class="card-kicker">{escape(t(lang, "item"))} {int(item["index"]):02d} · {escape(display_label(str(item["content_type"]), lang))}</div>
            <div class="card-title">{escape(str(item["title"]))}</div>
            <div class="meta-grid">
                <div class="meta"><span>{escape(t(lang, "score"))}</span><b>{int(item["compliance_score"])}/100</b></div>
                <div class="meta"><span>{escape(t(lang, "risk"))}</span><b class="{risk_css}">{escape(display_label(risk, lang))}</b></div>
                <div class="meta"><span>{escape(t(lang, "format"))}</span><b>{escape(display_label(str(item["format"]), lang))}</b></div>
                <div class="meta"><span>{escape(t(lang, "source"))}</span><b>{escape(str(item.get("source", "")))}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"**{t(lang, 'cover')}**")
    st.markdown(f'<div class="cover-box">{escape(str(item["cover_copy"]))}</div>', unsafe_allow_html=True)

    st.markdown(f"**{t(lang, 'body')}**")
    st.write(item["body"])

    st.markdown(f"**{t(lang, 'tags')}**")
    st.write(item["tags"])

    with st.expander(t(lang, "visual_prompt")):
        st.write(display_visual_prompt(item))

    with st.expander(t(lang, "risk_revision")):
        st.write(item["risk_issues"])
        st.markdown(f"**{t(lang, 'revised')}**")
        st.write(item["revised_version"])


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
LOCAL_KB_DIR = APP_DIR / "knowledge_base"
PUBLISH_CALENDAR_PATH = DATA_DIR / "publish_calendar.csv"
ANALYTICS_PATH = DATA_DIR / "analytics.csv"
FEEDBACK_KB_PATH = LOCAL_KB_DIR / "feedback_kb.md"

PUBLISH_COLUMNS = [
    "标题",
    "正文",
    "封面 Prompt",
    "发布时间",
    "发布账号",
    "内容栏目",
    "目标人群",
    "状态",
    "小红书链接",
    "备注",
]

ANALYTICS_COLUMNS = [
    "标题",
    "发布时间",
    "曝光量",
    "阅读量",
    "点赞数",
    "收藏数",
    "评论数",
    "转发数",
    "关注数",
    "私信咨询数",
    "封面类型",
    "标题类型",
    "选题方向",
    "阅读率",
    "互动率",
    "收藏率",
    "咨询率",
    "涨粉率",
]

SENSITIVE_KEYWORDS = (
    "收益",
    "回报",
    "投资回报",
    "理赔",
    "保费",
    "产品对比",
    "分红",
    "保证",
    "保本",
    "现金价值",
    "IUL",
)


def ensure_storage_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_KB_DIR.mkdir(parents=True, exist_ok=True)


def items_as_records(items: list) -> list[dict]:
    return [item.__dict__ if hasattr(item, "__dict__") else dict(item) for item in items]


def read_local_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    ensure_storage_dirs()
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)


def append_local_csv(path: Path, row: dict, columns: list[str]) -> None:
    df = read_local_csv(path, columns)
    next_df = pd.concat([df, pd.DataFrame([{column: row.get(column, "") for column in columns}])], ignore_index=True)
    next_df.to_csv(path, index=False, encoding="utf-8-sig")


def classify_comment(comment: str) -> tuple[str, str]:
    text = comment.strip()
    if any(word in text for word in ("收益", "回报", "投资回报", "分红", "保本", "赚", "现金价值")):
        return "收益咨询", "不承诺收益，提醒不同产品机制、费用、条款、风险等级和个人情况都要一起看。"
    if any(word in text for word in ("理赔", "赔不赔", "拒赔")):
        return "理赔疑问", "不保证理赔结果，提醒以正式条款、投保披露、理赔材料和保险公司审核为准。"
    if any(word in text for word in ("保费", "多少钱", "价格", "贵不贵")):
        return "保费预算疑问", "不直接报价，提醒保费与年龄、健康、保障额度、缴费期和产品条款相关。"
    if any(word in text for word in ("对比", "内地", "大陆", "更好")):
        return "产品/市场对比", "不做绝对化比较，提醒从监管、币种、条款、费用、保障范围和个人需求综合评估。"
    if any(word in text for word in ("适合", "普通家庭", "预算", "能买吗")):
        return "适合度疑问", "不直接判断适合，先引导做需求、预算、现金流和保障缺口评估。"
    if any(word in text for word in ("怎么买", "购买", "投保", "流程")):
        return "购买流程疑问", "评论区不做交易引导，建议通过官方渠道和持牌顾问了解正式文件。"
    if any(word in text for word in ("靠谱吗", "智商税", "骗人", "不信")):
        return "信任/质疑", "先接住担心，再回到监管、条款、费用、适配度和专业评估。"
    return "一般咨询", "用科普口径简短回应，复杂问题引导到官方咨询渠道。"


def risk_for_comment(comment: str) -> tuple[str, str]:
    if any(word in comment for word in SENSITIVE_KEYWORDS):
        return "中", "建议人工确认后回复"
    return "低", "可人工快速确认后回复"


def build_comment_replies(comment: str, tone: str, user_type: str) -> dict[str, str]:
    intent, direction = classify_comment(comment)
    risk_level, human_review = risk_for_comment(comment)
    public_reply = {
        "收益咨询": "香港保险或 IUL 不能简单理解为“收益一定更高”。不同产品的收益机制、费用结构、风险等级和持有条件都不同，建议结合家庭预算、保障需求和风险承受能力综合评估。",
        "理赔疑问": "理赔需要以正式条款、投保时的健康及财务披露、理赔材料和保险公司审核为准，不能在评论区简单保证结果。建议先把条款中的保障范围、除外责任和理赔流程看清楚。",
        "保费预算疑问": "保费会受年龄、健康情况、保障额度、缴费期和具体条款影响，不能只用一个数字判断贵不贵。更稳妥的方式是先确认预算和保障缺口，再看方案是否匹配。",
        "产品/市场对比": "不建议简单说香港保险一定比内地保险好。不同地区产品在监管、币种、条款、费用、保障范围和适合人群上都有差异，关键还是看个人需求和合规条件。",
        "适合度疑问": "要看预算、家庭阶段、保障缺口和长期现金流。普通家庭不是不能了解，但更需要先确认基础保障和缴费能力，再判断具体方案是否匹配。",
        "购买流程疑问": "这类问题不建议在评论区直接判断或交易。可以先通过官方渠道了解基本资料，再由持牌顾问结合个人情况和正式文件做评估。",
        "信任/质疑": "这个担心很正常。保险有没有价值，关键不在别人说好不好，而在是否匹配保障缺口、现金流和长期目标，也要把条款、费用和风险看清楚。",
        "一般咨询": "可以先从需求、预算、保障缺口、条款费用和风险承受能力几个角度看。具体到个人方案时，建议通过官方渠道做完整评估。",
    }[intent]
    if tone == "简洁":
        public_reply = public_reply.split("。")[0] + "。"
    elif tone == "亲和":
        public_reply = "这个问题很多人都会关心。" + public_reply
    elif tone == "顾问式":
        public_reply = public_reply + " 更建议先做需求梳理，再看正式文件里的费用、保障和风险。"

    return {
        "评论/私信内容": comment,
        "回复语气": tone,
        "用户类型": user_type,
        "用户意图": intent,
        "回复方向": direction,
        "回复建议": public_reply,
        "合规风险等级": risk_level,
        "是否建议人工介入": human_review,
    }


def render_reply_card(result: dict[str, str]) -> None:
    risk = str(result.get("合规风险等级", "低"))
    risk_css = risk_class({"低": "低", "中": "中", "高": "高"}.get(risk, risk))
    st.markdown(
        f"""
        <div class="reply-card">
            <div class="reply-header">
                <div>
                    <div class="card-kicker">COMMENT / DM REPLY</div>
                    <div class="reply-title">{escape(str(result.get("评论/私信内容", "")))}</div>
                </div>
                <div class="reply-badge">{escape(str(result.get("回复语气", "")))} · {escape(str(result.get("用户类型", "")))}</div>
            </div>
            <div class="reply-text">{escape(str(result.get("回复建议", "")))}</div>
            <div class="reply-grid">
                <div class="reply-meta"><span>用户意图</span><b>{escape(str(result.get("用户意图", "")))}</b></div>
                <div class="reply-meta"><span>回复方向</span><b>{escape(str(result.get("回复方向", "")))}</b></div>
                <div class="reply-meta"><span>合规风险等级</span><b class="{risk_css}">{escape(risk)}</b></div>
                <div class="reply-meta"><span>人工介入</span><b>{escape(str(result.get("是否建议人工介入", "")))}</b></div>
            </div>
            <div class="reply-note">回复建议不能直接承诺收益、保证理赔或夸大产品优势；涉及敏感主题时请人工确认。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def metric_number(row: pd.Series, column: str) -> float:
    value = row.get(column, 0)
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def enrich_analytics_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    enriched = df.copy()
    numeric_columns = ["曝光量", "阅读量", "点赞数", "收藏数", "评论数", "转发数", "关注数", "私信咨询数"]
    for column in numeric_columns:
        if column not in enriched.columns:
            enriched[column] = 0
        enriched[column] = pd.to_numeric(enriched[column], errors="coerce").fillna(0)
    interaction = enriched["点赞数"] + enriched["收藏数"] + enriched["评论数"] + enriched["转发数"]
    enriched["阅读率"] = [safe_rate(reads, exposure) for reads, exposure in zip(enriched["阅读量"], enriched["曝光量"])]
    enriched["互动率"] = [safe_rate(value, reads) for value, reads in zip(interaction, enriched["阅读量"])]
    enriched["收藏率"] = [safe_rate(saves, reads) for saves, reads in zip(enriched["收藏数"], enriched["阅读量"])]
    enriched["咨询率"] = [safe_rate(dms, reads) for dms, reads in zip(enriched["私信咨询数"], enriched["阅读量"])]
    enriched["涨粉率"] = [safe_rate(follows, reads) for follows, reads in zip(enriched["关注数"], enriched["阅读量"])]
    return enriched


def find_title_matches(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if df.empty or "标题" not in df.columns or not query.strip():
        return pd.DataFrame(columns=df.columns)
    title_series = df["标题"].astype(str)
    return df[title_series.str.contains(query.strip(), case=False, na=False)]


def render_title_visualization(row: pd.Series) -> None:
    title = str(row.get("标题", ""))
    exposure = metric_number(row, "曝光量")
    reads = metric_number(row, "阅读量")
    likes = metric_number(row, "点赞数")
    saves = metric_number(row, "收藏数")
    comments = metric_number(row, "评论数")
    shares = metric_number(row, "转发数")
    follows = metric_number(row, "关注数")
    dms = metric_number(row, "私信咨询数")
    interaction = likes + saves + comments + shares

    st.markdown(f"#### {title}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("曝光量", int(exposure))
    c2.metric("阅读量", int(reads), f"阅读率 {safe_rate(reads, exposure):.2%}")
    c3.metric("互动数", int(interaction), f"互动率 {safe_rate(interaction, reads):.2%}")
    c4.metric("私信咨询数", int(dms), f"咨询率 {safe_rate(dms, reads):.2%}")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("##### 互动构成")
        interaction_df = pd.DataFrame(
            {
                "指标": ["点赞", "收藏", "评论", "转发", "关注", "私信咨询"],
                "数量": [likes, saves, comments, shares, follows, dms],
            }
        ).set_index("指标")
        st.bar_chart(interaction_df, color="#8F5A39")

    with chart_right:
        st.markdown("##### 传播转化漏斗")
        funnel_df = pd.DataFrame(
            {
                "阶段": ["曝光", "阅读", "互动", "收藏", "私信咨询"],
                "数量": [exposure, reads, interaction, saves, dms],
            }
        ).set_index("阶段")
        st.bar_chart(funnel_df, color="#041E42")

    st.markdown("##### 效率指标")
    rate_df = pd.DataFrame(
        {
            "指标": ["阅读率", "互动率", "收藏率", "咨询率", "涨粉率"],
            "比例": [
                safe_rate(reads, exposure),
                safe_rate(interaction, reads),
                safe_rate(saves, reads),
                safe_rate(dms, reads),
                safe_rate(follows, reads),
            ],
        }
    ).set_index("指标")
    st.bar_chart(rate_df, color="#C8A878")

    review = review_metric_row(row)
    st.markdown("##### 自动复盘")
    st.write(f"诊断：{review['诊断']}")
    st.write(f"建议动作：{review['建议动作']}")
    st.write(f"封面类型：{row.get('封面类型', '') or '未填写'}")
    st.write(f"标题类型：{row.get('标题类型', '') or '未填写'}")
    st.write(f"选题方向：{row.get('选题方向', '') or '未填写'}")


def review_metric_row(row: pd.Series) -> dict[str, str | float]:
    exposure = float(row.get("曝光量", 0) or 0)
    reads = float(row.get("阅读量", 0) or 0)
    interaction_rate = float(row.get("互动率", 0) or 0)
    save_rate = float(row.get("收藏率", 0) or 0)
    inquiry_rate = float(row.get("咨询率", 0) or 0)

    if exposure <= 0 or reads <= 0:
        diagnosis = "还没有可判断数据"
        action = "发布后补齐曝光、阅读、互动和私信数据"
    elif safe_rate(reads, exposure) < 0.03:
        diagnosis = "封面或标题吸引力偏弱"
        action = "优先改封面标题，保留正文方向再测试"
    elif save_rate >= 0.08 and inquiry_rate < 0.01:
        diagnosis = "内容有收藏价值，但咨询动机不强"
        action = "做成系列，并在结尾补充温和的评估入口"
    elif inquiry_rate >= 0.01 or interaction_rate >= 0.12:
        diagnosis = "互动或咨询信号较强"
        action = "加入下周排期，同类主题继续做 2-3 篇"
    else:
        diagnosis = "表现中性，需要换角度再测"
        action = "调整用户场景或开头问题，不急着放大"

    return {
        "诊断": diagnosis,
        "建议动作": action,
    }


def build_review_df(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in metrics_df.iterrows():
        reviewed = review_metric_row(row)
        rows.append({**row.to_dict(), **reviewed})
    return pd.DataFrame(rows)


def render_content_production_tab(items: list, lang: str, export_only_passed: bool) -> None:
    if not items:
        render_empty_state(lang)
        return

    for item in items:
        item.visual_prompt = build_cover_visual_prompt(
            title=str(item.title),
            cover_copy=str(item.cover_copy),
            product_type=str(item.product_type),
            audience_type=str(item.audience_type),
            content_type=str(item.content_type),
        )

    st.markdown(f'<div class="panel-title">{escape(t(lang, "results"))}</div>', unsafe_allow_html=True)
    scores = [item.compliance_score for item in items]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t(lang, "metric_count"), len(items))
    c2.metric(t(lang, "metric_avg"), round(sum(scores) / len(scores), 1))
    c3.metric(t(lang, "metric_pass"), sum(1 for score in scores if score >= 80))
    c4.metric(t(lang, "metric_review"), sum(1 for score in scores if score < 90))

    export_path = OUTPUT_DIR / "content_calendar.xlsx"
    min_score = 80 if export_only_passed else None
    export_to_excel(items, export_path, min_score=min_score)

    st.download_button(
        t(lang, "download"),
        data=export_path.read_bytes(),
        file_name="content_calendar.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    tab_cards, tab_table = st.tabs([t(lang, "tab_cards"), t(lang, "tab_table")])
    with tab_cards:
        for item in items:
            render_card(item.__dict__, lang)
    with tab_table:
        df = pd.DataFrame([item.__dict__ for item in items])
        if lang == "en":
            df = df.rename(
                columns={
                    "index": "Index",
                    "content_type": "Content Type",
                    "audience_type": "Audience",
                    "product_type": "Product Direction",
                    "title": "Title",
                    "cover_copy": "Cover Copy",
                    "body": "Body",
                    "tags": "Tags",
                    "visual_prompt": "Visual Prompt",
                    "compliance_score": "Compliance Score",
                    "risk_level": "Risk Level",
                    "risk_issues": "Risk Issues",
                    "revised_version": "Revised Version",
                    "suggested_publish_time": "Suggested Publish Time",
                    "format": "Format",
                    "conversion_goal": "Conversion Goal",
                    "source": "Source",
                }
            )
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_publish_schedule_tab(items: list) -> None:
    records = items_as_records(items)
    titles = ["手动填写"] + [str(item.get("title", "")) for item in records]
    selected_title = st.selectbox("选择已通过合规的内容", titles, key="publish_template")
    selected_item = records[titles.index(selected_title) - 1] if selected_title != "手动填写" else {}

    with st.container(border=True):
        st.markdown("#### 发布排期 Skill")
        with st.form("publish_schedule_form"):
            title = st.text_input("标题", value=str(selected_item.get("title", "")))
            body = st.text_area("正文", value=str(selected_item.get("body", "")), height=120)
            cover_prompt = st.text_area(
                "封面 Prompt",
                value=str(selected_item.get("visual_prompt", "")),
                height=100,
            )
            c1, c2 = st.columns(2)
            publish_date = c1.date_input("发布时间日期", value=date.today())
            publish_time = c2.time_input("发布时间", value=time(19, 30))
            account = st.text_input("发布账号", value="昱丰保险")
            column = st.selectbox("内容栏目", ["保险科普", "避坑清单", "案例场景", "品牌观点", "评论区FAQ"])
            status = st.selectbox("状态", ["待发布", "已发布", "待修改", "暂缓"])
            xhs_link = st.text_input("小红书链接")
            remark = st.text_area("备注", height=80)
            submitted = st.form_submit_button("保存到发布日历", use_container_width=True)

        if submitted:
            append_local_csv(
                PUBLISH_CALENDAR_PATH,
                {
                    "标题": title,
                    "正文": body,
                    "封面 Prompt": cover_prompt,
                    "发布时间": f"{publish_date:%Y-%m-%d} {publish_time:%H:%M}",
                    "发布账号": account,
                    "内容栏目": column,
                    "目标人群": selected_item.get("audience_type", ""),
                    "状态": status,
                    "小红书链接": xhs_link,
                    "备注": remark,
                },
                PUBLISH_COLUMNS,
            )
            st.success(f"已保存到 {PUBLISH_CALENDAR_PATH}")

    st.markdown("#### 发布日历表格")
    st.dataframe(read_local_csv(PUBLISH_CALENDAR_PATH, PUBLISH_COLUMNS), use_container_width=True, hide_index=True)


def render_comment_reply_tab() -> None:
    with st.container(border=True):
        st.markdown("#### 评论私信回复 Skill")
        comment = st.text_area("评论/私信内容", placeholder="例如：香港保险收益是不是更高？", height=120)
        c1, c2 = st.columns(2)
        tone = c1.selectbox("回复语气", ["专业", "亲和", "简洁", "顾问式"])
        user_type = c2.selectbox("用户类型", ["小白用户", "高净值客户", "宝妈", "企业主"])
        if st.button("生成回复建议", use_container_width=True):
            if comment.strip():
                result = build_comment_replies(comment.strip(), tone, user_type)
                st.session_state["latest_comment_reply"] = result
                replies = st.session_state.get("comment_reply_notes", [])
                replies.append(result)
                st.session_state["comment_reply_notes"] = replies
            else:
                st.warning("请先粘贴一条评论或私信。")

    result = st.session_state.get("latest_comment_reply")
    if result:
        st.markdown("#### 回复建议")
        render_reply_card(result)


def render_analytics_tab() -> None:
    with st.container(border=True):
        st.markdown("#### 数据复盘优化 Skill")
        with st.form("analytics_form"):
            title = st.text_input("标题")
            publish_date = st.date_input("发布时间", value=date.today(), key="analytics_publish_date")
            c1, c2, c3 = st.columns(3)
            exposure = c1.number_input("曝光量", min_value=0, step=1)
            reads = c2.number_input("阅读量", min_value=0, step=1)
            likes = c3.number_input("点赞数", min_value=0, step=1)
            c4, c5, c6 = st.columns(3)
            saves = c4.number_input("收藏数", min_value=0, step=1)
            comments = c5.number_input("评论数", min_value=0, step=1)
            shares = c6.number_input("转发数", min_value=0, step=1)
            c7, c8 = st.columns(2)
            follows = c7.number_input("关注数", min_value=0, step=1)
            dms = c8.number_input("私信咨询数", min_value=0, step=1)
            cover_type = st.text_input("封面类型", placeholder="例如：清单型 / 对比型 / 问答型")
            title_type = st.text_input("标题类型", placeholder="例如：避坑型 / 提问型 / 场景型")
            topic_direction = st.text_input("选题方向", placeholder="例如：香港保险避坑")
            submitted = st.form_submit_button("保存数据复盘", use_container_width=True)

        if submitted:
            interaction = likes + saves + comments + shares
            row = {
                "标题": title,
                "发布时间": f"{publish_date:%Y-%m-%d}",
                "曝光量": int(exposure),
                "阅读量": int(reads),
                "点赞数": int(likes),
                "收藏数": int(saves),
                "评论数": int(comments),
                "转发数": int(shares),
                "关注数": int(follows),
                "私信咨询数": int(dms),
                "封面类型": cover_type,
                "标题类型": title_type,
                "选题方向": topic_direction,
                "阅读率": safe_rate(reads, exposure),
                "互动率": safe_rate(interaction, reads),
                "收藏率": safe_rate(saves, reads),
                "咨询率": safe_rate(dms, reads),
                "涨粉率": safe_rate(follows, reads),
            }
            append_local_csv(ANALYTICS_PATH, row, ANALYTICS_COLUMNS)
            st.success(f"已保存到 {ANALYTICS_PATH}")

    df = enrich_analytics_df(read_local_csv(ANALYTICS_PATH, ANALYTICS_COLUMNS))

    with st.container(border=True):
        st.markdown("#### 按小红书标题检索可视化")
        with st.form("analytics_title_search_form"):
            title_query_input = st.text_input("输入小红书标题关键词", placeholder="例如：买香港保险前，一定要问清楚")
            title_search_submitted = st.form_submit_button("检索并生成可视化", use_container_width=True)
        if title_search_submitted:
            st.session_state["analytics_title_query"] = title_query_input
        title_query = st.session_state.get("analytics_title_query", "")
        matches = find_title_matches(df, title_query)
        if title_query.strip() and matches.empty:
            st.warning("没有在本地复盘表中找到这个标题。请先把这篇笔记的数据保存到复盘表。")
        elif not matches.empty:
            selected_title = st.selectbox("选择匹配笔记", matches["标题"].astype(str).tolist())
            selected_row = matches[matches["标题"].astype(str) == selected_title].iloc[0]
            render_title_visualization(selected_row)

    st.markdown("#### 数据表格")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        review_df = build_review_df(df)
        st.markdown("#### 基础复盘结论")
        best_read = df.sort_values("阅读率", ascending=False).iloc[0]
        best_save = df.sort_values("收藏率", ascending=False).iloc[0]
        best_inquiry = df.sort_values("咨询率", ascending=False).iloc[0]
        st.write(f"本周阅读率较好的内容：{best_read['标题']}，阅读率 {best_read['阅读率']}")
        st.write(f"高收藏内容特征：{best_save['标题']}，收藏率 {best_save['收藏率']}，可继续做清单/避坑方向。")
        st.write(f"高咨询内容特征：{best_inquiry['标题']}，咨询率 {best_inquiry['咨询率']}，建议人工复核后放入下轮排期。")
        st.dataframe(review_df[["标题", "诊断", "建议动作"]], use_container_width=True, hide_index=True)


def render_feedback_kb_tab() -> None:
    ensure_storage_dirs()
    existing = FEEDBACK_KB_PATH.read_text(encoding="utf-8") if FEEDBACK_KB_PATH.exists() else ""
    with st.container(border=True):
        st.markdown("#### 反馈知识库 Skill")
        user_questions = st.text_area("用户真实问题", height=100)
        objections = st.text_area("高频异议", height=100)
        strong_topics = st.text_area("高表现选题", height=100)
        strong_titles = st.text_area("高转化标题", height=100)
        compliance_notes = st.text_area("合规风险提醒", height=100)
        if st.button("保存到反馈知识库", use_container_width=True):
            content = "\n".join(
                [
                    "# 反馈知识库",
                    "",
                    f"更新时间：{date.today():%Y-%m-%d}",
                    "",
                    "## 用户真实问题",
                    user_questions.strip() or "暂无",
                    "",
                    "## 高频异议",
                    objections.strip() or "暂无",
                    "",
                    "## 高表现选题",
                    strong_topics.strip() or "暂无",
                    "",
                    "## 高转化标题",
                    strong_titles.strip() or "暂无",
                    "",
                    "## 合规风险提醒",
                    compliance_notes.strip() or "暂无",
                    "",
                ]
            )
            FEEDBACK_KB_PATH.write_text(content, encoding="utf-8")
            st.success(f"已保存到 {FEEDBACK_KB_PATH}")

    if existing:
        with st.expander("查看当前 feedback_kb.md"):
            st.markdown(existing)


def render_sidebar(options: dict, config: dict) -> tuple[str, str, str, str, int, bool, bool]:
    with st.sidebar:
        lang_label = st.selectbox(t("zh", "language"), ["中文", "English"], index=0)
        lang = "en" if lang_label == "English" else "zh"

        st.markdown(
            f"""
            <div class="sidebar-brand">
                <h2>{escape(t(lang, "sidebar_title"))}</h2>
                <p>{escape(t(lang, "sidebar_desc"))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        load_dotenv()
        has_cloud_key = bool(os.getenv("DEEPSEEK_API_KEY"))
        st.caption(t(lang, "api_ready") if has_cloud_key else t(lang, "api_missing"))
        st.markdown(f"#### {t(lang, 'params')}")

        product_options = options.get("product_directions", ["香港保险", "IUL"])
        audience_options = options.get("audience_types", ["保险小白", "中产家庭"])
        content_options = options.get("content_types", ["小白科普", "避坑清单"])

        product_type = st.selectbox(
            t(lang, "product"),
            product_options,
            format_func=lambda value: display_label(value, lang),
        )
        audience_type = st.selectbox(
            t(lang, "audience"),
            audience_options,
            format_func=lambda value: display_label(value, lang),
        )
        content_type = st.selectbox(
            t(lang, "content_type"),
            content_options,
            format_func=lambda value: display_label(value, lang),
        )
        count = st.slider(
            t(lang, "count"),
            min_value=1,
            max_value=20,
            value=int(config.get("generation", {}).get("default_count", 5)),
        )
        export_only_passed = st.toggle(t(lang, "export_passed"), value=True)
        st.markdown("---")
        generate = st.button(t(lang, "generate"), type="primary", use_container_width=True)
    return lang, product_type, audience_type, content_type, count, export_only_passed, generate


def main() -> None:
    inject_style()
    ensure_storage_dirs()
    config = load_config()
    options = config.get("options", {})

    lang, product_type, audience_type, content_type, count, export_only_passed, generate = render_sidebar(options, config)

    render_hero(lang)

    if "items" not in st.session_state:
        st.session_state["items"] = []

    if generate:
        st.session_state["items"] = generate_content_batch(
            product_type=product_type,
            audience_type=audience_type,
            content_type=content_type,
            count=count,
        )

    items = st.session_state["items"]

    tab_content, tab_publish, tab_reply, tab_analytics, tab_feedback = st.tabs(
        ["内容生产", "发布排期", "评论私信", "数据复盘", "反馈知识库"]
    )
    with tab_content:
        render_content_production_tab(items, lang, export_only_passed)
    with tab_publish:
        render_publish_schedule_tab(items)
    with tab_reply:
        render_comment_reply_tab()
    with tab_analytics:
        render_analytics_tab()
    with tab_feedback:
        render_feedback_kb_tab()


if __name__ == "__main__":
    main()
