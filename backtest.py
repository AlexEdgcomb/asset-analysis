from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import math

import asset
import load_assets

# List of assets to include in backtest
#asset_names = ['FDVLX', 'VUSTX', 'FEMKX', 'VGSIX'] # Mutual funds: Stock, bond, emerging market, reit
asset_names = ['VTI', 'TLT', 'EEM', 'VGSIX'] # Index funds to replace above
#asset_names = ['IWV', 'VGLT', 'VWO', 'VNQ'] # Alternative index funds

#asset_names = ['VTSAX', 'VBLTX', 'VWO', 'VGSLX'] # Index funds that are through Ubiquity

# Number of trade days to include when computing merit
number_of_trade_days_for_computing_merit = 65

# Value must be an integer that is divisible by 12 without remain. Ex: 1, 2, 3, 4, 6, 12.
number_of_months_between_trades = 1
interval_till_next_trade        = relativedelta(months=number_of_months_between_trades)

# List of ETF classes built before backtest
assets = []

# |preferred_state_date| is optional and a string of a date: year-month-day
def get_earliest_possible_start_date_for_first_of_year(preferred_state_date='1900-01-1', print_earliest_start_date_of_each_asset=False):
    global assets
    global number_of_trade_days_for_computing_merit
    
    # Find earliest possible start date among all assets
    latest_start_date = datetime.strptime(preferred_state_date, '%Y-%m-%d')
    for asset in assets:
        asset_earliest_date = asset.days_adjusted_price[-1 * number_of_trade_days_for_computing_merit]['date']
        
        if print_earliest_start_date_of_each_asset:
            print '%s,%s' % (asset.name, asset_earliest_date)
        
        if asset_earliest_date > latest_start_date:
            latest_start_date = asset_earliest_date
    
    # If latest_start_date is not the first of the year, then go to the next first of the year
    if not((latest_start_date.day == 1) and (latest_start_date.month == 1)):
        latest_start_date = latest_start_date.replace(day=1, month=1)
        latest_start_date = latest_start_date + relativedelta(years=1)
    
    return latest_start_date

'''
    |max_loss_percentage_allowed| is the max percentage loss allowed.
    If the max loss percentage is met or exceed, then sell immediately instead of waiting until the |end_trade_day|.
    |max_loss_percentage_allowed| is optional and a number.
    
    |show_max_loss_percentage| as True will show the biggest loss percentage in a month.
'''
max_loss_percentage_of_day_vs_start_of_month = 1.0
def compute_gain_between_two_days(asset, start_trade_day, end_trade_day, max_loss_percentage_allowed=0.0, show_max_loss_percentage=False):
    global max_loss_percentage_of_day_vs_start_of_month
    
    start_adjusted_price = None
    end_adjusted_price   = None
    for day in reversed(asset.days_adjusted_price):
        if start_adjusted_price == None:
            if day['date'] == start_trade_day:
                found_start_date = True
                start_adjusted_price = day['adjusted_price']
        else:
            # Determine the max loss percentage on a given day vs the first of the month.
            # The use is for psychological reasons, so the investor knows how low max loss may go.
            if show_max_loss_percentage:
                loss_percentage_of_day_vs_start_of_month = day['adjusted_price'] / start_adjusted_price
                if loss_percentage_of_day_vs_start_of_month < max_loss_percentage_of_day_vs_start_of_month:
                    max_loss_percentage_of_day_vs_start_of_month = loss_percentage_of_day_vs_start_of_month
                    print 'Max loss %.2f on %s' % (max_loss_percentage_of_day_vs_start_of_month, day['date'])
            
            if day['adjusted_price'] <= (start_adjusted_price * max_loss_percentage_allowed):
                end_adjusted_price = day['adjusted_price']
                break
            
            if day['date'] == end_trade_day:
                end_adjusted_price = day['adjusted_price']
                break
    
    if (start_adjusted_price == None) or (end_adjusted_price == None):
        return None
    
    gain = 1.0 + ((end_adjusted_price - start_adjusted_price) / start_adjusted_price)
    
    return gain

'''
    |print_monthly_gain| as True will print the monthly gain.
    |threshold_to_use_cash_if_merits_under| is a number. If all asset merits are under this threshold, then just use cash for a gain of 1.0.
'''
def get_gain_between_trades(first_of_month, print_monthly_gain=False, threshold_to_use_cash_if_merits_under=float('-inf'), print_all_assets=False, allocate_by_merit=False, include_inverse_assets=False):
    global assets
    global number_of_trade_days_for_computing_merit
    
    first_trade_day_of_month      = assets[0].get_first_trade_of_month(first_of_month)
    next_first_trade_day_of_month = assets[0].get_first_trade_of_month(first_of_month + interval_till_next_trade)
    
    # If the next trade day doesn't exist, then not enough data, so stop
    if next_first_trade_day_of_month == None:
        return None
    
    # Compute merit and gains for each asset
    asset_by_merit = []
    date_not_found = False
    for asset in assets:
        merit = asset.get_merit(first_trade_day_of_month, number_of_trade_days_for_computing_merit)
        
        # If no merit computed, then not enough data, so stop
        if (merit == None):
            date_not_found = True
            return None
        else:
            gain = compute_gain_between_two_days(asset, first_trade_day_of_month, next_first_trade_day_of_month, max_loss_percentage_allowed=0.8)
            
            is_inverse = False
            if include_inverse_assets:
                if merit < 0:
                    is_inverse = True
                    merit = -1.0 * merit
                    gain  = 2.0 - gain
            
            asset_by_merit.append({
                'merit':      merit,
                'class':      asset,
                'gain':       gain,
                'is_inverse': is_inverse
            })

    if print_all_assets:
        all_asset_output = ''
        for asset in asset_by_merit:
            all_asset_output += '%s,%.2f,%.2f,,' % (asset['class'].name, asset['merit'], asset['gain'])
        print all_asset_output

    # Sort ETFs from highest to lowest merit
    asset_by_merit = sorted(asset_by_merit, key=lambda k: k['merit'], reverse=True)

    gain = 0.0
    if allocate_by_merit:
        total_merit = 0.0
        for asset in asset_by_merit:
            if asset['merit'] > 0:
                total_merit += asset['merit']
        
        if total_merit == 0.0:
            gain = 1.0
        else:
            for asset in asset_by_merit:
                if asset['merit'] > 0:
                    gain += asset['gain'] * (asset['merit'] / total_merit)
    else:
        base_asset_name = ''
        if asset_by_merit[0]['merit'] > threshold_to_use_cash_if_merits_under:
            gain = asset_by_merit[0]['gain']
            base_asset_name = asset_by_merit[0]['class'].name
        else:
            gain = 1.0
            base_asset_name = 'cash'
    
        if print_monthly_gain:
            if asset_by_merit[0]['is_inverse']:
                base_asset_name = 'i' + base_asset_name
            print '%d/%d,gain,%.2f,%s' % (first_trade_day_of_month.month, first_trade_day_of_month.year, gain, base_asset_name)
            
    return gain
    
def get_gain_for_year(first_of_year):
    first_of_month = first_of_year
    
    number_of_trades_per_year = 12 / number_of_months_between_trades
    
    total_gain = 1.0
    for month in range(number_of_trades_per_year):
        gain = get_gain_between_trades(first_of_month)
        
        if gain == None:
            return None
        
        total_gain     = total_gain * gain
        first_of_month = first_of_month + interval_till_next_trade
        
    return total_gain

def get_compound_annual_growth_rate(start_price, end_price, number_of_years):
    return 100.0 * (math.pow((end_price / start_price), (1.0 / number_of_years)) - 1.0)

# Compute each years gain starting from earliest possible first of year
def backtest_assets():
    number_of_years = 0
    start_gain = 1.0
    five_year_start_gain = start_gain
    end_gain = start_gain
    five_years = 5
    
    first_of_month = get_earliest_possible_start_date_for_first_of_year()
    
    while True:
        gain = get_gain_for_year(first_of_month)
        
        if gain == None:
            break
        else:
            print '%d,gain,%f' % (first_of_month.year, gain)
            
            # Every 5 years, print the CAGR of the last 5 years
            end_gain = end_gain * gain
            if (number_of_years % five_years) == (five_years - 1):
                print '5 year CAGR,,%f%%' % get_compound_annual_growth_rate(five_year_start_gain, end_gain, five_years)
                print ''
                five_year_start_gain = end_gain
            
            first_of_month = first_of_month + relativedelta(years=1)
            number_of_years += 1
    
    print ''
    print 'Total CAGR,,%.1f%%' % get_compound_annual_growth_rate(start_gain, end_gain, number_of_years)

def compute_merit_of_assets_yesterday():
    _yd = date.today() - timedelta(days=1)
    yesterday = datetime.strptime('%s-%s-%s'%(_yd.year, _yd.month, _yd.day), '%Y-%m-%d')
    print yesterday
    for asset in assets:
        print asset.name, asset.get_merit(yesterday, number_of_trade_days_for_computing_merit)

def main():
    global asset_names
    global assets
    
    assets = load_assets.load_assets(asset_names)
    #backtest_assets()
    compute_merit_of_assets_yesterday()

if __name__ == "__main__":
    main()
