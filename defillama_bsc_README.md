# DeFiLlama BSC DEX Data Analysis

This project fetches and analyzes data from DeFiLlama API about Decentralized Exchanges (DEXs) on the Binance Smart Chain (BSC).

## Metrics Collected

1. **Trading Volume (24h, 7d, 30d, Total)**
   - Description: Total USD value of swap transactions
   - Source: DeFiLlama API

2. **Total Value Locked (TVL - Total & Per Pool/Pair)**
   - Description: Value of assets deposited in liquidity pools
   - Source: DeFiLlama API

3. **Top Liquidity Pools / Trading Pairs**
   - Description: Ranked by TVL
   - Source: DeFiLlama Yields API

4. **Fees (Total 24h/7d/30d)**
   - Description: Fees paid by traders (% of volume)
   - Source: DeFiLlama API

5. **Protocol Revenue (Total 24h/7d/30d)**
   - Description: Portion of fees accumulated for the protocol treasury/DAO
   - Source: DeFiLlama API

## Requirements

- Python 3.10+
- Required packages:
  - requests
  - pandas
  - matplotlib
  - seaborn

## Usage

1. First, run the data collection script:

```
conda activate py310
python defillama_bsc_dex_data.py
```

This will:
- Fetch all DEX protocols on BSC
- Collect TVL, volume, fees, and protocol revenue data
- Identify top liquidity pools for each DEX
- Save all raw data as JSON files in the `defillama_data` directory
- Generate a summary CSV file with key metrics

2. Then, run the visualization script:

```
conda activate py310
python defillama_bsc_visualization.py
```

This will create various visualizations:
- Top DEXs by TVL
- Volume comparison across different time periods
- Fees to volume ratio analysis
- Top liquidity pools by TVL

## Output Files

All output files are stored in the `defillama_data` directory:

- `bsc_dexs.json`: List of all DEX protocols on BSC
- `bsc_dexs_summary.csv`: Summary of key metrics for all DEXs
- `{protocol_slug}_tvl.json`: TVL data for each protocol
- `{protocol_slug}_volumes.json`: Volume data for each protocol
- `{protocol_slug}_fees.json`: Fee data for each protocol
- `{protocol_slug}_top_pools.json`: Top pools data for each protocol
- Visualization PNG files:
  - `top_dexs_by_tvl.png`
  - `volume_comparison.png`
  - `fee_to_volume_ratio.png`
  - `top_pools_by_tvl.png`

## API Endpoints Used

- `https://api.llama.fi/protocols`: Get all protocols
- `https://api.llama.fi/protocol/{protocol_slug}`: Get TVL data
- `https://api.llama.fi/summary/dexs/{protocol_slug}`: Get volume data
- `https://api.llama.fi/summary/fees/{protocol_slug}`: Get fee data
- `https://yields.llama.fi/pools`: Get pools data 