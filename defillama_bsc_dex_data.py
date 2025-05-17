import requests
import pandas as pd
import json
from datetime import datetime
import time
import os

def fetch_dex_protocols():
    """Fetch all DEX protocols on BSC from DeFiLlama"""
    url = "https://api.llama.fi/protocols"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching protocols: {response.status_code}")
        return []
    
    protocols = response.json()
    
    # Print some debug info
    print(f"Total protocols: {len(protocols)}")
    
    # Count categories
    categories = {}
    for p in protocols:
        cat = p.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("Categories found:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")
    
    # Check chains
    chains_count = {}
    for p in protocols:
        for chain in p.get('chains', []):
            chains_count[chain] = chains_count.get(chain, 0) + 1
    
    print("\nTop chains found:")
    for chain, count in sorted(chains_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {chain}: {count}")
    
    # Filter for DEXs on BSC - be more flexible with naming
    bsc_chains = ['bsc', 'binance', 'binancesmartchain', 'bnb chain', 'BSC']
    
    bsc_dexs = []
    for p in protocols:
        category = p.get('category', '').lower()
        chains = [chain.lower() for chain in p.get('chains', [])]
        
        if any(dex_term in category.lower() for dex_term in ['dexes', 'dex', 'exchange']):
            if any(bsc_term.lower() in chain for chain in chains for bsc_term in bsc_chains):
                bsc_dexs.append(p)
    
    return bsc_dexs

def fetch_protocol_tvl(protocol_slug):
    """Fetch TVL data for a specific protocol"""
    url = f"https://api.llama.fi/protocol/{protocol_slug}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching TVL for {protocol_slug}: {response.status_code}")
        return None
    
    return response.json()

def fetch_dex_volumes(protocol_slug):
    """Fetch volume data for a specific protocol"""
    url = f"https://api.llama.fi/summary/dexs/{protocol_slug}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyVolume"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching volumes for {protocol_slug}: {response.status_code}")
        return None
    
    return response.json()

def fetch_dex_fees(protocol_slug):
    """Fetch fee data for a specific protocol"""
    url = f"https://api.llama.fi/summary/fees/{protocol_slug}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching fees for {protocol_slug}: {response.status_code}")
        return None
    
    return response.json()

def fetch_top_pools(dex_name=None):
    """Fetch top liquidity pools, optionally filtered by DEX name"""
    url = "https://yields.llama.fi/pools"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching pools: {response.status_code}")
        return []
    
    pools = response.json().get('data', [])
    
    # Filter by DEX name if provided
    if dex_name:
        pools = [p for p in pools if dex_name.lower() in p.get('project', '').lower()]
    
    # Sort by TVL (descending)
    pools = sorted(pools, key=lambda x: x.get('tvlUsd', 0), reverse=True)
    
    return pools

def get_numeric_value(value):
    """Convert value to a number if it's not already one"""
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, list) and len(value) > 0:
        # If it's a list, try to get the first numeric value
        for item in value:
            if isinstance(item, (int, float)):
                return item
        return 0
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

def main():
    # Create output directory
    output_dir = "defillama_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Fetch all DEX protocols on BSC
    print("Fetching DEX protocols on BSC...")
    bsc_dexs = fetch_dex_protocols()
    print(f"Found {len(bsc_dexs)} DEX protocols on BSC")
    
    # Limit to the first 20 for testing
    bsc_dexs = bsc_dexs[:20]
    print(f"Using first {len(bsc_dexs)} DEXs for processing")
    
    # If no DEXs found, try a different approach - fetch top BSC protocols
    if len(bsc_dexs) == 0:
        print("No DEXs found with the initial method. Trying a direct approach...")
        try:
            # Directly get data about PancakeSwap and other known BSC DEXs
            known_bsc_dexs = [
                {"name": "PancakeSwap", "slug": "pancakeswap"},
                {"name": "BiSwap", "slug": "biswap"},
                {"name": "MDEX", "slug": "mdex"},
                {"name": "BabySwap", "slug": "babyswap"},
                {"name": "ApeSwap", "slug": "apeswap"},
                {"name": "PancakeBunny", "slug": "pancakebunny"}
            ]
            bsc_dexs = known_bsc_dexs
            print(f"Using {len(bsc_dexs)} known BSC DEXs")
        except Exception as e:
            print(f"Error with direct approach: {e}")
    
    # Save the list of DEXs
    with open(f"{output_dir}/bsc_dexs.json", "w") as f:
        json.dump(bsc_dexs, f, indent=2)
    
    # Create summary dataframe
    summary_data = []
    
    # 2. Process each DEX
    for dex in bsc_dexs:
        protocol_name = dex.get('name')
        protocol_slug = dex.get('slug')
        
        print(f"\nProcessing {protocol_name} ({protocol_slug})...")
        
        try:
            # 2.1 Fetch TVL data
            tvl_data = fetch_protocol_tvl(protocol_slug)
            if tvl_data:
                # Try different ways to get BSC TVL
                current_tvl = 0
                if 'currentChainTvls' in tvl_data:
                    for chain_key in ['BSC', 'bsc', 'binance', 'Binance', 'BNB Chain', 'BNB']:
                        if chain_key in tvl_data.get('currentChainTvls', {}):
                            chain_tvl = tvl_data.get('currentChainTvls', {}).get(chain_key, 0)
                            current_tvl = get_numeric_value(chain_tvl)
                            break
                
                # If still 0, use the total TVL
                if current_tvl == 0:
                    current_tvl = get_numeric_value(tvl_data.get('tvl', 0))
                
                print(f"Current TVL: ${current_tvl:,.2f}")
                
                # Save TVL data
                with open(f"{output_dir}/{protocol_slug}_tvl.json", "w") as f:
                    json.dump(tvl_data, f, indent=2)
            else:
                current_tvl = 0
            
            # 2.2 Fetch volume data
            volume_data = fetch_dex_volumes(protocol_slug)
            if volume_data:
                total_volume = get_numeric_value(volume_data.get('totalVolume', 0))
                volume_24h = get_numeric_value(volume_data.get('total24h', 0))
                volume_7d = get_numeric_value(volume_data.get('total7d', 0))
                volume_30d = get_numeric_value(volume_data.get('total30d', 0))
                
                print(f"Trading Volume (24h): ${volume_24h:,.2f}")
                print(f"Trading Volume (7d): ${volume_7d:,.2f}")
                print(f"Trading Volume (30d): ${volume_30d:,.2f}")
                print(f"Trading Volume (Total): ${total_volume:,.2f}")
                
                # Save volume data
                with open(f"{output_dir}/{protocol_slug}_volumes.json", "w") as f:
                    json.dump(volume_data, f, indent=2)
            else:
                volume_24h = volume_7d = volume_30d = total_volume = 0
            
            # 2.3 Fetch fee data
            fee_data = fetch_dex_fees(protocol_slug)
            if fee_data:
                fees_24h = get_numeric_value(fee_data.get('total24h', 0))
                fees_7d = get_numeric_value(fee_data.get('total7d', 0))
                fees_30d = get_numeric_value(fee_data.get('total30d', 0))
                
                revenue_24h = get_numeric_value(fee_data.get('revenue24h', 0))
                revenue_7d = get_numeric_value(fee_data.get('revenue7d', 0))
                revenue_30d = get_numeric_value(fee_data.get('revenue30d', 0))
                
                print(f"Fees (24h): ${fees_24h:,.2f}")
                print(f"Fees (7d): ${fees_7d:,.2f}")
                print(f"Fees (30d): ${fees_30d:,.2f}")
                
                print(f"Protocol Revenue (24h): ${revenue_24h:,.2f}")
                print(f"Protocol Revenue (7d): ${revenue_7d:,.2f}")
                print(f"Protocol Revenue (30d): ${revenue_30d:,.2f}")
                
                # Save fee data
                with open(f"{output_dir}/{protocol_slug}_fees.json", "w") as f:
                    json.dump(fee_data, f, indent=2)
            else:
                fees_24h = fees_7d = fees_30d = revenue_24h = revenue_7d = revenue_30d = 0
            
            # 2.4 Fetch top pools for this DEX
            top_pools = fetch_top_pools(protocol_name)
            if top_pools:
                print(f"Top Pools for {protocol_name}:")
                for i, pool in enumerate(top_pools[:5]):  # Show top 5
                    pool_name = pool.get('pool')
                    pool_tvl = get_numeric_value(pool.get('tvlUsd', 0))
                    print(f"  {i+1}. {pool_name} - TVL: ${pool_tvl:,.2f}")
                
                # Save top pools data
                with open(f"{output_dir}/{protocol_slug}_top_pools.json", "w") as f:
                    json.dump(top_pools[:20], f, indent=2)  # Save top 20
            
            # Add to summary data
            summary_data.append({
                'Protocol': protocol_name,
                'Slug': protocol_slug,
                'TVL': current_tvl,
                'Volume_24h': volume_24h,
                'Volume_7d': volume_7d,
                'Volume_30d': volume_30d,
                'Volume_Total': total_volume,
                'Fees_24h': fees_24h,
                'Fees_7d': fees_7d,
                'Fees_30d': fees_30d,
                'Revenue_24h': revenue_24h,
                'Revenue_7d': revenue_7d,
                'Revenue_30d': revenue_30d
            })
        except Exception as e:
            print(f"Error processing {protocol_name}: {e}")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    # Create summary DataFrame and save to CSV
    if summary_data:
        df = pd.DataFrame(summary_data)
        df.to_csv(f"{output_dir}/bsc_dexs_summary.csv", index=False)
        
        # Display summary
        print("\n--- BSC DEXs Summary ---")
        print(f"Total DEXs: {len(df)}")
        print(f"Total TVL: ${df['TVL'].sum():,.2f}")
        print(f"Total 24h Volume: ${df['Volume_24h'].sum():,.2f}")
        print(f"Top 5 DEXs by TVL:")
        for _, row in df.sort_values('TVL', ascending=False).head(5).iterrows():
            print(f"  {row['Protocol']}: ${row['TVL']:,.2f}")

if __name__ == "__main__":
    main()