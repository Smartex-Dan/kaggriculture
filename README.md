# Kaggriculture

Competitive farming agent for the Kaggriculture Kaggle competition
(two-agent, 720-turn turn-based farming/economic simulation).

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Development ladder

See project roadmap doc for the full plan. Short version:

1. Random agent (verify environment integration)
2. Starter agent analysis
3. Simple rule-based farming agent
4. Crop/economic strategy
5. Market intelligence
6. Labor optimization
7. Animals + fertilizer
8. Land expansion / town-demand forecasting
9. Opponent modeling
10. Long-horizon planning / search
11. RL experiments (only if the heuristic ceiling is actually hit)
12. Hybrid architecture

## Project layout

```
kaggriculture/
├── src/
│   ├── agent.py       # agent() entry point, wires everything together
│   ├── state.py        # observation parsing / state representation
│   ├── strategy.py     # StrategicPlanner
│   ├── economy.py      # profitability / ROI calculations
│   ├── market.py        # MarketModel (price estimation, timing)
│   ├── farm.py           # farm/crop/animal action logic
│   ├── workers.py         # labor allocation, hiring decisions
│   ├── opponent.py         # opponent modeling from public info
│   └── utils.py             # shared helpers
├── experiments/             # experiment logs (see below)
├── notebooks/                 # exploratory analysis
├── logs/                       # raw game logs
├── submissions/                 # packaged Kaggle submissions
├── tests/                        # pytest tests
├── requirements.txt
├── README.md
└── main.py                        # local entry point for running games
```

## Experiment tracking

`experiments/log.csv` tracks every benchmark run:
`experiment_id, version, opponent, n_games, win_rate, avg_bank, median_bank, notes`

Don't trust a strategy change until it's been run across 100+ games
against the benchmark suite (Random, Starter, previous best version).
