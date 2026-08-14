from __future__ import annotations

import json
from pathlib import Path

import click

from app.memory.runbooks.catalog import list_runbook_chunks
from app.memory.runbooks.external import (
    BUNDLED_K8S_AF_CATALOG,
    K8S_AF_URL,
    LOCAL_K8S_AF_CATALOG,
    fetch_k8s_af_catalog,
    load_external_catalog,
    parse_k8s_af_html,
    save_external_catalog,
    search_external_stories,
)
from app.memory.runbooks.retrieval import (
    format_runbook_context_for_prompt,
    search_runbooks,
)
from app.memory.runbooks.reviewed import (
    get_review,
    load_review_catalog,
    review_queue,
    search_reviews,
)
from app.schemas.memory import RunbookQuery


def _echo_json(payload: object) -> None:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    click.echo(json.dumps(payload, indent=2, default=str))


@click.group("runbooks")
def runbooks() -> None:
    """
    Retrieve trusted runbook snippets for bounded RAG context.
    """


@runbooks.group("import")
def import_sources() -> None:
    """
    Import provenance-first external knowledge metadata.
    """


@import_sources.command("k8s-af")
@click.option(
    "--input-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Parse previously saved k8s.af HTML instead of using the network.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=LOCAL_K8S_AF_CATALOG,
    show_default=True,
)
@click.option("--source-url", default=K8S_AF_URL, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def import_k8s_af(
    input_file: Path | None,
    output: Path,
    source_url: str,
    as_json: bool,
) -> None:
    """
    Import k8s.af links, technology tags, and impact metadata only.
    """

    if input_file is not None:
        catalog = parse_k8s_af_html(input_file.read_text(encoding="utf-8"))
    else:
        catalog = fetch_k8s_af_catalog(url=source_url)

    save_external_catalog(catalog, output)
    payload = {
        "source_catalog": catalog.source_catalog,
        "source_catalog_url": catalog.source_catalog_url,
        "story_count": catalog.story_count,
        "output": str(output),
        "content_scope": "metadata_only",
        "license_status": "unverified",
        "review_state": "source_review_required",
    }
    if as_json:
        _echo_json(payload)
        return

    click.echo("AOP external knowledge import")
    for key, value in payload.items():
        click.echo(f"{key}: {value}")
    click.echo(
        "boundary: Original sources must be reviewed before root cause or "
        "solution guidance enters RCA."
    )


@runbooks.command("sources")
@click.option("--json", "as_json", is_flag=True)
def sources(as_json: bool) -> None:
    """
    Show external knowledge source and snapshot status.
    """

    active_path = (
        LOCAL_K8S_AF_CATALOG
        if LOCAL_K8S_AF_CATALOG.exists()
        else BUNDLED_K8S_AF_CATALOG
    )
    catalog = load_external_catalog(active_path)
    payload = {
        "source_catalog": catalog.source_catalog,
        "source_catalog_url": catalog.source_catalog_url,
        "active_snapshot": str(active_path),
        "imported_at": catalog.imported_at,
        "story_count": catalog.story_count,
        "content_policy": catalog.content_policy,
    }
    if as_json:
        _echo_json(payload)
        return

    click.echo("AOP external knowledge sources")
    for key, value in payload.items():
        click.echo(f"{key}: {value}")


@runbooks.group("stories")
def stories() -> None:
    """
    Search imported historical incident metadata.
    """


@stories.command("search")
@click.option("--text", default="")
@click.option("--technology")
@click.option("--limit", type=int, default=10, show_default=True)
@click.option(
    "--catalog",
    "catalog_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "as_json", is_flag=True)
def search_stories(
    text: str,
    technology: str | None,
    limit: int,
    catalog_path: Path | None,
    as_json: bool,
) -> None:
    """
    Search metadata; results are historical evidence, not verified solutions.
    """

    catalog = load_external_catalog(catalog_path)
    matches = search_external_stories(
        catalog,
        text=text,
        technology=technology,
        limit=limit,
    )
    if as_json:
        _echo_json([match.model_dump() for match in matches])
        return

    click.echo("AOP historical Kubernetes failure stories")
    click.echo(f"matches: {len(matches)}")
    click.echo(
        "boundary: Metadata only; review the original source before using "
        "root cause or solution guidance."
    )
    for match in matches:
        story = match.story
        click.echo()
        click.echo(f"- {story.title}")
        click.echo(f"  score: {match.score}")
        click.echo(f"  involved: {', '.join(story.technologies)}")
        click.echo(f"  impact: {story.impact}")
        click.echo(f"  source: {story.canonical_url}")
        click.echo(f"  review_state: {story.review_state}")


@runbooks.group("review")
def review() -> None:
    """
    Inspect source-backed knowledge review state and guidance.
    """


@review.command("queue")
@click.option("--limit", type=int, default=20, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def review_queue_command(limit: int, as_json: bool) -> None:
    """
    List imported stories that still require original-source review.
    """

    pending = review_queue()
    payload = {
        "pending_count": len(pending),
        "reviewed_count": load_review_catalog().review_count,
        "items": pending[: max(limit, 0)],
    }
    if as_json:
        _echo_json(payload)
        return

    click.echo("AOP external knowledge review queue")
    click.echo(f"pending_count: {payload['pending_count']}")
    click.echo(f"reviewed_count: {payload['reviewed_count']}")
    for item in payload["items"]:
        click.echo()
        click.echo(f"- {item['story_id']}: {item['title']}")
        click.echo(f"  involved: {', '.join(item['technologies'])}")
        click.echo(f"  source: {item['canonical_url']}")


@review.command("show")
@click.argument("review_or_story_id")
@click.option("--json", "as_json", is_flag=True)
def show_review(review_or_story_id: str, as_json: bool) -> None:
    """
    Show reported facts, reusable checks, and historical-risk boundaries.
    """

    try:
        item = get_review(review_or_story_id)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        _echo_json(item)
        return

    click.echo(item.source_title)
    click.echo(f"review_id: {item.review_id}")
    click.echo(f"story_id: {item.story_id}")
    click.echo(f"review_state: {item.review_state}")
    click.echo(f"source: {item.source_url}")
    click.echo()
    click.echo("Reported root cause")
    click.echo(item.reported_root_cause)
    click.echo()
    click.echo("Reusable checks")
    for check in item.reusable_checks:
        click.echo(f"- {check}")
    click.echo()
    click.echo("Safe read-only commands")
    for command in item.safe_commands:
        click.echo(f"- {command}")
    click.echo()
    click.echo("Risky or historical actions")
    for action in item.risky_or_historical_actions:
        click.echo(f"- {action}")
    click.echo()
    click.echo(f"boundary: {item.safety_boundary}")


@review.command("search")
@click.option("--text", required=True)
@click.option(
    "--state",
    "review_state",
    default="guidance_reviewed",
    show_default=True,
)
@click.option("--limit", type=int, default=10, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def search_reviewed(
    text: str,
    review_state: str,
    limit: int,
    as_json: bool,
) -> None:
    """
    Search reviewed source-backed knowledge.
    """

    matches = search_reviews(
        text,
        review_state=review_state,
        limit=limit,
    )
    if as_json:
        _echo_json([item.model_dump() for item in matches])
        return

    click.echo("AOP reviewed external knowledge")
    click.echo(f"matches: {len(matches)}")
    for item in matches:
        click.echo()
        click.echo(f"- {item.review_id}: {item.source_title}")
        click.echo(f"  state: {item.review_state}")
        click.echo(f"  root_cause: {item.reported_root_cause}")
        click.echo(f"  source: {item.source_url}")


@runbooks.command("list")
@click.option("--domain")
@click.option("--incident-type")
@click.option("--json", "as_json", is_flag=True)
def list_chunks(
    domain: str | None,
    incident_type: str | None,
    as_json: bool,
) -> None:
    """
    List source-controlled runbook chunks.
    """

    chunks = list_runbook_chunks(
        domain=domain,
        incident_type=incident_type,
    )
    if as_json:
        _echo_json([chunk.model_dump() for chunk in chunks])
        return

    for chunk in chunks:
        click.echo(f"{chunk.runbook_id:40} {chunk.domain:16} {chunk.title}")


@runbooks.command("search")
@click.option("--domain")
@click.option("--incident-type")
@click.option("--text", default="")
@click.option("--limit", type=int, default=3, show_default=True)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json", "prompt"]),
    default="summary",
    show_default=True,
)
def search(
    domain: str | None,
    incident_type: str | None,
    text: str,
    limit: int,
    output_format: str,
) -> None:
    """
    Search trusted runbook chunks by domain, incident type, and text.
    """

    result = search_runbooks(
        RunbookQuery(
            domain=domain,
            incident_type=incident_type,
            text=text,
            limit=limit,
        )
    )

    if output_format == "json":
        _echo_json(result)
        return

    if output_format == "prompt":
        click.echo(format_runbook_context_for_prompt(result))
        return

    click.echo("AOP runbook retrieval")
    click.echo(f"total_matches: {result.total_matches}")
    click.echo(
        "boundary: Runbook match is guidance, not proof. Verify with live evidence."
    )
    for match in result.matches:
        chunk = match.chunk
        click.echo()
        click.echo(f"- {chunk.title}")
        click.echo(f"  id: {chunk.runbook_id}/{chunk.chunk_id}")
        click.echo(f"  domain: {chunk.domain}")
        click.echo(f"  score: {match.score}")
        click.echo(f"  matched: {', '.join(match.matched_terms) or 'none'}")
        click.echo(f"  summary: {chunk.summary}")
