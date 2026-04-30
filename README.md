```
watchexec --restart --verbose --debounce=100ms \
  --watch . \
  --shell=bash -- 'python3 life_in_weeks.py sample/gregor-mendel.toml > gregor-mendel.html'
```

```
watchexec --restart --verbose --debounce=100ms \
  --watch . --watch ../yliw-private/ \
  --shell=bash -- 'python3 life_in_weeks.py ../yliw-private/hania.toml > hania.html'
```
