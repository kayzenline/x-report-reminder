# Lessons

- `setuptools.backends.legacy:build` is not available in older setuptools; use `setuptools.build_meta` instead.
- Twitter's free API tier only allows writing, not reading. twscrape (user-credential login) is the practical read alternative.
- Always use `Path(os.path.expanduser(...))` for paths with `~` — especially for iCloud paths which contain spaces.
