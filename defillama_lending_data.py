import requests
import pandas as pd
import json
import time
import os

def fetch_lending_protocols(target_chain_name=None):
    """Fetch lending protocols from DeFiLlama, optionally filtered by chain"""
    url = "https://api.llama.fi/protocols"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching protocols: {response.status_code}")
        return []
    
    protocols = response.json()
    
    lending_protocols = []
    for p in protocols:
        category = p.get('category', '').lower()
        chains = [chain.lower() for chain in p.get('chains', [])]
        
        # Filter for lending protocols
        if 'lending' in category:
            # Apply chain filter if specified
            if target_chain_name:
                if target_chain_name.lower() in chains:
                    lending_protocols.append(p)
            else:
                lending_protocols.append(p)
    
    return lending_protocols

def fetch_protocol_tvl(protocol_slug, target_chain_name=None):
    """Fetch TVL data for a specific protocol"""
    url = f"https://api.llama.fi/protocol/{protocol_slug}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def get_numeric_value(value):
    """Convert value to a number if it's not already one"""
    if isinstance(value, (int, float)):
        return value
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

def main(target_chain=None):
    base_output_dir = "defillama_data"
    output_dir = os.path.join(base_output_dir, "lending")
    if target_chain:
        output_dir = os.path.join(output_dir, target_chain)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Fetch lending protocols
    lending_protocols = fetch_lending_protocols(target_chain)
    if not lending_protocols:
        print(f"No lending protocols found for {target_chain or 'all chains'}")
        return
    
    # Save the list of protocols found
    protocol_list_file = "lending_protocols_list.json"
    if target_chain:
        protocol_list_file = f"{target_chain}_lending_protocols_list.json"
    with open(os.path.join(output_dir, protocol_list_file), "w") as f:
        json.dump(lending_protocols, f, indent=2)
    
    # Process up to 5 protocols for testing (adjust as needed)
    protocols_to_process = lending_protocols[:5]
    
    summary_data = []
    
    for protocol_info in protocols_to_process:
        protocol_name = protocol_info.get('name')
        protocol_slug = protocol_info.get('slug')
        
        if not protocol_slug:
            continue
            
        current_tvl = 0
        current_tvl_on_chain = 0 if target_chain else 0
        
        try:
            # Fetch TVL data
            tvl_data = fetch_protocol_tvl(protocol_slug, target_chain)
            if tvl_data:
                if target_chain and 'currentChainTvls' in tvl_data:
                    for chain_name, chain_tvl in tvl_data.get('currentChainTvls', {}).items():
                        if chain_name.lower() == target_chain.lower():
                            current_tvl_on_chain = get_numeric_value(chain_tvl)
                
                # Get total TVL
                current_tvl = get_numeric_value(tvl_data.get('tvl', 0))
                
                # Save TVL data
                with open(os.path.join(output_dir, f"{protocol_slug}_tvl.json"), "w") as f:
                    json.dump(tvl_data, f, indent=2)
            
            # Add to summary data
            summary_data.append({
                'Protocol': protocol_name,
                'Slug': protocol_slug,
                'TVL': current_tvl,
                'TVL_on_Chain': current_tvl_on_chain if target_chain else current_tvl,
                'Total_Borrows': 0,  # We don't have this data
                'Total_Deposits': current_tvl_on_chain if target_chain else current_tvl,  # Using TVL as deposits
                'Markets_Count': 0  # We don't have market data
            })
            
        except Exception as e:
            print(f"Error processing {protocol_name}: {e}")
        
        time.sleep(1)  # Respect API rate limits
    
    # Create summary DataFrame and save to CSV
    if summary_data:
        df = pd.DataFrame(summary_data)
        summary_file = "lending_protocols_summary.csv"
        if target_chain:
            summary_file = f"{target_chain}_lending_protocols_summary.csv"
        df.to_csv(os.path.join(output_dir, summary_file), index=False)

if __name__ == "__main__":
    # Define the list of chains to process
    chains_to_process = [
        "Ethereum", 
        "BSC", 
        "Solana", 
        "Arbitrum", 
        "Polygon",
        "Berachain"
    ]
    
    # First run without chain filter to get aggregated data
    print("\n--- Processing all lending protocols across chains ---")
    main()
    
    # Then process each chain
    if chains_to_process:
        for chain_name in chains_to_process:
            print(f"\n--- Processing lending protocols on {chain_name} ---")
            main(chain_name)
    
    print("\nAll lending protocol data has been processed.") 