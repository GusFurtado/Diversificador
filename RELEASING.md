# Releasing

Pushing a `v*` tag triggers two workflows, each gated on CI:

| Workflow | Publishes |
| --- | --- |
| `.github/workflows/python-publish.yml` | `markowizard` to PyPI |
| `.github/workflows/docker-publish.yml` | `ghcr.io/outliersanalytics/markowizard` image |

## One-time setup

### PyPI trusted publisher

The PyPI workflow publishes with [trusted publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC, no API token). Before the first release, register the publisher on PyPI:

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Add a **pending publisher**:
   - PyPI project name: `markowizard`
   - Owner: `OutliersAnalytics`
   - Repository name: `MarkoWizard`
   - Workflow name: `python-publish.yml`
   - Environment name: `pypi`

### GitHub environment

Create an environment named `pypi` (Settings → Environments). Optionally add
protection rules (required reviewers, tag restriction `v*`).

### GHCR package visibility

The first `docker-publish` run creates a **private** package even though the repo
is public. After it, go to the org's *Packages* → `markowizard` → *Package
settings* → set visibility to **Public** so `docker pull` works without auth.
One-time.

## Cutting a release

1. Bump `version` in `pyproject.toml` (and update `CHANGELOG.md` if present).
2. Merge to `main`, let CI pass.
3. Tag and push:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
4. Watch both workflows. On success:
   - `markowizard` <version> is on PyPI
   - `ghcr.io/outliersanalytics/markowizard:<version>`, `:<major>.<minor>`, and
     `:latest` are pushed (`:latest` only for non-prerelease tags)

Use `v0.1.0rc1`-style tags for pre-releases — PyPI marks them as pre-releases and
the image `:latest` tag is skipped.
