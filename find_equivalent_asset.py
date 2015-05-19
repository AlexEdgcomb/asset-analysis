#asset_name_to_replace  = ['FDVLX']
#asset_names_to_compare = ['VTSMX', 'VTI', 'IYY', 'SCHB', 'FNDB', 'EZY']
'''
Possible replacements for FDVLX:
    VTSMX: r=0.959 across 5771 trade days
      VTI: r=0.988 across 3463 trade days
      IYY: r=0.956 across 3714 trade days
     SCHB: r=0.995 across 1355 trade days
     FNDB: r=0.989 across  404 trade days
      EZY: r=0.992 across 2035 trade days
'''

#asset_name_to_replace  = ['VUSTX']
#asset_names_to_compare = ['LAG', 'BND', 'AGG', 'SCHZ', 'GBF', 'HYLS', 'VMBS', 'MBG']
'''
Possible replacements for VUSTX:
      LAG: r=0.951 across 1969 trade days
      BND: r=0.952 across 2004 trade days
      AGG: r=0.974 across 2891 trade days
     SCHZ: r=0.833 across  929 trade days
      GBF: r=0.963 across 2064 trade days
     HYLS: r=0.423 across  522 trade days
     VMBS: r=0.942 across 1341 trade days
      MBG: r=0.933 across 1547 trade days
'''

asset_name_to_replace  = ['FEMKX']
asset_names_to_compare = ['VWO', 'SCHE', 'JPEM', 'EEM', 'HEEM', 'DEM']
'''
Possible replacements for FEMKX:
      VWO: r=0.933 across 2527 trade days
     SCHE: r=0.936 across 1306 trade days
     JPEM: r=0.775 across   51 trade days
      EEM: r=0.968 across 3007 trade days
     HEEM: r=0.850 across  124 trade days
      DEM: r=0.604 across 1938 trade days
'''

asset_names = asset_name_to_replace + asset_names_to_compare
assets = [None] * len(asset_names)

import asset
import load_assets
from scipy import stats

def main():
    global asset_names
    global assets
    
    assets = load_assets.load_assets(asset_names, assets)
    
    print 'Possible replacements for %s: ' % (assets[0].name)
    for index, asset in enumerate(assets):
        asset_to_replace = assets[0].days_adjusted_price
        
        if index != 0:
            possible_replacement = assets[index].days_adjusted_price
    
            min_number_of_adjusted_prices = min(len(asset_to_replace), len(possible_replacement))
    
            adjusted_price_of_asset_to_replace = []
            adjusted_price_of_possible_replacement = []
            for i in range(0, min_number_of_adjusted_prices):
                adjusted_price_of_asset_to_replace.append(asset_to_replace[i]['adjusted_price'])
                adjusted_price_of_possible_replacement.append(possible_replacement[i]['adjusted_price'])
    
            pearson_r, p_value = stats.pearsonr(adjusted_price_of_asset_to_replace, adjusted_price_of_possible_replacement)
            print '    %5s: r=%.3f across %4d trade days'% (assets[index].name, pearson_r, min_number_of_adjusted_prices)

if __name__ == "__main__":
    main()