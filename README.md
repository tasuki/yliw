# Your Life In Weeks

Needs whatever `python3`, no other dependencies hopefully.

## Use

Generate `.html` files next to `.toml` files in each directory. If one has `watchexec`, run perhaps something like this:

```
watchexec --restart --verbose --debounce=100ms \
  --watch . --watch ../yliw-private/ --ignore '*.html' \
  --shell=bash -- 'python3 liw_batch.py sample/ ../yliw-private/'
```
