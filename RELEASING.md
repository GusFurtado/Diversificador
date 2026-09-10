# Releasing

Pushing a `v*` tag triggers `.github/workflows/publish.yml`, which — after CI
passes — builds and publishes the PyPI package and the GHCR container image.

## One-time setup

### PyPI trusted publisher

The workflow publishes with [trusted publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC, no API token). Before the first release, register the publisher on PyPI:

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Add a **pending publisher** (the project doesn't exist on PyPI yet):
   - PyPI project name: `markowizard`
   - Owner: `OutliersAnalytics`
   - Repository name: `MarkoWizard`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

### GitHub environment

Create an environment named `pypi` (Settings → Environments). Optionally add
protection rules (required reviewers, tag restriction `v*`).

## Cutting a release

1. Bump `version` in `pyproject.toml` (and update `CHANGELOG.md` if present).
2. Merge to `main`, let CI pass.
3. Tag and push:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
4. Watch the **Publish** workflow. On success:
   - `markowizard` <version> is on PyPI
   - `ghcr.io/outliersanalytics/markowizard:<version>` and `:<major>.<minor>` are pushed

Use `v0.1.0rc1`-style tags for pre-releases (PyPI treats them as pre-releases).

> The container's `:latest` tag and its dependency setup still need work — see
> the open packaging follow-ups. This doc covers the PyPI release path.
