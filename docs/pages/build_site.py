from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_site"
SITE_URL = "https://sidrichardsquantum.github.io/Quantum_Backend_Bench/"
PORTFOLIO_URL = "https://sidrichardsquantum.github.io/"
PROFILE_URL = "https://github.com/SidRichardsQuantum"
REPO_URL = "https://github.com/SidRichardsQuantum/Quantum_Backend_Bench"
PYPI_URL = "https://pypi.org/project/quantum-backend-bench/"

DOCS = [
    ("Overview", ROOT / "README.md", "overview.html", "Package overview and quickstart."),
    ("Usage", ROOT / "USAGE.md", "usage.html", "CLI and Python API workflows."),
    (
        "Results",
        ROOT / "RESULTS.md",
        "results.html",
        "Reference benchmark outputs, plots, and reproduction commands.",
    ),
    ("Theory", ROOT / "THEORY.md", "theory.html", "Benchmark and simulator background."),
    (
        "Methodology",
        ROOT / "METHODOLOGY.md",
        "methodology.html",
        "Measurement design and interpretation.",
    ),
    ("Problem", ROOT / "PROBLEM.md", "problem.html", "Research motivation and scope."),
    ("Schema", ROOT / "SCHEMA.md", "schema.html", "Result and manifest schemas."),
    (
        "Compatibility",
        ROOT / "COMPATIBILITY.md",
        "compatibility.html",
        "Supported Python versions, SDK extras, and local runtime requirements.",
    ),
    ("Limitations", ROOT / "LIMITATIONS.md", "limitations.html", "Known boundaries and caveats."),
    ("Changelog", ROOT / "CHANGELOG.md", "changelog.html", "Release notes and project history."),
]
DOC_OUTPUTS = {source.name: output for _, source, output, _ in DOCS}

BACKENDS = [
    ("Cirq", "Local circuit simulation with depolarizing-noise support."),
    ("PennyLane", "default.qubit and default.mixed local device workflows."),
    ("Braket", "Amazon Braket LocalSimulator adapter for offline execution."),
    ("Qiskit Aer", "AerSimulator execution and noise-injection coverage."),
    ("CUDA-Q", "Optional local CUDA-Q simulator adapter."),
    ("pyQuil", "Local QVM and quilc integration when runtimes are available."),
    ("QuTiP", "Statevector simulation for physics-oriented local coverage."),
    ("pytket", "Analysis-only circuit depth and gate metric support."),
]

BENCHMARKS = [
    ("GHZ", "Entanglement fidelity and distribution quality."),
    ("QFT", "Structured depth and runtime comparisons."),
    ("Bernstein-Vazirani", "Oracle recovery across backend adapters."),
    ("Deutsch-Jozsa", "Balanced and constant oracle behaviour."),
    ("Random Circuit", "Seeded synthetic circuits for scaling studies."),
    ("Quantum Volume", "Square model circuits for simulator stress tests."),
    ("Grover", "Marked-state amplification checks."),
    ("QAOA MaxCut", "Parameterized optimization-style circuits."),
    ("Hamiltonian Simulation", "Trotterized dynamics benchmarks."),
    ("Noise Sensitivity", "Quality curves under injected depolarizing noise."),
]


def slugify(value: str, separator: str = "-") -> str:
    return re.sub(r"[^a-z0-9]+", separator, value.lower()).strip(separator)


def rewrite_links(fragment: str) -> str:
    def replace(match: re.Match[str]) -> str:
        target, anchor = match.group(1), match.group(2) or ""
        output = DOC_OUTPUTS.get(target)
        if not output:
            return match.group(0)
        return f'href="{output}{anchor}"'

    fragment = re.sub(r'href="(?:\./)?([A-Z0-9_-]+\.md)(#[^"]*)?"', replace, fragment)
    return fragment.replace('href="http', 'target="_blank" rel="noopener noreferrer" href="http')


def render_markdown(path: Path) -> str:
    md = markdown.Markdown(
        extensions=["extra", "toc", "tables", "fenced_code", "codehilite", "pymdownx.arithmatex"],
        extension_configs={
            "toc": {"permalink": True, "slugify": slugify},
            "pymdownx.arithmatex": {"generic": True},
        },
        output_format="html5",
    )
    return rewrite_links(md.convert(path.read_text(encoding="utf-8")))


def nav(current: str | None) -> str:
    links = [
        ("Home", "index.html"),
        ("Docs", "overview.html"),
        ("Usage", "usage.html"),
        ("Results", "results.html"),
        ("Theory", "theory.html"),
        ("Compatibility", "compatibility.html"),
        ("Portfolio", PORTFOLIO_URL),
        ("GitHub", REPO_URL),
    ]
    items = []
    for label, href in links:
        active = ' aria-current="page"' if label == current else ""
        target = ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""
        items.append(f'<a href="{href}"{target}{active}>{label}</a>')
    return "\n".join(items)


def page(title: str, body: str, current: str | None = None) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta
      name="description"
      content="Backend-agnostic benchmarking toolkit for local quantum circuit simulators."
    >
    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(title)} | Quantum Backend Bench">
    <meta
      property="og:description"
      content="Benchmark local quantum SDK simulators across Cirq, PennyLane, Braket, Qiskit Aer, CUDA-Q, pyQuil, and QuTiP."
    >
    <meta property="og:url" content="{SITE_URL}">
    <meta name="theme-color" content="#0f5364">
    <title>{html.escape(title)} | Quantum Backend Bench</title>
    <link rel="stylesheet" href="styles.css">
    <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  </head>
  <body>
    <a class="skip-link" href="#top">Skip to main content</a>
    <header class="site-header">
      <a class="brand" href="index.html" aria-label="Quantum Backend Bench home">
        <span class="brand-mark">SR</span>
        <span>Quantum Backend Bench</span>
      </a>
      <nav class="nav-links" aria-label="Primary navigation">
        {nav(current)}
      </nav>
    </header>
    <main id="top" tabindex="-1">{body}</main>
    <footer class="site-footer">
      <span>&copy; 2026 Sid Richards</span>
      <a href="{PORTFOLIO_URL}" target="_blank" rel="noopener noreferrer">Main portfolio</a>
    </footer>
  </body>
</html>
"""


def tag_html(tags: list[str]) -> str:
    return "".join(f"<span>{html.escape(tag)}</span>" for tag in tags)


def card(title: str, description: str, href: str, tags: list[str]) -> str:
    return f"""
      <article class="project-card">
        <div>
          <h3>{html.escape(title)}</h3>
          <p>{html.escape(description)}</p>
        </div>
        <div class="tags">{tag_html(tags)}</div>
        <div class="card-links"><a href="{html.escape(href)}">Read</a></div>
      </article>
    """


def hero_visual() -> str:
    return """
      <div class="hero-visual" aria-hidden="true">
        <svg viewBox="0 0 520 360" role="presentation" focusable="false">
          <defs>
            <pattern id="hero-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M40 0H0V40" />
            </pattern>
          </defs>
          <rect class="visual-bg" width="520" height="360" rx="8" />
          <rect class="visual-grid" width="520" height="360" rx="8" fill="url(#hero-grid)" />
          <g class="visual-circuit">
            <path d="M72 86h344M72 146h344M72 206h344M72 266h344" />
            <path d="M168 86v120M276 146v120M360 86v180" />
            <circle cx="168" cy="86" r="13" />
            <circle cx="168" cy="206" r="13" />
            <circle cx="276" cy="146" r="13" />
            <circle cx="276" cy="266" r="13" />
            <circle cx="360" cy="86" r="13" />
            <circle cx="360" cy="266" r="13" />
            <path d="M121 68v36M103 86h36M103 128l36 36M139 128l-36 36M333 188l54 36M387 188l-54 36" />
            <rect x="218" y="66" width="52" height="40" rx="8" />
            <rect x="400" y="126" width="52" height="40" rx="8" />
          </g>
          <g class="visual-labels">
            <text x="64" y="322">GHZ</text>
            <text x="150" y="322">QFT</text>
            <text x="230" y="322">QAOA</text>
            <text x="314" y="322">Noise</text>
            <text x="410" y="322">PyPI</text>
          </g>
        </svg>
      </div>
    """


def home() -> str:
    benchmark_cards = "\n".join(
        card(name, description, "overview.html#benchmark-suite", ["Benchmark", "Metrics"])
        for name, description in BENCHMARKS
    )
    backend_cards = "\n".join(
        card(name, description, "overview.html#backend-support", ["Backend", "Local", "Simulator"])
        for name, description in BACKENDS
    )
    doc_cards = "\n".join(
        card(label, description, output, ["Documentation"])
        for label, source, output, description in DOCS[1:]
        if source.exists()
    )
    body = f"""
      <section class="hero section">
        <div class="hero-copy">
          <p class="eyebrow">Scientific computing and quantum software</p>
          <h1>Quantum Backend Bench</h1>
          <p class="hero-text">
            Backend-agnostic benchmarking for local quantum circuit simulators, with
            standardized runtime, structure, and distribution metrics across reusable
            benchmark definitions.
          </p>
          <div class="hero-actions" aria-label="Project links">
            <a class="button primary" href="{REPO_URL}" target="_blank" rel="noopener noreferrer">GitHub Repo</a>
            <a class="button" href="{PYPI_URL}" target="_blank" rel="noopener noreferrer">PyPI Package</a>
            <a class="button" href="usage.html">Usage</a>
            <a class="button" href="results.html">Results</a>
            <a class="button" href="{PORTFOLIO_URL}" target="_blank" rel="noopener noreferrer">Main Portfolio</a>
            <a class="button" href="{PROFILE_URL}" target="_blank" rel="noopener noreferrer">GitHub Profile</a>
          </div>
        </div>

        <div class="hero-side">
          {hero_visual()}
          <aside class="focus-panel" aria-label="Package focus areas">
            <h2>Focus Areas</h2>
            <ul>
              <li>Backend-agnostic benchmark specifications</li>
              <li>Local-first SDK simulator comparisons</li>
              <li>Runtime, structure, and distribution metrics</li>
              <li>CLI, manifest, report, and plotting workflows</li>
            </ul>
          </aside>
        </div>
      </section>

      <section id="benchmarks" class="section">
        <div class="section-heading">
          <p class="eyebrow">Benchmark suite</p>
          <h2>Reusable circuits and metrics</h2>
          <p>
            Run common quantum algorithm workloads against multiple local simulator
            adapters and compare standardized outputs.
          </p>
        </div>
        <div class="project-grid">{benchmark_cards}</div>
      </section>

      <section id="backends" class="section">
        <div class="section-heading">
          <p class="eyebrow">Backend support</p>
          <h2>Local SDK coverage</h2>
          <p>
            The package keeps execution local and treats cloud-backed providers as out
            of scope for reproducible benchmark runs.
          </p>
        </div>
        <div class="project-grid">{backend_cards}</div>
      </section>

      <section id="docs" class="section">
        <div class="section-heading">
          <p class="eyebrow">Reference material</p>
          <h2>Documentation</h2>
          <p>
            Guides are generated from the Markdown sources tracked in this repository,
            with the same visual language as the main portfolio.
          </p>
        </div>
        <div class="project-grid">{doc_cards}</div>
      </section>

      <section class="section contact-section">
        <div>
          <p class="eyebrow">Install</p>
          <h2>Use the package from PyPI or source</h2>
          <p>
            Install <code>quantum-backend-bench</code> for the CLI and Python API, then
            add simulator extras as needed.
          </p>
        </div>
        <div class="contact-actions">
          <a class="button primary" href="{PYPI_URL}" target="_blank" rel="noopener noreferrer">PyPI</a>
          <a class="button" href="{REPO_URL}" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a class="button" href="{PORTFOLIO_URL}" target="_blank" rel="noopener noreferrer">Portfolio</a>
        </div>
      </section>
    """
    return page("Home", body, current="Home")


def documentation_page(label: str, source: Path) -> str:
    doc_nav = "".join(
        f'<a href="{output}">{html.escape(name)}</a>'
        for name, doc_source, output, _ in DOCS
        if doc_source.exists()
    )
    current = label if label in {"Usage", "Results", "Theory"} else "Docs"
    body = f"""
      <section class="section doc-layout">
        <aside class="doc-sidebar" aria-label="Documentation navigation">
          <p class="eyebrow">Documentation</p>
          <nav>{doc_nav}</nav>
        </aside>
        <article class="doc-content">{render_markdown(source)}</article>
      </section>
    """
    return page(label, body, current=current)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copyfile(ROOT / "docs/pages/styles.css", OUT / "styles.css")
    assets = ROOT / "docs/pages/assets"
    if assets.exists():
        shutil.copytree(assets, OUT / "docs/pages/assets")
    reference_results = ROOT / "examples/reference_results"
    if reference_results.exists():
        shutil.copytree(reference_results, OUT / "examples/reference_results")
    (OUT / "index.html").write_text(home(), encoding="utf-8")
    for label, source, output, _ in DOCS:
        if source.exists():
            (OUT / output).write_text(documentation_page(label, source), encoding="utf-8")


if __name__ == "__main__":
    main()
