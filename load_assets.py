import threading
import csv
import urllib2
import StringIO

import asset

def convert_asset_raw_data_to_list(asset_raw_data):
    # Convert asset_raw_data to CSV format
    asset_raw_data_file = StringIO.StringIO(asset_raw_data)
    asset_data_reader   = csv.reader(asset_raw_data_file, delimiter=',')
    
    # Convert CSV format to list
    asset_data_list     = []
    for asset_data in asset_data_reader:
        asset_data_list.append(asset_data)
    
    return asset_data_list

def convert_asset_data_list_to_asset_class(asset_data_list, asset_name):
    asset_class = asset.Asset(asset_name)
    
    for asset_data in asset_data_list:
        date                   = asset_data[0]
        adjusted_closing_price = asset_data[6]

        # Skip the headers
        if not(date == 'Date'):
            asset_class.add_day(date, adjusted_closing_price)
    
    return asset_class

# Download ETF data and build class for asset_name
# Then store in global assets at given index
def load_asset(asset_name, index, assets):
    # URL for dividend downloading: http://real-chart.finance.yahoo.com/table.csv?s=SHY&g=v&ignore=.csv
    asset_raw_data  = urllib2.urlopen('http://real-chart.finance.yahoo.com/table.csv?s=' + asset_name + '&ignore=.csv')
    asset_data_list = convert_asset_raw_data_to_list(asset_raw_data.read())
    asset_class     = convert_asset_data_list_to_asset_class(asset_data_list, asset_name)
    assets[index]   = asset_class

# Uses multi-threading to parallelize downloads and asset class processing
def load_assets(asset_names):
    assets = [None] * len(asset_names)
    
    thread_list = []
    for index, asset_name in enumerate(asset_names):
        thread = threading.Thread(target=load_asset, args=(asset_name, index, assets))
        thread_list.append(thread)
    
    for thread in thread_list:
        thread.start()
    
    for thread in thread_list:
        thread.join()
    
    return assets