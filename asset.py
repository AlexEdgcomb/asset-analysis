import numpy
from scipy import stats
from scipy.interpolate import interp1d
import math
from datetime import datetime, date, time

class Asset:
    def __init__(self, name):
        self.name = name
        self.days_adjusted_price = []
        
    def add_day(self, date, adjusted_closing_price):
        self.days_adjusted_price.append({
            'date':           datetime.strptime(date, '%Y-%m-%d'),
            'adjusted_price': float(adjusted_closing_price)
        })
    
    def get_first_trade_of_month(self, desired_trade_date):
        index = 0
        while desired_trade_date < self.days_adjusted_price[index]['date']:
            index += 1
        
        # If desired_trade_date was a trading day, then use desired_trade_date
        if desired_trade_date == self.days_adjusted_price[index]['date']:
            return desired_trade_date
        # If index is 0 and desired_trade_date not found, then the date isn't a trade date
        elif index == 0:
            return None
        # Otherwise, use the next trading day after desired_trade_date
        else:
            return self.days_adjusted_price[index - 1]['date']
    
    def get_twelth_trade_of_month(self, first_trade_date_of_month):
        index = 0
        while first_trade_date_of_month < self.days_adjusted_price[index]['date']:
            index += 1
        
        # If desired_trade_date was a trading day, then use desired_trade_date
        if first_trade_date_of_month == self.days_adjusted_price[index]['date']:
            return self.days_adjusted_price[index - 11]['date']
        # If index is 0 and desired_trade_date not found, then the date isn't a trade date
        elif index == 0:
            return None
        # Otherwise, use the next trading day after desired_trade_date
        else:
            return self.days_adjusted_price[index - 12]['date']
    
    def find_date_index_in_adjusted_prices(self, date):
        date_index = None
        for index, adjusted_price in enumerate(self.days_adjusted_price):
            if adjusted_price['date'] == date:
                date_index = index
                break
        return date_index
    
    # |start_value_type| can be either 'date' or 'index'. If 'date', then compute the start_date_index. If 'index', then start from that index.
    def get_adjusted_prices_in_range(self, start_value, number_of_days_to_go_back, start_value_type='date'):
        # Find start date in self.days_adjusted_price
        start_date_index = None
        if start_value_type == 'date':
            start_date_index = self.find_date_index_in_adjusted_prices(start_value)
        elif start_value_type == 'index':
            start_date_index = start_value
        
        # start_date not found
        if start_date_index == None:
            return None
        
        end_date_index = start_date_index + number_of_days_to_go_back
        
        # If end_date does not exist
        if end_date_index >= len(self.days_adjusted_price):
            return None
        
        # Build list of ajusted_prices from the start_date and for number_of_days_to_go_back
        adjusted_prices = []
        for index in range(start_date_index, end_date_index):
            adjusted_prices.append(self.days_adjusted_price[index]['adjusted_price'])
        
        return adjusted_prices
    
    def compute_exponential_moving_average(self, adjusted_prices, scaling_factor=0.0):
        sum = 0.0
        for index, price in enumerate(adjusted_prices):
            sum += price * pow(1 - scaling_factor, index)
        return sum / len(adjusted_prices)
    
    # start_date is a datetime object
    # number_of_days_to_look_back is an integer.
    def get_merit(self, start_date, number_of_days_to_look_back, use_exponential_moving_average=False):
        adjusted_prices = self.get_adjusted_prices_in_range(start_date, number_of_days_to_look_back)
        
        if adjusted_prices == None:
            return None
        
        merit = None
        if use_exponential_moving_average:
            scaling_factor = 0.6
            
            ema_for_start_date = self.compute_exponential_moving_average(adjusted_prices, scaling_factor)
            
            # Compute EMA for trading day |number_of_days_to_look_back| days ago.
            start_date_index = self.find_date_index_in_adjusted_prices(start_date)
            previous_start_date_index = start_date_index + number_of_days_to_look_back
            previous_months_adjusted_prices = self.get_adjusted_prices_in_range(previous_start_date_index, number_of_days_to_look_back, 'index')
            ema_for_previous_start_date = self.compute_exponential_moving_average(previous_months_adjusted_prices, scaling_factor)
            
            merit = ((ema_for_start_date - ema_for_previous_start_date) / ema_for_previous_start_date) / stats.tstd(adjusted_prices)
        else:
            # Reverse adjusted_prices so index 0 is the oldest date
            adjusted_prices.reverse()
        
            # Compute best fit line's slope and y-intercept for adjusted_prices
            slope, y_intercept = numpy.polyfit(range(0, number_of_days_to_look_back), adjusted_prices, 1)
        
            # Build list for adjusted_prices best fit line
            best_fit_line_for_adjusted_prices = []
            actual_and_best_fit_difference = []
            for x in range(0, number_of_days_to_look_back):
                best_fit_line_for_adjusted_prices.append((slope * x) + y_intercept)
                diff = (adjusted_prices[x] - best_fit_line_for_adjusted_prices[x]) / best_fit_line_for_adjusted_prices[x]
                actual_and_best_fit_difference.append(diff)
        
            # Compute gain of best_fit_line_for_adjusted_prices
            start_price = best_fit_line_for_adjusted_prices[0]
            end_price   = best_fit_line_for_adjusted_prices[-1]
            best_fit_gain_percentage = 100.0 * (end_price - start_price) / start_price
        
            # Compute standard deviation of best_fit_line_for_adjusted_prices
            actual_and_best_fit_difference_standard_deviation = stats.tstd(actual_and_best_fit_difference)
        
            merit = best_fit_gain_percentage / actual_and_best_fit_difference_standard_deviation
        
        return merit