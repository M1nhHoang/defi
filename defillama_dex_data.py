import requests
import pandas as pd
import json
from datetime import datetime
import time
import os
import sys

def fetch_protocols_on_chain(target_chain_name):
    """Fetch DEX-like protocols on a specific chain from DeFiLlama"""
    url = "https://api.llama.fi/protocols"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching protocols: {response.status_code}")
        return []
    
    protocols = response.json()
    
    target_chain_protocols = []
    for p in protocols:
        category = p.get('category', '').lower()
        chains = [chain.lower() for chain in p.get('chains', [])]
        
        if any(dex_term in category for dex_term in ['dexes', 'dex', 'exchange']):
            if target_chain_name.lower() in chains:
                target_chain_protocols.append(p)
    
    return target_chain_protocols

def fetch_protocol_tvl(protocol_slug, target_chain_name):
    """Fetch TVL data for a specific protocol"""
    url = f"https://api.llama.fi/protocol/{protocol_slug}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def fetch_dex_volumes(protocol_slug):
    """Fetch volume data for a specific protocol"""
    url = f"https://api.llama.fi/summary/dexs/{protocol_slug}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyVolume"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def fetch_dex_fees(protocol_slug):
    """Fetch fee data for a specific protocol"""
    url = f"https://api.llama.fi/summary/fees/{protocol_slug}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def fetch_top_pools(protocol_slug, target_chain_name):
    """Fetch top liquidity pools, filtered by protocol slug and chain name"""
    url = "https://yields.llama.fi/pools"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    
    all_pools = response.json().get('data', [])
    
    filtered_pools = []
    for p in all_pools:
        if p.get('project', '').lower() == protocol_slug.lower() and \
           p.get('chain', '').lower() == target_chain_name.lower():
            filtered_pools.append(p)
            
    filtered_pools = sorted(filtered_pools, key=lambda x: x.get('tvlUsd', 0), reverse=True)
    return filtered_pools

def get_numeric_value(value):
    """Convert value to a number if it's not already one"""
    if isinstance(value, (int, float)):
        return value
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

def main(target_chain):
    base_output_dir = "defillama_data"
    output_dir = os.path.join(base_output_dir, target_chain)
    os.makedirs(output_dir, exist_ok=True)
    
    chain_protocols = fetch_protocols_on_chain(target_chain)
    
    protocols_to_process = chain_protocols[:5] 
    if not protocols_to_process:
        return
        
    with open(os.path.join(output_dir, f"{target_chain}_protocols_list.json"), "w") as f:
        json.dump(protocols_to_process, f, indent=2)
    
    summary_data = []
    
    for protocol_info in protocols_to_process:
        protocol_name = protocol_info.get('name')
        protocol_slug = protocol_info.get('slug')
        
        if not protocol_slug:
            continue
            
        current_tvl_on_chain = 0
        volume_24h = volume_7d = volume_30d = total_volume = 0
        fees_24h = fees_7d = fees_30d = 0
        revenue_24h = revenue_7d = revenue_30d = 0
        
        try:
            tvl_data_full = fetch_protocol_tvl(protocol_slug, target_chain)
            if tvl_data_full:
                chain_tvls_map = tvl_data_full.get('currentChainTvls', {})
                if target_chain in chain_tvls_map:
                    current_tvl_on_chain = get_numeric_value(chain_tvls_map.get(target_chain, 0))
                
                if current_tvl_on_chain == 0:
                    historical_tvl_list = tvl_data_full.get('tvl', [])
                    if isinstance(historical_tvl_list, list) and len(historical_tvl_list) > 0:
                        last_tvl_record = historical_tvl_list[-1]
                        if isinstance(last_tvl_record, dict):
                            current_tvl_on_chain = get_numeric_value(last_tvl_record.get('totalLiquidityUSD', 0))
                    elif isinstance(historical_tvl_list, (int, float)):
                        current_tvl_on_chain = get_numeric_value(historical_tvl_list)
                
                with open(os.path.join(output_dir, f"{protocol_slug}_tvl.json"), "w") as f:
                    json.dump(tvl_data_full, f, indent=2)
            
            volume_data = fetch_dex_volumes(protocol_slug)
            if volume_data:
                total_volume = get_numeric_value(volume_data.get('totalVolume', 0))
                volume_24h = get_numeric_value(volume_data.get('total24h', 0))
                volume_7d = get_numeric_value(volume_data.get('total7d', 0))
                volume_30d = get_numeric_value(volume_data.get('total30d', 0))
                
                with open(os.path.join(output_dir, f"{protocol_slug}_volumes.json"), "w") as f:
                    json.dump(volume_data, f, indent=2)
            
            fee_data = fetch_dex_fees(protocol_slug)
            if fee_data:
                fees_24h = get_numeric_value(fee_data.get('total24h', 0))
                fees_7d = get_numeric_value(fee_data.get('total7d', 0))
                fees_30d = get_numeric_value(fee_data.get('total30d', 0))
                
                revenue_24h = get_numeric_value(fee_data.get('totalRevenue24h', fee_data.get('revenue24h', 0)))
                revenue_7d = get_numeric_value(fee_data.get('totalRevenue7d', fee_data.get('revenue7d', 0)))
                revenue_30d = get_numeric_value(fee_data.get('totalRevenue30d', fee_data.get('revenue30d', 0)))
                
                with open(os.path.join(output_dir, f"{protocol_slug}_fees.json"), "w") as f:
                    json.dump(fee_data, f, indent=2)
            
            top_pools_data = fetch_top_pools(protocol_slug, target_chain)
            if top_pools_data:
                with open(os.path.join(output_dir, f"{protocol_slug}_top_pools.json"), "w") as f:
                    json.dump(top_pools_data[:20], f, indent=2)
            
            summary_data.append({
                'Protocol': protocol_name,
                'Slug': protocol_slug,
                f'TVL_on_{target_chain.replace(" ", "_")}': current_tvl_on_chain,
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
            pass
        
        time.sleep(1)
    
    if summary_data:
        df = pd.DataFrame(summary_data)
        summary_csv_path = os.path.join(output_dir, f"{target_chain}_protocols_summary.csv")
        df.to_csv(summary_csv_path, index=False)

if __name__ == "__main__":
    # Define the list of chains you want to process
    chains_to_process = [
        "Ethereum", 
        "BSC", 
        "Solana", 
        "Arbitrum", 
        "Polygon",
        "Berachain"
    ]

    if not chains_to_process:
        print("No chains defined in 'chains_to_process' list. Exiting.")
    else:
        print(f"Starting processing for the following chains: {', '.join(chains_to_process)}")
        for chain_name in chains_to_process:
            print(f"\n--- Processing chain: {chain_name} ---")
            main(chain_name)
            print(f"--- Finished processing for chain: {chain_name} ---")
        print("\nAll specified chains have been processed.")