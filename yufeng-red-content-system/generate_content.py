from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import json
import os
import re
import urllib.error
import urllib.request

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parent
KB_DIR = ROOT / "knowledge_base"
PROMPT_DIR = ROOT / "prompts"
OUTPUT_DIR = ROOT / "output"


@dataclass
class ContentItem:
    index: int
    content_type: str
    audience_type: str
    product_type: str
    title: str
    cover_copy: str
    body: str
    tags: str
    visual_prompt: str
    compliance_score: int
    risk_level: str
    risk_issues: str
    revised_version: str
    suggested_publish_time: str
    format: str
    conversion_goal: str
    source: str = "Local fallback"


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for sub in ["notes", "visual_prompts", "compliance_reports"]:
        (OUTPUT_DIR / sub).mkdir(parents=True, exist_ok=True)


def load_dotenv() -> None:
    for env_path in (ROOT / ".env", ROOT / "DEEPSEEK_API_KEY.env", ROOT / "OPENAI_API_KEY.env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def load_config() -> dict[str, Any]:
    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        return {}
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_knowledge_base() -> dict[str, str]:
    return {
        "brand_profile": read_text(KB_DIR / "brand_profile.md"),
        "product_iul": read_text(KB_DIR / "product_iul.md"),
        "product_hongkong_insurance": read_text(KB_DIR / "product_hongkong_insurance.md"),
        "compliance_rules": read_text(KB_DIR / "compliance_rules.md"),
        "xiaohongshu_style": read_text(KB_DIR / "xiaohongshu_style.md"),
        "target_audience": read_text(KB_DIR / "target_audience.md"),
        "topic_prompt": read_text(PROMPT_DIR / "01_topic_generator.md"),
        "note_prompt": read_text(PROMPT_DIR / "02_note_writer.md"),
        "visual_prompt": read_text(PROMPT_DIR / "03_visual_prompt.md"),
        "compliance_prompt": read_text(PROMPT_DIR / "04_compliance_review.md"),
    }


def suggested_publish_time(index: int) -> str:
    return (date.today() + timedelta(days=index)).strftime("%Y-%m-%d")


def normalize_risk(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"低", "low", "low risk"}:
        return "低"
    if text in {"中", "medium", "moderate", "medium risk"}:
        return "中"
    if text in {"高", "high", "high risk"}:
        return "高"
    return "低"


def parse_tags(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def parse_int(value: Any, default: int = 85) -> int:
    try:
        number = int(float(str(value).strip()))
    except (TypeError, ValueError):
        number = default
    return max(0, min(100, number))


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def cloud_generation_enabled(config: dict[str, Any]) -> bool:
    generation = config.get("generation", {})
    return bool(generation.get("use_deepseek", generation.get("use_openai", True)))


def call_deepseek_chat_json(prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured.")

    generation = config.get("generation", {})
    model = generation.get("model", "deepseek-v4-flash")
    base_url = str(generation.get("base_url", "https://api.deepseek.com")).rstrip("/")
    temperature = float(generation.get("temperature", 0.7))
    timeout = int(generation.get("timeout_seconds", 90))

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional Xiaohongshu content system for YFG Prestige and Yu Fung Broker. "
                    "Return strict JSON only. Avoid misleading insurance sales claims, return promises, "
                    "fear marketing, and unlicensed transaction language."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"DeepSeek API returned HTTP {exc.code}: {detail}") from exc

    content = data["choices"][0]["message"]["content"]
    return extract_json_object(content)


def build_generation_prompt(
    product_type: str,
    audience_type: str,
    content_type: str,
    count: int,
    kb: dict[str, str],
) -> str:
    return f"""
请基于以下昱豐保險 / YFG Prestige 知识库，生成 {count} 条小红书内容结果。

品牌资料：
{kb.get("brand_profile", "")}

产品资料 IUL：
{kb.get("product_iul", "")}

产品资料 香港保险：
{kb.get("product_hongkong_insurance", "")}

目标人群：
{kb.get("target_audience", "")}

小红书风格：
{kb.get("xiaohongshu_style", "")}

合规规则：
{kb.get("compliance_rules", "")}

用户选择：
- 产品方向：{product_type}
- 目标人群：{audience_type}
- 内容类型：{content_type}
- 生成数量：{count}

输出要求：
1. 必须生成适合小红书的真实内容，不要只给模板。
2. 每条内容包含标题、封面文案、正文、标签、视觉 Prompt、合规审查结果、修改后版本、推荐形式、转化目标。
3. visual_prompt 只写一条精简的封面海报 Prompt，不要堆砌复杂元素，不要重复说明。
4. visual_prompt 的结构固定为：文案排版 + 海报背景。图片主体必须是 cover_copy 对应的文字排版，背景只做品牌调性和主题氛围辅助。
5. 图片上的主标题优先使用 cover_copy 的第一行，副标题使用 cover_copy 的第二行；如果 cover_copy 不清晰，则使用 title。不要生成只有背景、没有标题文字的图片 Prompt。
6. 不承诺收益，不使用“稳赚、保本高收益、无风险、闭眼买、适合所有人、财富自由”等表达。
7. 涉及 IUL、投资相连、香港保险、跨境服务时，需要补充费用、流动性、条款、风险和个人情况评估提示。
8. 正文用中文输出，语言要适合小红书，但保持金融保险品牌的专业、克制、可信。

请只返回严格 JSON，结构如下：
{{
  "items": [
    {{
      "content_type": "{content_type}",
      "audience_type": "{audience_type}",
      "product_type": "{product_type}",
      "title": "小红书标题",
      "cover_copy": "封面主副文案，可以换行",
      "body": "完整正文",
      "tags": ["#香港保险", "#保险科普"],
      "visual_prompt": "封面海报 Prompt，格式为：3:4竖版海报。画面文字：主标题...，副标题...。排版：...。背景：...。风格：...。避免：...",
      "compliance_score": 88,
      "risk_level": "低",
      "risk_issues": "发现的问题与修改建议",
      "revised_version": "合规修改后正文",
      "format": "图文笔记",
      "conversion_goal": "收藏"
    }}
  ]
}}
"""


TOPIC_POOLS = {
    "小白科普": [
        "{product}到底适合什么人？小白先看懂这几点",
        "第一次了解{product}，先别急着问收益",
        "{product}不是神话，真正要看懂的是这些",
        "看懂{product}前，先问自己这3个问题",
        "{product}和家庭保障有什么关系？",
    ],
    "避坑清单": [
        "买{product}前，一定要看懂这5个问题",
        "别只看演示收益，{product}还要看这些",
        "{product}适合所有人吗？这篇说点实在的",
        "第一次看{product}方案，最容易忽略什么？",
        "{product}常见误区：不要只听一个数字",
    ],
    "情绪共鸣": [
        "成年人的安全感，很多时候来自提前规划",
        "有了孩子以后，我才真正理解保障的意义",
        "家庭收入稳定，为什么还是会担心未来？",
        "为什么30岁以后，越来越不敢让家庭裸奔？",
        "给家人的安全感，不一定从产品开始",
    ],
    "案例场景": [
        "一个三口之家，如何做基础保障规划？",
        "企业主家庭，为什么要重视保单架构？",
        "给孩子做教育金规划，真正要看的不是收益率",
        "家庭收入主要靠一个人，保障应该先看哪里？",
        "企业主最容易忽略的风险，是公司和家庭边界不清",
    ],
    "品牌专业观点": [
        "专业保险顾问不会一上来就推荐产品",
        "一份保险方案，真正重要的是匹配家庭需求",
        "保险经纪的价值，不只是卖产品",
        "为什么保险方案不能只看收益演示？",
        "昱豐保险如何帮助客户看懂复杂条款？",
    ],
    "评论区FAQ": [
        "香港保险靠谱吗？可以先从这3点看",
        "IUL收益多少？为什么不能只用一个数字回答",
        "普通家庭适合了解香港保险吗？",
        "怎么买香港保险？先了解正规流程",
        "保险是不是智商税？关键看适不适合",
    ],
}


def recommend_format(content_type: str) -> str:
    return {
        "小白科普": "图文笔记",
        "避坑清单": "长图/轮播",
        "情绪共鸣": "图文笔记",
        "案例场景": "场景案例",
        "品牌专业观点": "品牌观点",
        "评论区FAQ": "问答笔记",
    }.get(content_type, "图文笔记")


def recommend_goal(content_type: str) -> str:
    return {
        "小白科普": "建立认知",
        "避坑清单": "收藏+转发",
        "情绪共鸣": "评论互动",
        "案例场景": "私信咨询",
        "品牌专业观点": "建立信任",
        "评论区FAQ": "降低疑虑",
    }.get(content_type, "收藏")


def build_local_body(product_type: str, audience_type: str) -> str:
    return "\n".join(
        [
            f"很多人第一次了解{product_type}，会先问收益、价格或别人买不买。",
            "",
            "但保险规划更建议先看这几个问题：",
            "1. 你的家庭阶段、保障缺口和现金流是否清晰？",
            "2. 产品条款、费用结构、流动性和长期持有条件是否看懂？",
            "3. 它是否匹配你的预算、目标和风险承受能力？",
            "",
            f"对于{audience_type}来说，真正重要的不是“别人适不适合”，而是方案是否匹配自己的家庭情况。",
            "",
            "提示：具体保障、费用、现金价值、退保影响及适合人群，应以保险公司正式条款及个人情况评估为准。",
        ]
    )


def compliance_review(text: str, product_type: str) -> dict[str, Any]:
    banned = ["稳赚", "保本高收益", "一定回报", "无风险", "闭眼买", "适合所有人", "财富自由", "保证收益"]
    issues = []
    score = 94
    for word in banned:
        if word in text:
            issues.append(f"出现高风险表达“{word}”，建议删除或改为条件性表述。")
            score -= 12
    if product_type in {"IUL", "财富传承", "信托与CRS"} and "条款" not in text:
        issues.append("涉及复杂产品或跨境规划，建议补充正式文件、费用和风险提示。")
        score -= 8
    risk_level = "低" if score >= 85 else "中" if score >= 70 else "高"
    return {
        "score": max(score, 0),
        "risk_level": risk_level,
        "issues": "；".join(issues) if issues else "未发现明显高风险表达，发布前仍建议人工复核。",
    }


def split_cover_copy(cover_copy: str, title: str) -> tuple[str, str]:
    lines = [line.strip() for line in str(cover_copy or "").splitlines() if line.strip()]
    if not lines:
        return title.strip(), "先看懂逻辑，再做适合自己的规划"
    main_title = lines[0]
    subtitle = " / ".join(lines[1:]) if len(lines) > 1 else title.strip()
    return main_title, subtitle


def poster_background_direction(product_type: str, content_type: str) -> str:
    by_content = {
        "小白科普": "米白渐变背景，淡化的香港天际线和一张简洁信息卡片轮廓",
        "避坑清单": "米白背景，浅金分隔线，低透明度的保单文件和核对清单轮廓",
        "情绪共鸣": "柔和米白背景，低饱和家庭生活剪影，浅金光线点缀",
        "案例场景": "现代商务会客室或书桌文件场景虚化背景，稳重克制",
        "品牌专业观点": "高级金融办公室背景，深蓝细线网格和浅金品牌线条",
        "评论区FAQ": "米白背景，简洁问答卡片和浅金对话框轮廓",
    }
    if product_type == "IUL":
        return "米白背景，低透明度保单文件、现金价值曲线和细线图表，避免收益暗示"
    return by_content.get(content_type, "米白背景，淡化香港城市线条和专业金融文件轮廓")


def build_cover_visual_prompt(
    title: str,
    cover_copy: str,
    product_type: str,
    audience_type: str,
    content_type: str,
    base_prompt: str = "",
) -> str:
    main_title, subtitle = split_cover_copy(cover_copy, title)
    background = poster_background_direction(product_type, content_type)
    return (
        "3:4竖版小红书封面海报。"
        f"画面文字：主标题“{main_title}”，副标题“{subtitle}”，底部小字“YFG Prestige · 昱豐保險”。"
        "排版：以文字为主视觉，主标题置于上半区偏左，2行大字，深蓝色；副标题紧跟其下，较小字号，浅金强调；底部品牌小字低调留白。"
        f"背景：{background}，只作为氛围辅助，不抢文字。"
        "风格：高级金融感、克制专业、米白底、深蓝字、浅金线条、干净留白，中文清晰可读。"
        "避免：元素堆砌、复杂插画、文字被遮挡、现金堆、暴富符号、夸张上涨箭头、收益承诺、无风险表达。"
    )


def generate_local_batch(product_type: str, audience_type: str, content_type: str, count: int) -> list[ContentItem]:
    pool = TOPIC_POOLS.get(content_type, TOPIC_POOLS["小白科普"])
    items: list[ContentItem] = []
    for index in range(1, count + 1):
        title = pool[(index - 1) % len(pool)].format(product=product_type)
        cover_copy = "别只问收益\n先看懂底层逻辑" if product_type == "IUL" else f"{product_type}\n小白先看懂这几点"
        body = build_local_body(product_type, audience_type)
        tags = "#香港保险 #保险科普 #家庭保障 #财富规划 #昱豐保险"
        visual_prompt = build_cover_visual_prompt(title, cover_copy, product_type, audience_type, content_type)
        review = compliance_review("\n".join([title, cover_copy, body, tags]), product_type)
        items.append(
            ContentItem(
                index=index,
                content_type=content_type,
                audience_type=audience_type,
                product_type=product_type,
                title=title,
                cover_copy=cover_copy,
                body=body,
                tags=tags,
                visual_prompt=visual_prompt,
                compliance_score=review["score"],
                risk_level=review["risk_level"],
                risk_issues=review["issues"],
                revised_version=body,
                suggested_publish_time=suggested_publish_time(index),
                format=recommend_format(content_type),
                conversion_goal=recommend_goal(content_type),
                source="Local fallback",
            )
        )
    return items


def item_from_ai(raw: dict[str, Any], index: int, product_type: str, audience_type: str, content_type: str) -> ContentItem:
    title = str(raw.get("title") or f"{product_type}小红书选题")
    cover_copy = str(raw.get("cover_copy") or "")
    visual_prompt = build_cover_visual_prompt(
        title=title,
        cover_copy=cover_copy,
        product_type=str(raw.get("product_type") or product_type),
        audience_type=str(raw.get("audience_type") or audience_type),
        content_type=str(raw.get("content_type") or content_type),
        base_prompt=str(raw.get("visual_prompt") or ""),
    )
    return ContentItem(
        index=index,
        content_type=str(raw.get("content_type") or content_type),
        audience_type=str(raw.get("audience_type") or audience_type),
        product_type=str(raw.get("product_type") or product_type),
        title=title,
        cover_copy=cover_copy,
        body=str(raw.get("body") or ""),
        tags=parse_tags(raw.get("tags")),
        visual_prompt=visual_prompt,
        compliance_score=parse_int(raw.get("compliance_score"), 85),
        risk_level=normalize_risk(raw.get("risk_level")),
        risk_issues=str(raw.get("risk_issues") or "DeepSeek 已返回初步合规意见，发布前建议人工复核。"),
        revised_version=str(raw.get("revised_version") or raw.get("body") or ""),
        suggested_publish_time=suggested_publish_time(index),
        format=str(raw.get("format") or recommend_format(content_type)),
        conversion_goal=str(raw.get("conversion_goal") or recommend_goal(content_type)),
        source="DeepSeek Cloud",
    )


def generate_deepseek_batch(product_type: str, audience_type: str, content_type: str, count: int) -> list[ContentItem]:
    config = load_config()
    kb = load_knowledge_base()
    prompt = build_generation_prompt(product_type, audience_type, content_type, count, kb)
    data = call_deepseek_chat_json(prompt, config)
    raw_items = data.get("items", [])
    if not isinstance(raw_items, list) or not raw_items:
        raise RuntimeError("DeepSeek response did not include a non-empty items list.")
    return [
        item_from_ai(raw if isinstance(raw, dict) else {}, index, product_type, audience_type, content_type)
        for index, raw in enumerate(raw_items[:count], start=1)
    ]


def fallback_source_from_error(exc: Exception) -> str:
    message = str(exc)
    if "insufficient_quota" in message or "exceeded your current quota" in message:
        return "Local fallback (DeepSeek quota exceeded)"
    if "invalid_api_key" in message or "Incorrect API key" in message:
        return "Local fallback (invalid API key)"
    if "DEEPSEEK_API_KEY is not configured" in message:
        return "Local fallback (DeepSeek API key missing)"
    if "rate_limit" in message or "HTTP 429" in message:
        return "Local fallback (DeepSeek rate limited)"
    return "Local fallback (DeepSeek request failed)"


def generate_content_batch(
    product_type: str,
    audience_type: str,
    content_type: str,
    count: int,
) -> list[ContentItem]:
    ensure_output_dirs()
    config = load_config()
    if cloud_generation_enabled(config):
        try:
            return generate_deepseek_batch(product_type, audience_type, content_type, count)
        except Exception as exc:
            fallback_items = generate_local_batch(product_type, audience_type, content_type, count)
            fallback_source = fallback_source_from_error(exc)
            for item in fallback_items:
                item.source = fallback_source
            return fallback_items
    return generate_local_batch(product_type, audience_type, content_type, count)


def export_to_excel(items: list[ContentItem], path: Path, min_score: int | None = None) -> Path:
    ensure_output_dirs()
    rows = [asdict(item) for item in items if min_score is None or item.compliance_score >= min_score]
    df = pd.DataFrame(rows)
    rename_map = {
        "index": "序号",
        "content_type": "内容类型",
        "audience_type": "目标人群",
        "product_type": "产品方向",
        "title": "小红书标题",
        "cover_copy": "封面文案",
        "body": "正文",
        "tags": "标签",
        "visual_prompt": "封面图 Prompt",
        "compliance_score": "合规评分",
        "risk_level": "风险等级",
        "risk_issues": "风险问题",
        "revised_version": "修改后版本",
        "suggested_publish_time": "建议发布时间",
        "format": "推荐形式",
        "conversion_goal": "转化目标",
        "source": "生成来源",
    }
    df = df.rename(columns=rename_map)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="content")
        worksheet = writer.sheets["content"]
        for col in worksheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            worksheet.column_dimensions[col[0].column_letter].width = min(max(max_length + 2, 12), 48)
    return path


def items_to_dataframe(items: list[ContentItem]) -> pd.DataFrame:
    return pd.DataFrame([asdict(item) for item in items])


if __name__ == "__main__":
    demo_items = generate_content_batch("IUL", "保险小白", "小白科普", 3)
    out = export_to_excel(demo_items, OUTPUT_DIR / "content_calendar.xlsx")
    print(f"Generated {len(demo_items)} items: {out}")
