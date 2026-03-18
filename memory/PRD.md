# PRD: The Cipher Dispatch — Academic Blog Ideation Tool

**Author**: Parth Nagar  
**Date Created**: March 2026  
**Status**: MVP Complete  

---

## Problem Statement
Help a Privacy-Preserving ML researcher (FHE, Federated Learning, ViTs, KD) transform daily study notes and academic papers into thoughtful, accessible academic blog posts using AI-assisted ideation.

## Architecture

**Stack**: React + FastAPI + MongoDB  
**AI**: Claude Haiku 4.5 (claude-haiku-4-5-20251001) via Emergent LLM Key  
**Source Ingestion**:  
- Local repo: `/app/Day X - ...` folders (markdown notes)  
- arXiv API (HTTPS, free, no key needed)  
- RSS feeds (HuggingFace Blog, Google AI Blog)  

**Key Files**:
- Backend: `/app/backend/server.py`
- Frontend: `/app/frontend/src/`
  - `App.js` - Main layout + navigation state
  - `components/Dashboard.js` - Source feed
  - `components/IdeationStudio.js` - Blog generation
  - `components/SavedDrafts.js` - Draft library
  - `components/Sidebar.js` - Navigation
  - `components/TagPill.js` - Reusable tag component

---

## Core Requirements (Static)

1. Ingest repo daily notes (30 Day folders)
2. Fetch arXiv papers on FHE/FL/privacy ML
3. Fetch RSS feeds from ML blogs
4. Generate: Blog Ideas (5 ideas), Blog Outline, Full Draft
5. Save, edit, delete drafts
6. Topic tagging: FHE, FL, ViT, KD, PPML, GNN, RAG
7. Credit-frugal design (Claude Haiku, content caching)

---

## User Personas

- **Primary**: Parth Nagar — PhD researcher, 30 Days of FL Code author
- **Secondary**: ML researchers and engineers in PPML/FHE who want to blog about their work

---

## What's Been Implemented (MVP - March 2026)

### Backend APIs
- `GET /api/sources/repo` — Parse all 30 Day folders from repo (30 sources)
- `GET /api/sources/arxiv` — Fetch latest arXiv papers (cached 1h)
- `GET /api/sources/rss` — Fetch HuggingFace + Google AI blog feeds (cached 1h)
- `GET /api/sources/all` — Combined feed (repo + arxiv + rss)
- `POST /api/ideate` — Claude Haiku generation (ideas/outline/draft modes)
- `POST /api/drafts` — Save draft
- `GET /api/drafts` — List all drafts
- `GET /api/drafts/{id}` — Get single draft
- `PUT /api/drafts/{id}` — Update draft
- `DELETE /api/drafts/{id}` — Delete draft

### Frontend Features
- Dark Academia design ("The Cipher Dispatch") — dark obsidian theme, electric violet/neon-cyan accents
- Source Feed with type + topic filters
- Stats bar (total/repo/arxiv/rss counts)
- Ideation Studio: mode selector, source picker, custom angle, generate button
- Generated output with ReactMarkdown rendering
- Save to library, copy to clipboard
- Saved Drafts: card grid, view modal, inline edit, delete
- Sidebar navigation
- Loading skeletons, sonner toasts, smooth animations

### Testing Results
- Backend: 100% (all APIs tested)
- Frontend: 100% (all user flows tested)

---

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Better arXiv search queries — more targeted to FHE + ViT + KD
- [ ] PDF parsing for repo PDFs (SortingHat.pdf, FedJAX.pdf, FHEFL.pdf)
- [ ] Show raw markdown notes content more cleanly

### P1 (Important)
- [ ] Twitter/X thread ingestion for real-time research discussions
- [ ] Semantic Scholar API integration for citation-rich papers
- [ ] Tag-based smart source pre-selection in Ideation Studio
- [ ] Export draft as Markdown file download
- [ ] Blog length/tone controls (beginner-friendly vs expert)

### P2 (Future)
- [ ] Medium/Substack integration to publish directly
- [ ] Topic trend analysis (which FHE topics are gaining momentum)
- [ ] Multi-draft comparison view
- [ ] User auth for multi-researcher use
- [ ] Chrome extension to add any webpage as a source

---

## Next Tasks

1. Add PDF text extraction for `/app/Day 13 - SortingHat-FHE/SortingHat.pdf` etc.
2. Improve arXiv topic relevance (use `cat:cs.CR AND ti:homomorphic` style queries)
3. Add custom URL source — paste any paper/blog URL and parse it as a source
