from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.schemas.memory import (
    ExternalKnowledgeCatalog,
    ExternalKnowledgeStory,
    ExternalStoryMatch,
)


K8S_AF_URL = "https://k8s.af/"
BUNDLED_K8S_AF_CATALOG = Path(__file__).parent / "sources" / "k8s_af.json"
LOCAL_K8S_AF_CATALOG = Path("data/runbooks/external/k8s_af.json")
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
WORD_PATTERN = re.compile(r"[a-z0-9_.:/-]+")


class _K8sAfHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ul_depth = 0
        self.current: dict[str, object] | None = None
        self.in_story_anchor = False
        self.in_metadata_item = False
        self.text_parts: list[str] = []
        self.records: list[dict[str, object]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag == "ul":
            self.ul_depth += 1
            return

        if tag == "li" and self.ul_depth == 1 and self.current is None:
            self.current = {
                "canonical_url": "",
                "title": "",
                "technologies": [],
                "impact": "",
            }
            return

        if tag == "a" and self.ul_depth == 1 and self.current is not None:
            href = dict(attrs).get("href") or ""
            self.current["canonical_url"] = href.strip()
            self.in_story_anchor = True
            self.text_parts = []
            return

        if tag == "li" and self.ul_depth == 2 and self.current is not None:
            self.in_metadata_item = True
            self.text_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_story_anchor or self.in_metadata_item:
            self.text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_story_anchor:
            assert self.current is not None
            self.current["title"] = " ".join(
                " ".join(self.text_parts).split()
            )
            self.in_story_anchor = False
            self.text_parts = []
            return

        if tag == "li" and self.in_metadata_item:
            assert self.current is not None
            metadata = " ".join(" ".join(self.text_parts).split())
            label, _, value = metadata.partition(":")
            normalized_label = label.strip().lower()
            value = value.strip()
            if normalized_label == "involved":
                self.current["technologies"] = [
                    item.strip()
                    for item in value.split(",")
                    if item.strip()
                ]
            elif normalized_label in {"impact", "impace"}:
                self.current["impact"] = value
            self.in_metadata_item = False
            self.text_parts = []
            return

        if tag == "ul":
            self.ul_depth -= 1
            return

        if tag == "li" and self.ul_depth == 1 and self.current is not None:
            if self.current.get("canonical_url") and self.current.get("title"):
                self.records.append(self.current)
            self.current = None


def _story_id(canonical_url: str) -> str:
    digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:16]
    return f"k8s-af-{digest}"


def _checksum(record: dict[str, object]) -> str:
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_k8s_af_html(
    html: str,
    *,
    imported_at: datetime | None = None,
) -> ExternalKnowledgeCatalog:
    """
    Parse k8s.af metadata without retrieving linked article bodies.
    """

    parser = _K8sAfHTMLParser()
    parser.feed(html)

    stories: list[ExternalKnowledgeStory] = []
    seen_urls: set[str] = set()
    for record in parser.records:
        canonical_url = str(record["canonical_url"])
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)

        title = str(record["title"])
        years = YEAR_PATTERN.findall(title)
        year = int(years[-1]) if years else None
        normalized_record = {
            "canonical_url": canonical_url,
            "title": title,
            "technologies": list(record["technologies"]),
            "impact": str(record["impact"]),
        }
        stories.append(
            ExternalKnowledgeStory(
                story_id=_story_id(canonical_url),
                source_catalog="k8s.af",
                source_catalog_url=K8S_AF_URL,
                canonical_url=canonical_url,
                source_host=urlparse(canonical_url).netloc.lower(),
                title=title,
                published_year=year,
                technologies=normalized_record["technologies"],
                impact=normalized_record["impact"],
                source_checksum=_checksum(normalized_record),
            )
        )

    timestamp = imported_at or datetime.now(timezone.utc)
    return ExternalKnowledgeCatalog(
        source_catalog="k8s.af",
        source_catalog_url=K8S_AF_URL,
        imported_at=timestamp,
        story_count=len(stories),
        stories=stories,
    )


def fetch_k8s_af_catalog(
    *,
    url: str = K8S_AF_URL,
    timeout_seconds: int = 20,
) -> ExternalKnowledgeCatalog:
    """
    Fetch the public index only; linked story bodies are never downloaded.
    """

    response = requests.get(
        url,
        timeout=timeout_seconds,
        headers={"User-Agent": "AOP-Knowledge-Importer/0.39 (+https://k8s.af/)"},
    )
    response.raise_for_status()
    return parse_k8s_af_html(response.text)


def save_external_catalog(
    catalog: ExternalKnowledgeCatalog,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        catalog.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def load_external_catalog(path: Path | None = None) -> ExternalKnowledgeCatalog:
    selected = path
    if selected is None:
        selected = (
            LOCAL_K8S_AF_CATALOG
            if LOCAL_K8S_AF_CATALOG.exists()
            else BUNDLED_K8S_AF_CATALOG
        )
    return ExternalKnowledgeCatalog.model_validate_json(
        selected.read_text(encoding="utf-8")
    )


def search_external_stories(
    catalog: ExternalKnowledgeCatalog,
    *,
    text: str = "",
    technology: str | None = None,
    limit: int = 10,
) -> list[ExternalStoryMatch]:
    """
    Search historical metadata without promoting it to verified guidance.
    """

    query_terms = set(WORD_PATTERN.findall(text.lower()))
    technology_term = technology.lower() if technology else None
    matches: list[ExternalStoryMatch] = []

    for story in catalog.stories:
        technology_values = {value.lower() for value in story.technologies}
        if technology_term and not any(
            technology_term in value for value in technology_values
        ):
            continue

        haystack = " ".join(
            [story.title, story.impact, *story.technologies, story.source_host]
        ).lower()
        story_terms = set(WORD_PATTERN.findall(haystack))
        overlap = query_terms & story_terms
        score = len(overlap)
        matched_terms = set(overlap)

        if technology_term:
            score += 5
            matched_terms.add(technology)

        if not query_terms and not technology_term:
            score = 1

        if score > 0:
            matches.append(
                ExternalStoryMatch(
                    story=story,
                    score=score,
                    matched_terms=sorted(matched_terms),
                )
            )

    matches.sort(
        key=lambda item: (
            item.score,
            item.story.published_year or 0,
            item.story.title,
        ),
        reverse=True,
    )
    return matches[: max(limit, 0)]
