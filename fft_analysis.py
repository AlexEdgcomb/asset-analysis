from scipy.fftpack import fft
import numpy as np

import asset
import load_assets

# List of assets to include in backtest
asset_names = ['VTI', 'TLT', 'EEM', 'VGSIX'] # Index funds to replace above

# List of ETF classes built before backtest
assets = []

def main():
    global asset_names
    global assets
    
    assets = load_assets.load_assets(asset_names)
    
    adjusted_prices_ffts = []
    for asset in assets:
        adjusted_prices = []
        for adjusted_price in asset.days_adjusted_price:
            adjusted_prices.append(adjusted_price['adjusted_price'])
        
        # Make sure adjusted_prices is even
        if (len(adjusted_prices) % 2) == 1:
            adjusted_prices.pop()
        
        adjusted_prices_fft = fft(adjusted_prices)
        adjusted_prices_fft = np.abs(adjusted_prices_fft[0:len(adjusted_prices_fft) / 2])
        adjusted_prices_ffts.append(adjusted_prices_fft)
    
    asset_fft_output = ''
    for index, adjusted_prices_fft in enumerate(adjusted_prices_ffts):
        asset_fft_output = assets[index].name + ','
        for fft_element in adjusted_prices_fft:
            asset_fft_output += '%f,' % (fft_element)
        
        print asset_fft_output

if __name__ == "__main__":
    main()