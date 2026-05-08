# Your Life In Weeks

Needs whatever `python3`, no other dependencies hopefully.

## Use

Generate `.html` files next to `.toml` files in each directory. If one has `watchexec`, run perhaps something like this:

```
watchexec --restart --verbose --debounce=100ms \
  --watch . --watch ../yliw-private/ --ignore '*.html' \
  --shell=bash -- 'python3 liw_batch.py sample/ ../yliw-private/'
```

## Deploy (to GitHub Pages)

A workflow is included at `.github/workflows/pages.yml`. It builds a standalone site into `dist/`:

```
python3 build_site.py sample dist
```

To finish setup on GitHub:

1. Push to `master`.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. After the workflow runs, the site will publish automatically on pushes to `master`.
