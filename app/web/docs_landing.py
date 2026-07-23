from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

FRONTEND_URL = "https://ai-automation-platform.com"
GITHUB_REPOSITORY_URL = "https://github.com/Anastasia-front/ai-platform-backend"

router = APIRouter()


def _external_link_attrs(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return ' target="_blank" rel="noopener noreferrer"'
    return ""


def _resource_card(title: str, description: str, href: str, label: str) -> str:
    safe_href = escape(href, quote=True)
    attrs = _external_link_attrs(href)
    return f"""
        <article class="card">
          <div>
            <h2>{escape(title)}</h2>
            <p>{escape(description)}</p>
          </div>
          <a class="card-link" href="{safe_href}"{attrs}>{escape(label)}</a>
        </article>
    """


def render_docs_landing(
    *,
    api_title: str,
    api_version: str,
    api_description: str | None,
) -> str:
    description = api_description or "Developer documentation and service resources"
    cards = "\n".join(
        [
            _resource_card(
                "Swagger UI",
                "Interactive API explorer",
                "/swagger",
                "Open Swagger",
            ),
            _resource_card("ReDoc", "Structured API reference", "/redoc", "Open ReDoc"),
            _resource_card(
                "OpenAPI Specification",
                "Raw machine-readable schema",
                "/openapi.json",
                "View JSON",
            ),
            _resource_card(
                "API Status",
                "Service health endpoint",
                "/health",
                "Check status",
            ),
            _resource_card(
                "Web Application",
                "Open the production frontend",
                FRONTEND_URL,
                "Open app",
            ),
            _resource_card(
                "GitHub Repository",
                "Open the source repository",
                GITHUB_REPOSITORY_URL,
                "Open source",
            ),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <title>{escape(api_title)} API Documentation</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f7f8fb;
        --panel: #ffffff;
        --text: #18202f;
        --muted: #5e6878;
        --line: #d9dee8;
        --accent: #0ea5e9;
        --accent-strong: #0ea5e9;
        --eyebrow:#ea7130;
        --shadow: 0 18px 45px rgba(24, 32, 47, 0.08);
      }}

      * {{ box-sizing: border-box; }}

      body {{
        margin: 0;
        min-height: 100vh;
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--text);
        background:
          linear-gradient(180deg, #eef3fb 0, rgba(238, 243, 251, 0) 340px),
          var(--bg);
      }}

      main {{
        width: min(1120px, calc(100% - 32px));
        margin: 0 auto;
        padding: 56px 0;
      }}

      .intro {{
        display: grid;
        gap: 18px;
        margin-bottom: 34px;
      }}

      .eyebrow {{
        margin: 0;
        color: var(--eyebrow);
        font-size: 0.84rem;
        font-weight: 700;
        text-transform: uppercase;
      }}

      h1 {{
        margin: 0;
        font-size: clamp(2.25rem, 7vw, 4.75rem);
        line-height: 0.98;
        letter-spacing: 0;
      }}

      .subtitle {{
        margin: 0;
        max-width: 680px;
        color: var(--muted);
        font-size: 1.16rem;
        line-height: 1.6;
      }}

      .metadata {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 8px 0 0;
        padding: 0;
        list-style: none;
      }}

      .metadata li {{
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.72);
        color: var(--muted);
        font-size: 0.92rem;
      }}

      .grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
      }}

      .card {{
        min-height: 210px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 28px;
        padding: 24px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--panel);
        box-shadow: var(--shadow);
      }}

      h2 {{
        margin: 0 0 10px;
        font-size: 1.18rem;
        letter-spacing: 0;
      }}

      .card p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }}

      .card-link {{
        width: fit-content;
        max-width: 100%;
        display: inline-flex;
        align-items: center;
        min-height: 42px;
        padding: 0 16px;
        border-radius: 6px;
        background: var(--accent);
        color: #ffffff;
        font-weight: 700;
        text-decoration: none;
      }}

      .card-link:hover,
      .card-link:focus-visible {{
        background: var(--accent-strong);
      }}

      .card-link:focus-visible {{
        outline: 3px solid rgba(14, 165, 233, 0.35);
        outline-offset: 3px;
      }}

      @media (max-width: 860px) {{
        main {{ padding: 40px 0; }}
        .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      }}

      @media (max-width: 620px) {{
        main {{ width: min(100% - 24px, 1120px); }}
        .grid {{ grid-template-columns: 1fr; }}
        .card {{ min-height: 180px; padding: 20px; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="intro" aria-labelledby="page-title">
        <p class="eyebrow">documentation</p>
        <h1 id="page-title">{escape(api_title)} API</h1>
        <p class="subtitle">{escape(description)}</p>
        <ul class="metadata" aria-label="API metadata">
          <li>Framework: {escape('FastAPI')}</li>
          <li>Version: {escape(api_version)}</li>
        </ul>
      </section>
      <section class="grid" aria-label="Documentation resources">
        {cards}
      </section>
    </main>
  </body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def docs_landing(request: Request) -> HTMLResponse:
    return HTMLResponse(
        render_docs_landing(
            api_title=request.app.title,
            api_version=request.app.version,
            api_description=request.app.description,
        )
    )


@router.get("/docs", include_in_schema=False)
async def legacy_docs_redirect() -> RedirectResponse:
    return RedirectResponse(url="/swagger", status_code=307)
