import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from pathlib import Path

def load_data(output_dir="defillama_data"):
    """Load the summary data and return a DataFrame"""
    csv_path = os.path.join(output_dir, "bsc_dexs_summary.csv")
    if not os.path.exists(csv_path):
        print(f"Summary data not found at {csv_path}")
        return None
    
    return pd.read_csv(csv_path)

def plot_top_dexs_by_tvl(df, n=10, output_dir="defillama_data"):
    """Plot top DEXs by TVL"""
    plt.figure(figsize=(12, 8))
    
    # Sort by TVL and take top n
    df_sorted = df.sort_values('TVL', ascending=False).head(n)
    
    # Create bar plot
    sns.barplot(x='TVL', y='Protocol', data=df_sorted)
    
    plt.title(f'Top {n} BSC DEXs by TVL (USD)')
    plt.xlabel('TVL (USD)')
    plt.ylabel('DEX Protocol')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.ticklabel_format(style='plain', axis='x')
    
    # Format x-axis with billions/millions
    current_values = plt.gca().get_xticks()
    plt.gca().set_xticklabels(['${:,.0f}'.format(x) for x in current_values])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "top_dexs_by_tvl.png"))
    plt.close()
    
    print(f"Created chart: top_dexs_by_tvl.png")

def plot_volume_comparison(df, n=10, output_dir="defillama_data"):
    """Plot volume comparison (24h, 7d, 30d) for top DEXs by 24h volume"""
    plt.figure(figsize=(14, 10))
    
    # Sort by 24h volume and take top n
    df_sorted = df.sort_values('Volume_24h', ascending=False).head(n)
    
    # Melt the dataframe to convert to long format for grouped bar chart
    df_melted = pd.melt(df_sorted, 
                        id_vars=['Protocol'], 
                        value_vars=['Volume_24h', 'Volume_7d', 'Volume_30d'],
                        var_name='Time Period',
                        value_name='Volume')
    
    # Format the time period labels
    df_melted['Time Period'] = df_melted['Time Period'].map({
        'Volume_24h': '24h',
        'Volume_7d': '7d',
        'Volume_30d': '30d'
    })
    
    # Create grouped bar plot
    sns.barplot(x='Protocol', y='Volume', hue='Time Period', data=df_melted)
    
    plt.title(f'Trading Volume Comparison for Top {n} BSC DEXs')
    plt.xlabel('DEX Protocol')
    plt.ylabel('Volume (USD)')
    plt.yscale('log')  # Log scale for better visualization
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend(title='Time Period')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "volume_comparison.png"))
    plt.close()
    
    print(f"Created chart: volume_comparison.png")

def plot_fees_to_volume_ratio(df, output_dir="defillama_data"):
    """Plot fees to volume ratio for DEXs (measures efficiency/cost)"""
    plt.figure(figsize=(12, 8))
    
    # Calculate fees as percentage of volume
    df = df.copy()
    # Filter to exclude ones with zero volume to avoid division by zero
    df = df[df['Volume_24h'] > 0]
    df['Fee_Percentage'] = (df['Fees_24h'] / df['Volume_24h']) * 100
    
    # Sort by fee percentage
    df_sorted = df.sort_values('Fee_Percentage').head(15)
    
    # Create bar plot
    sns.barplot(x='Fee_Percentage', y='Protocol', data=df_sorted)
    
    plt.title('Fees as Percentage of 24h Trading Volume')
    plt.xlabel('Fee Percentage (%)')
    plt.ylabel('DEX Protocol')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fee_to_volume_ratio.png"))
    plt.close()
    
    print(f"Created chart: fee_to_volume_ratio.png")

def analyze_top_pools(output_dir="defillama_data"):
    """Analyze and visualize top liquidity pools across DEXs"""
    # Get all top pools files
    pools_files = list(Path(output_dir).glob("*_top_pools.json"))
    
    all_pools = []
    for file_path in pools_files:
        protocol_slug = file_path.stem.replace("_top_pools", "")
        try:
            with open(file_path, 'r') as f:
                pools = json.load(f)
                for pool in pools:
                    pool['protocol_slug'] = protocol_slug
                    all_pools.append(pool)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    if not all_pools:
        print("No pool data found!")
        return
    
    # Convert to DataFrame
    pools_df = pd.DataFrame(all_pools)
    
    # Top 20 pools by TVL across all DEXs
    plt.figure(figsize=(14, 10))
    
    # Sort by TVL and take top 20
    top_pools = pools_df.sort_values('tvlUsd', ascending=False).head(20)
    
    # Create bar plot
    sns.barplot(x='tvlUsd', y='pool', data=top_pools)
    
    plt.title('Top 20 Liquidity Pools by TVL across BSC DEXs')
    plt.xlabel('TVL (USD)')
    plt.ylabel('Pool')
    plt.ticklabel_format(style='plain', axis='x')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    
    # Format x-axis with millions
    current_values = plt.gca().get_xticks()
    plt.gca().set_xticklabels(['${:,.0f}'.format(x) for x in current_values])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "top_pools_by_tvl.png"))
    plt.close()
    
    print(f"Created chart: top_pools_by_tvl.png")
    
    # Return data for further analysis
    return pools_df

def main():
    output_dir = "defillama_data"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = load_data(output_dir)
    if df is None:
        print("Please run defillama_bsc_dex_data.py first to collect the data.")
        return
    
    print(f"Loaded data for {len(df)} DEX protocols")
    
    # Create visualizations
    plot_top_dexs_by_tvl(df, output_dir=output_dir)
    plot_volume_comparison(df, output_dir=output_dir)
    plot_fees_to_volume_ratio(df, output_dir=output_dir)
    
    # Analyze top pools
    analyze_top_pools(output_dir=output_dir)
    
    print("\nAll visualizations have been created in the 'defillama_data' directory.")

if __name__ == "__main__":
    main() 