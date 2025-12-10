#!/usr/bin/env python3
"""
Generate Figure 2 from the ASM replication project.

This script requires:
- data/long.csv (from data_prep.py)
- data/figures/f2_time_plot.csv (from Stata regressions.do)

Output:
- data/figures/f2_summary.svg
"""

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import gridspec
import seaborn as sns
import numpy as np
import os
import re
try:
    from scipy.interpolate import make_interp_spline
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Set data directory
data_dir = './data/'

# Create figures directory if it doesn't exist
os.makedirs(data_dir + 'figures/', exist_ok=True)

# Color palette
palette = ['#CD6699', '#448970', '#F5CA7A']
palette = {'notleg': palette[2],
           'notbiom': palette[0],
           'soym': palette[1],
           'neutral': 'black'}

# Font settings
font = {'family': 'sans-serif',
        'weight': 'normal',
        'size': 16}
matplotlib.rc('font', **font)

print("Loading data...")
# Load main dataset
defor_csv = data_dir + 'long.csv'
defor_df = pd.read_csv(defor_csv)

# Filter to sample (same as Stata: dist_amb > -300, dist_aml < 300)
buffer = 300
sample_df = defor_df.loc[((defor_df['dist_amb'] > -300) & (defor_df['dist_aml'] < 300))]

print("Creating soy suitability variable...")
# Create soy suitability variable
sample_df.loc[:, 'gaez_soy_suit'] = (sample_df['GAEZsuit'] > 40).astype(int)
sample_df.loc[:, 'soy_suit'] = ((sample_df['gaez_soy_suit'] == 1) & (sample_df['suit'] > 0)).astype(int)
suit_var = 'soy_suit'

print("Calculating deforestation rates...")
# Calculate deforestation rates by group
out_var = 'mb2_vdefor'
defor = pd.pivot_table(sample_df, columns='year', index=[suit_var, 'biome', 'legal_amazon'], 
                       values=out_var, aggfunc='sum')
forest = pd.pivot_table(sample_df, columns='year', index=[suit_var, 'biome', 'legal_amazon'], 
                        values=out_var, aggfunc='count')
defor_shr = ((defor / forest) * 100).dropna(axis=1).T.loc[2002:2016]
defor_shr = defor_shr.T

print("Loading time plot data from Stata...")
# Function to clean time plot data from Stata
def clean_time(time_csv):
    """Parse the Stata esttab output CSV into a clean dataframe."""
    time_df = pd.read_csv(time_csv)
    time_df = time_df.iloc[1:-1]  # Remove first and last rows (header/footer)
    time_df.columns = ['var', 'estimate']
    time_df.loc[:, 'var'] = np.repeat(time_df['var'].dropna(), 2).values
    time_df.loc[:, 'stat'] = np.tile(['coef', 'ci'], int((time_df.shape[0]/2)))
    time_df = time_df.set_index(['stat', 'var'])
    time_df = time_df.unstack().T.reset_index()
    soy_rows = [var for var in time_df['var'] if (suit_var in var) & ('biome' in var) & ('year' in var)]
    df = time_df.loc[time_df['var'].isin(soy_rows)]
    df.loc[:, 'year'] = df['var'].apply(lambda x: int(x[:4]))
    df.loc[:, 'coef'] = df['coef'].apply(lambda x: float(x)) * 100
    df.loc[:, 'lb'] = df['ci'].apply(lambda x: float(x.split(',')[0])) * 100
    df.loc[:, 'ub'] = df['ci'].apply(lambda x: float(x.split(',')[1])) * 100
    df.loc[:, 'err'] = df.loc[:, 'coef'] - df.loc[:, 'lb']
    return df

# Load time plot data
time_csv = data_dir + 'figures/f2_time_plot.csv'
if not os.path.exists(time_csv):
    raise FileNotFoundError(f"Time plot data not found: {time_csv}\n"
                           f"Please run the Stata code to generate this file first.")

soytime_df = clean_time(time_csv)

print("Creating Figure 2...")
# Create figure with 3 panels
gs = gridspec.GridSpec(3, 1, height_ratios=[2, 2, 1.5]) 
fig = plt.figure(figsize=(8, 12))
ax2 = plt.subplot(gs[2])
ax0 = plt.subplot(gs[0])
ax1 = plt.subplot(gs[1], sharex=ax0, sharey=ax0)

# Panel A: Outside soy-suitable forests
# Index format: (soy_suit, biome, legal_amazon)
ax0.plot(defor_shr.columns, defor_shr.loc[(0, 0, 0)], color=palette['notleg'], linestyle='-', label='Cerrado, not legal Amazon')
ax0.plot(defor_shr.columns, defor_shr.loc[(0, 0, 1)], color=palette['notbiom'], linestyle='-', label='Cerrado, legal Amazon')
ax0.plot(defor_shr.columns, defor_shr.loc[(0, 1, 1)], color=palette['soym'], linestyle='-', label='Amazon, legal Amazon')

# Panel B: Within soy-suitable forests
ax1.plot(defor_shr.columns, defor_shr.loc[(1, 0, 0)], color=palette['notleg'], linestyle='-')
ax1.plot(defor_shr.columns, defor_shr.loc[(1, 0, 1)], color=palette['notbiom'], linestyle='-')
ax1.plot(defor_shr.columns, defor_shr.loc[(1, 1, 1)], color=palette['soym'], linestyle='-')

# Panel C: Time-varying treatment effect
ax2.plot(soytime_df['year'].values, soytime_df['coef'].values, color='black', linewidth=2)
ax2.fill_between(soytime_df['year'], soytime_df['lb'], soytime_df['ub'], 
                 alpha=0.5, facecolor='grey', interpolate=False)

# Formatting
sns.despine()
handles = [plt.Line2D(range(10), range(10), linestyle='-', color=palette['notleg'], linewidth=2),
           plt.Line2D(range(10), range(10), linestyle='-', color=palette['notbiom'], linewidth=2),
           plt.Line2D(range(10), range(10), linestyle='-', color=palette['soym'], linewidth=2)]
labels = ['Cerrado biome, not legal Amazon', 'Cerrado biome, legal Amazon', 'Amazon biome, legal Amazon']

ax0.set_ylabel('Deforestation rate outside\nsoy-suitable forests (%/y)')
ax1.set_ylabel('Deforestation rate within\nsoy-suitable forests (%/y)')
ax2.set_xlabel('Year')
ax2.set_ylabel('Time varying treatment effect\n(percentage point)')

# Add vertical lines at 2006 (policy implementation)
ax0.axvline(x=2006, color='grey', linestyle='--', linewidth=1)
ax1.axvline(x=2006, color='grey', linestyle='--', linewidth=1)
ax2.axvline(x=2006, color='grey', linestyle='--', linewidth=1)
ax2.axhline(y=0, color='grey', linestyle='--', linewidth=1)

ax0.set_xticklabels([])
ax1.set_xticklabels([])
ax0.set_ylim((0, 3.8))

# Add panel labels
ax0.annotate("A", xy=(2015, 3.5), fontsize=14, fontweight='bold')
ax1.annotate("B", xy=(2015, 3.5), fontsize=14, fontweight='bold')
ax2.annotate("C", xy=(2015, 0.6), fontsize=14, fontweight='bold')

# Add legends
lgd = ax0.legend(handles, labels, fontsize=10, frameon=False, loc='lower left', bbox_to_anchor=(0.5, 0.6))
lgd = ax1.legend(handles, labels, fontsize=10, frameon=False, loc='lower left', bbox_to_anchor=(0.5, 0.6))

fig.tight_layout()

# Save figure
output_path = data_dir + 'figures/f2_summary.svg'
fig.savefig(output_path)
print(f"Figure 2 saved to: {output_path}")

# Also save as PNG for easier viewing
output_path_png = data_dir + 'figures/f2_summary.png'
fig.savefig(output_path_png, dpi=300)
print(f"Figure 2 (PNG) saved to: {output_path_png}")

plt.show()

# ---------------------------------------------------------------------------
# Additional plot: soy-suitable vs non-suitable differences (three lines)
# Simply compute differences from the Figure 2 data
# ---------------------------------------------------------------------------
print("Creating soy-suitability difference plot from Figure 2 data...")

# Compute differences: soy-suitable (soy_suit=1) minus non-suitable (soy_suit=0)
# Index format: (soy_suit, biome, legal_amazon)
diff_series = {}
groups = {
    "Cerrado, not legal Amazon": (0, 0),  # biome=0, legal_amazon=0
    "Cerrado, legal Amazon": (0, 1),      # biome=0, legal_amazon=1
    "Amazon, legal Amazon": (1, 1),      # biome=1, legal_amazon=1
}

for label, (biome, legal) in groups.items():
    try:
        # (soy_suit=1) minus (soy_suit=0) for this biome/legal combination
        diff_series[label] = defor_shr.loc[(1, biome, legal)] - defor_shr.loc[(0, biome, legal)]
    except KeyError:
        print(f"Warning: Could not find data for {label} (biome={biome}, legal={legal})")
        continue

if diff_series:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = {
        'Cerrado, not legal Amazon': palette['notleg'],
        'Cerrado, legal Amazon': palette['notbiom'],
        'Amazon, legal Amazon': palette['soym']
    }
    
    # Plot in order: not legal, Cerrado legal, Amazon legal
    plot_order = ["Cerrado, not legal Amazon", "Cerrado, legal Amazon", "Amazon, legal Amazon"]
    for label in plot_order:
        if label in diff_series:
            series = diff_series[label]
            color = colors.get(label, 'grey')
            
            # Sort by index (year)
            series_sorted = series.sort_index()
            years = series_sorted.index.values
            values = series_sorted.values
            
            # Create smoother line using interpolation
            if HAS_SCIPY and len(years) > 3:  # Need at least 3 points for spline
                years_smooth = np.linspace(years.min(), years.max(), 300)
                spline = make_interp_spline(years, values, k=min(3, len(years)-1))
                values_smooth = spline(years_smooth)
                ax.plot(years_smooth, values_smooth, 
                       label=label, linewidth=2.5, color=color, linestyle='-', alpha=0.8)
                # Add markers at original data points
                ax.scatter(years, values, color=color, s=30, zorder=5, alpha=0.7)
            else:
                # Fallback to regular plot with smooth appearance
                ax.plot(years, values, label=label, linewidth=2.5, 
                       color=color, marker='o', markersize=4, linestyle='-', alpha=0.8, antialiased=True)
    
    ax.axhline(y=0, color='grey', linestyle='--', linewidth=1)
    ax.axvline(x=2006, color='grey', linestyle='--', linewidth=1)
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Soy-suitable minus non-suitable\ndeforestation rate (pp)', fontsize=14)
    ax.set_title('Difference: soy-suitable vs non-suitable', fontsize=16, fontweight='bold')
    ax.legend(frameon=False, fontsize=12)
    ax.set_xlim(2002, 2016)
    sns.despine()
    fig.tight_layout()
    
    out_diff_svg = data_dir + 'figures/f2_soy_diff.svg'
    out_diff_png = data_dir + 'figures/f2_soy_diff.png'
    fig.savefig(out_diff_svg)
    fig.savefig(out_diff_png, dpi=300)
    print(f"Soy-suitability difference plot saved to: {out_diff_svg}")
    print(f"Soy-suitability difference plot (PNG) saved to: {out_diff_png}")
else:
    print("Error: Could not compute any difference series")
