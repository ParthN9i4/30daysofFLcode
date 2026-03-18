from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, BeforeValidator
from typing import Annotated, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timezone
import os, httpx, feedparser, asyncio, re, uuid
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

app = FastAPI(title="Blog Ideation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
REPO_PATH = os.environ.get("REPO_PATH", "/app")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ── Pydantic helpers ─────────────────────────────────────────────────────────

PyObjectId = Annotated[str, BeforeValidator(str)]


class BaseDocument(BaseModel):
    id: Optional[PyObjectId] = None

    class Config:
        populate_by_name = True

    @classmethod
    def from_mongo(cls, doc):
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return cls(**doc)

    def to_mongo(self):
        d = self.model_dump(exclude={"id"})
        return d


# ── Models ────────────────────────────────────────────────────────────────────

class BlogDraft(BaseDocument):
    title: str
    content: str
    mode: str  # "ideas" | "outline" | "draft"
    source_ids: List[str] = []
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IdeationRequest(BaseModel):
    source_texts: List[str]
    source_titles: List[str]
    mode: str  # "ideas" | "outline" | "draft"
    custom_angle: Optional[str] = None


class SaveDraftRequest(BaseModel):
    title: str
    content: str
    mode: str
    source_ids: List[str] = []
    tags: List[str] = []


class UpdateDraftRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


# ── Repo Parser ───────────────────────────────────────────────────────────────

TOPIC_TAGS = {
    "fhe": ["fhe", "homomorphic", "tenseal", "concrete", "encrypted", "ckks", "bfv"],
    "fl": ["federated", "flower", "pysyft", "opacus", "fedrag", "flwr"],
    "vit": ["vit", "vision transformer", "attention", "transformer"],
    "kd": ["knowledge distillation", "distillation", "teacher", "student"],
    "ppml": ["privacy", "ppml", "pet", "differential privacy", "secure", "mpc", "crypten"],
    "gnn": ["gnn", "graph neural", "graph network"],
    "rag": ["rag", "retrieval", "fedrag"],
}


def infer_tags(text: str) -> List[str]:
    text_lower = text.lower()
    tags = []
    for tag, keywords in TOPIC_TAGS.items():
        if any(k in text_lower for k in keywords):
            tags.append(tag)
    return tags or ["ppml"]


def parse_repo_sources():
    sources = []
    day_pattern = re.compile(r"^Day (\d+) - (.+)$")
    
    try:
        entries = sorted(os.listdir(REPO_PATH))
    except Exception:
        return sources

    for entry in entries:
        match = day_pattern.match(entry)
        if not match:
            continue
        day_num = int(match.group(1))
        day_title = match.group(2).strip()
        folder = os.path.join(REPO_PATH, entry)
        if not os.path.isdir(folder):
            continue

        content_parts = []
        links = []

        for fname in ["progress.md", "README.md", "progress.d"]:
            fpath = os.path.join(folder, fname)
            if os.path.exists(fpath):
                try:
                    text = open(fpath).read().strip()
                    if text:
                        content_parts.append(text)
                        # extract URLs
                        found = re.findall(r"https?://[^\s\)]+", text)
                        links.extend(found)
                except Exception:
                    pass

        # list any PDFs
        pdfs = [f for f in os.listdir(folder) if f.endswith(".pdf")]

        # strip markdown header symbols for clean display
        def strip_md(text):
            text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            return text.strip()

        summary = strip_md("\n\n".join(content_parts)) if content_parts else f"Study session: {day_title}"
        tags = infer_tags(summary + " " + day_title)

        sources.append({
            "id": f"repo-day-{day_num}",
            "type": "repo",
            "day": day_num,
            "title": f"Day {day_num}: {day_title}",
            "summary": summary[:800],
            "links": links[:5],
            "pdfs": pdfs,
            "tags": tags,
            "date": None,
        })

    return sources


# ── ArXiv Fetcher ─────────────────────────────────────────────────────────────

ARXIV_QUERIES = [
    "homomorphic encryption machine learning",
    "federated learning privacy preserving neural network",
    "fully homomorphic encryption deep learning",
]

_arxiv_cache = []
_arxiv_fetched_at = None


async def fetch_arxiv_papers():
    global _arxiv_cache, _arxiv_fetched_at
    now = datetime.now(timezone.utc)
    if _arxiv_fetched_at and (now - _arxiv_fetched_at).seconds < 3600 and _arxiv_cache:
        return _arxiv_cache

    papers = []
    base_url = "https://export.arxiv.org/api/query"
    seen_ids = set()

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as http_client:
        for query in ARXIV_QUERIES[:3]:
            try:
                params = {
                    "search_query": f"all:{query}",
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "max_results": 5,
                }
                resp = await http_client.get(base_url, params=params)
                if resp.status_code != 200:
                    continue
                content = resp.text
                # parse XML entries
                entries = re.findall(r"<entry>(.*?)</entry>", content, re.DOTALL)
                for entry in entries:
                    arxiv_id_m = re.search(r"<id>(.*?)</id>", entry)
                    title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                    summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                    published_m = re.search(r"<published>(.*?)</published>", entry)

                    if not arxiv_id_m or not title_m:
                        continue
                    arxiv_id = arxiv_id_m.group(1).strip()
                    if arxiv_id in seen_ids:
                        continue
                    seen_ids.add(arxiv_id)

                    title = re.sub(r"\s+", " ", title_m.group(1)).strip()
                    summary = re.sub(r"\s+", " ", summary_m.group(1)).strip() if summary_m else ""
                    published = published_m.group(1).strip() if published_m else ""
                    tags = infer_tags(title + " " + summary)

                    papers.append({
                        "id": f"arxiv-{arxiv_id.split('/')[-1]}",
                        "type": "arxiv",
                        "title": title,
                        "summary": summary[:600],
                        "url": arxiv_id,
                        "published": published,
                        "tags": tags,
                    })
            except Exception as e:
                print(f"ArXiv fetch error for '{query}': {e}", flush=True)
                continue

    _arxiv_cache = papers
    _arxiv_fetched_at = now
    return papers


# ── RSS Fetcher ───────────────────────────────────────────────────────────────

RSS_FEEDS = [
    ("https://huggingface.co/blog/feed.xml", "HuggingFace Blog"),
    ("https://feeds.feedburner.com/blogspot/gJZg", "Google AI Blog"),
]

_rss_cache = []
_rss_fetched_at = None


async def fetch_rss_items():
    global _rss_cache, _rss_fetched_at
    now = datetime.now(timezone.utc)
    if _rss_fetched_at and (now - _rss_fetched_at).seconds < 3600 and _rss_cache:
        return _rss_cache

    items = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as http:
        for url, source_name in RSS_FEEDS:
            try:
                resp = await http.get(url, follow_redirects=True)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:5]:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    link = getattr(entry, "link", "")
                    published = getattr(entry, "published", "")
                    tags = infer_tags(title + " " + summary)
                    items.append({
                        "id": f"rss-{hash(link) % 999999}",
                        "type": "rss",
                        "source_name": source_name,
                        "title": title,
                        "summary": re.sub(r"<[^>]+>", "", summary)[:400],
                        "url": link,
                        "published": published,
                        "tags": tags,
                    })
            except Exception as e:
                print(f"RSS fetch error: {e}")

    _rss_cache = items
    _rss_fetched_at = now
    return items


# ── Claude Ideation ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert academic blog writer specializing in Privacy-Preserving Machine Learning, 
Fully Homomorphic Encryption (FHE), Federated Learning, Vision Transformers (ViTs), and Knowledge Distillation (KD). 
Your role is to help researchers transform dense technical notes and papers into engaging, accessible academic blog posts.
Be concise, insightful, and technically accurate. Use markdown formatting."""

MODE_PROMPTS = {
    "ideas": """Based on the following research notes/papers, generate 5 distinct, creative blog post ideas.
For each idea provide:
- **Title**: A compelling, SEO-friendly title
- **Angle**: The unique perspective or insight (1-2 sentences)  
- **Target Audience**: Who should read this
- **Hook**: An engaging opening line

Be specific to the technical content. Avoid generic titles.

Research content:
{content}

{angle}""",

    "outline": """Based on the following research content, create a detailed blog post outline.
Structure it as:
- **Working Title**
- **Abstract** (2-3 sentences)
- **Introduction** (key hook + why this matters)
- **Section 1**: [Title + 3-4 bullet points]
- **Section 2**: [Title + 3-4 bullet points]  
- **Section 3**: [Title + 3-4 bullet points]
- **Conclusion**: Key takeaways
- **Further Reading**: 2-3 resource suggestions

Research content:
{content}

{angle}""",

    "draft": """Based on the following research content, write a complete academic blog post (~800-1000 words).
Requirements:
- Engaging introduction that hooks both technical and semi-technical readers
- Clear explanations with analogies for complex concepts
- Technical depth without losing accessibility
- Concrete examples or use cases
- Strong conclusion with implications

Use proper markdown formatting with headers, bold, and code blocks where appropriate.

Research content:
{content}

{angle}""",
}


async def generate_blog_content(source_texts: List[str], source_titles: List[str], mode: str, custom_angle: str = "") -> str:
    combined = "\n\n---\n\n".join(
        [f"**{t}**\n{s}" for t, s in zip(source_titles, source_texts)]
    )
    # truncate to keep tokens low
    combined = combined[:3000]
    
    angle_text = f"\nFocus angle: {custom_angle}" if custom_angle else ""
    prompt = MODE_PROMPTS[mode].format(content=combined, angle=angle_text)

    session_id = str(uuid.uuid4())
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=SYSTEM_PROMPT,
    ).with_model("anthropic", "claude-haiku-4-5-20251001")

    response = await chat.send_message(UserMessage(text=prompt))
    return response


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/sources/repo")
async def get_repo_sources():
    sources = parse_repo_sources()
    return {"sources": sources, "count": len(sources)}


@app.get("/api/sources/arxiv")
async def get_arxiv_sources():
    papers = await fetch_arxiv_papers()
    return {"sources": papers, "count": len(papers)}


@app.get("/api/sources/rss")
async def get_rss_sources():
    items = await fetch_rss_items()
    return {"sources": items, "count": len(items)}


@app.get("/api/sources/all")
async def get_all_sources():
    repo, arxiv, rss = await asyncio.gather(
        asyncio.to_thread(parse_repo_sources),
        fetch_arxiv_papers(),
        fetch_rss_items(),
    )
    all_sources = repo + arxiv + rss
    return {"sources": all_sources, "total": len(all_sources)}


@app.post("/api/ideate")
async def ideate(req: IdeationRequest):
    if not req.source_texts:
        raise HTTPException(400, "No source texts provided")
    if req.mode not in ("ideas", "outline", "draft"):
        raise HTTPException(400, "mode must be ideas, outline, or draft")

    result = await generate_blog_content(
        req.source_texts, req.source_titles, req.mode, req.custom_angle or ""
    )
    return {"content": result, "mode": req.mode}


@app.post("/api/drafts")
async def save_draft(req: SaveDraftRequest):
    doc = {
        "title": req.title,
        "content": req.content,
        "mode": req.mode,
        "source_ids": req.source_ids,
        "tags": req.tags,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await db.drafts.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Draft saved"}


@app.get("/api/drafts")
async def list_drafts():
    cursor = db.drafts.find().sort("created_at", -1).limit(50)
    drafts = []
    async for doc in cursor:
        drafts.append(BlogDraft.from_mongo(doc).model_dump())
    return {"drafts": drafts}


@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: str):
    doc = await db.drafts.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(404, "Draft not found")
    return BlogDraft.from_mongo(doc).model_dump()


@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: str, req: UpdateDraftRequest):
    update = {"updated_at": datetime.now(timezone.utc)}
    if req.title is not None:
        update["title"] = req.title
    if req.content is not None:
        update["content"] = req.content
    if req.tags is not None:
        update["tags"] = req.tags
    result = await db.drafts.update_one({"_id": ObjectId(draft_id)}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "Draft not found")
    return {"message": "Updated"}


@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    result = await db.drafts.delete_one({"_id": ObjectId(draft_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Draft not found")
    return {"message": "Deleted"}
