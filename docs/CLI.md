# Finance MMG CLI

Use `mmg.py` from the repo root for local control of the paper-trading engine.

```powershell
py -3 mmg.py --help
```

## Daily Commands

Show current mode, profile, portfolio, budget, and history counts:

```powershell
py -3 mmg.py status
```

Run the safety gate:

```powershell
py -3 mmg.py safety
```

Analyze the market without creating paper orders:

```powershell
py -3 mmg.py analyze --checkpoint close --force
```

Run the engine and allow paper orders:

```powershell
py -3 mmg.py execute --checkpoint close --force
```

If a broad scan needs more time:

```powershell
py -3 mmg.py analyze --checkpoint close --force --timeout 1800
```

## Capability Profiles

List profiles:

```powershell
py -3 mmg.py profile list
```

Apply the maximum paper-research profile:

```powershell
py -3 mmg.py profile apply max-paper
```

Preview a profile without writing files:

```powershell
py -3 mmg.py profile apply balanced --dry-run
```

Profiles currently available:

- `conservative`: smaller paper budget, 10-symbol scan, buy threshold 80.
- `balanced`: medium paper budget, 24-symbol scan, buy threshold 74.
- `max-paper`: larger paper budget, full NIFTY 500 scan (light fetch), buy threshold 70, NEUTRAL confidence floor 0.50.
- `evidence`: like max-paper, plus optional paper exits after observation triggers so round-trips can accumulate (still paper-only).

```powershell
py -3 mmg.py profile apply evidence
```

The scanned universe comes from `config/nifty500.csv` via `active_source` in
`config/universe.yml`; the run is capped by `market_data.max_symbols_per_run`.

All profiles keep `allow_real_orders: false`; they only change paper-trading research capacity.

## Config Inspection

Read a config value:

```powershell
py -3 mmg.py config get scoring hybrid_scoring.buy_threshold
```

Set a config value:

```powershell
py -3 mmg.py config set settings market_data.max_symbols_per_run 20
```

Show a full config file:

```powershell
py -3 mmg.py config show risk
```

## History

Recent signals:

```powershell
py -3 mmg.py history signals --limit 10
```

Only buy candidates:

```powershell
py -3 mmg.py history signals --label BUY_SMALL_PAPER --limit 20
```

Recent trades:

```powershell
py -3 mmg.py history trades --limit 20
```

Machine-readable output:

```powershell
py -3 mmg.py history signals --limit 5 --json
```

## Observe flags (analyze / execute)

```powershell
py -3 mmg.py execute --checkpoint close --force --observe
py -3 mmg.py execute --observe-only --force
py -3 mmg.py execute --observe-only --focused-symbol RELIANCE.NS --force
```

(`--escalation-report` is available on `python src/main.py` only.)

## Backfill (price-only replay)

Descriptive historical replay of price strategies — **not a profitability claim**:

```powershell
py -3 mmg.py backfill --symbols-limit 8
py -3 mmg.py backfill --lookback 2y --window 22 --horizon 20 --step 5
```

Writes `data/reports/price_replay.{json,md}` and `public/data/price_replay.json`.

## Learn (proposal only)

```powershell
py -3 mmg.py learn propose
py -3 mmg.py learn show
```

Writes a labeled **PROPOSAL — not applied**. Apply paper changes yourself with
`profile apply` / `config set`. Never enables live trading.

## Remote CLI (GitHub Actions)

Repo → Actions → **mmg CLI (remote)** (`cli.yml`), or:

```powershell
gh workflow run cli.yml -f subcommand="status"
gh workflow run cli.yml -f subcommand="profile apply evidence"
gh workflow run cli.yml -f subcommand="learn propose"
```

Mutating runs may commit `config/`, `data/reports/`, and `public/data/`.
