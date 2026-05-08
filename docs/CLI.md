# CLI Reference — `fake-post`

The package installs a `fake-post` console script for one-off renders without
writing Python. Useful for shell scripts, video-pipeline glue, or quick checks.

```
pip install -e .
playwright install chromium
fake-post --help
```

## Synopsis

```
fake-post <platform> --account <id> --out <path.png> [options]
```

`<platform>` is one of `twitter` or `reddit` (and any third-party plugin you've
registered). The CLI always writes one PNG and exits.

## Required arguments

| Flag | Description |
|---|---|
| `<platform>` | Positional. `twitter` or `reddit`. |
| `--account <id>` | Account id from a YAML config (see [Accounts](#accounts)). |
| `--out <path>` | Where to write the PNG. |

## Common options

| Flag | Default | Notes |
|---|---|---|
| `--variant <name>` | `full` | One of `full`, `compact`, `badge`. (Thread variants aren't exposed to the CLI yet — use the Python API.) |
| `--theme <name>` | `light` | Twitter: `light` / `dim` / `dark`. Reddit: `light` / `dark`. |
| `--background <value>` | `theme` | `theme` (matching the card), `transparent`, or any CSS color (`"#000"`, `"rgb(...)"`). |
| `--width <px>` | `600` | Card width in CSS pixels. Final image is `width × scale`. |
| `--scale <float>` | `2.0` | Device pixel ratio. `2.0` = retina-quality. |
| `--font-scale <float>` | `1.0` | Multiplier on every CSS font-size in the templates. |
| `--accounts-file <path>` | (auto) | Override the default YAML lookup with an explicit path. |

## Content options

### Twitter / X

| Flag | Default | Notes |
|---|---|---|
| `--text <str>` | `""` | Tweet body. |
| `--likes <int>` | `0` | |
| `--retweets <int>` | `0` | |
| `--replies <int>` | `0` | The integer reply *count*. (CLI doesn't take nested replies.) |
| `--views <int>` | `0` | |
| `--bookmarks <int>` | `0` | |
| `--date <str>` | `null` | Free-form (e.g. `"May 8, 2026"`). |
| `--time <str>` | `null` | Free-form (e.g. `"11:25 AM"`). |

### Reddit

| Flag | Default | Notes |
|---|---|---|
| `--title <str>` | `""` | Post title. Required for `full` / `compact`. |
| `--text <str>` | `""` | Post body. |
| `--subreddit <str>` | `r/AskReddit` | |
| `--upvotes <int>` | `0` | |
| `--comments <int>` | `0` | The integer comment count. |
| `--flair <str>` | `null` | Case-insensitive lookup against the [flair palette](USAGE.md#flair-colors). |
| `--timestamp <str>` | `null` | E.g. `"3h ago"`. |

## Accounts

The CLI **always** uses an account from a YAML config — there's no way to
inline `name`/`handle` on the command line. This keeps invocations terse.

The default lookup order:

1. `~/.fake_post_generator/accounts.yaml`
2. `./accounts.yaml`

Either can have entries like:

```yaml
elon:
  name: Elon Musk
  handle: elonmusk
  avatar: https://example.com/elon.jpg
  verified: blue
```

Override with `--accounts-file <path>`:

```bash
fake-post twitter --account elon --accounts-file examples/accounts.yaml \
                  --text "hello" --out tweet.png
```

## Examples

### Tweet, dim theme, transparent

```bash
fake-post twitter \
  --account elon \
  --variant full \
  --theme dim \
  --background transparent \
  --text "shipped a python package" \
  --likes 12345 --views 1200000 --replies 42 --retweets 234 \
  --time "11:25 AM" --date "May 9, 2026" \
  --out tweet.png
```

### Reddit post, light theme

```bash
fake-post reddit \
  --account throwaway42 \
  --variant full \
  --theme light \
  --title "I built a fake post generator" \
  --text "AMA. It works headless via Playwright." \
  --subreddit r/Python \
  --upvotes 2412 --comments 312 \
  --flair Showcase \
  --timestamp "3h ago" \
  --out post.png
```

### Avatar badge for video overlay

```bash
fake-post twitter --account elon \
  --variant badge --background transparent \
  --width 720 --font-scale 1.4 --scale 3 \
  --out badge_9x16.png
```

## Exit codes

| Code | Meaning |
|---|---|
| `0`  | Render succeeded; PNG written. |
| `2`  | Account not found in any YAML. |
| `>0` | Other (Playwright failure, IO error, validation error from the platform). The error message is printed to stderr. |

## What the CLI doesn't expose (yet)

For these, use the Python API:

- **Threads / nested replies** (`thread_nested`, `thread_flat`).
- **Random commenter banks** (`build_replies`, `account_bank`).
- **Standalone comments** (`comment`, `comment_compact`).
- **Reddit thread variant** (`thread`).
- **Per-post subreddit overrides** (icon, members, description) — currently
  driven by the auto-loaded `subreddits.yaml`.
- **Custom renderer** swapping (the CLI always uses the default Playwright
  renderer).

See [USAGE.md](USAGE.md) for the full Python API.
