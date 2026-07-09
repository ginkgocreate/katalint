# Publishing to PyPI

katalint publishes via GitHub Actions using
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) —
no API token is stored in this repository.

## One-time setup (do this once, before the first release)

1. Log in to [pypi.org](https://pypi.org) with the account that will own the
   `katalint` project. (If the project does not exist yet, PyPI supports
   registering a **pending publisher** for a name that hasn't been published
   yet — you do not need to upload a release manually first.)
2. Go to **Account Settings → Publishing** (or, for an existing project,
   the project's **Settings → Publishing**) and add a new trusted publisher
   with:
   - **PyPI Project Name:** `katalint`
   - **Owner:** `ginkgocreate`
   - **Repository name:** `katalint`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. In this repo's GitHub Settings → Environments, create an environment named
   `pypi` (optionally add required reviewers here if you want a manual
   approval gate on every publish — recommended).

## Releasing

Publishing is triggered by creating a GitHub Release (not just a tag):

```bash
git tag v0.1.1
git push origin v0.1.1
gh release create v0.1.1 --generate-notes
```

The `publish` workflow builds the sdist/wheel and uploads them to PyPI via
Trusted Publishing when the release is published. No secrets to rotate, no
tokens to leak.
