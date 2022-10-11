import pandas as pd
from tqdm import tqdm
from darts import TimeSeries


# clean and prepare trips data
def prep_station_data(data, station_col, station_time):
    
    # clean trips data
    trips_clean = data[[station_col, station_time]]
    trips_clean[station_time] = pd.to_datetime(trips_clean[station_time])
    
    # prepare station data
    trips_clean_group = trips_clean.groupby([station_time, station_col], as_index = False).size()
    
    return trips_clean_group

# get individual station id and standardize
def get_station_data(data, station_col, station_time, station, freq, max_date):
    
    # filter for each station
    temp_series = data[data[station_col] == station]
    temp_series.set_index(station_time, inplace = True)
    
    # downsample trips to freq increments
    temp_series_freq = temp_series.resample(freq).sum()
    temp_daterange = pd.date_range(start = temp_series_freq.index[0], end = max_date, freq = freq)
    
    # ensure the series reaches the end/max_date
    temp_series_freq = temp_series_freq.reindex(temp_daterange).fillna(0)
    temp_series_freq = temp_series_freq.drop([station_col], axis = 1)
    temp_series_freq["size"] = temp_series_freq["size"].astype(int)
    
    return temp_series_freq

# format data for darts package
def darts_station_data(data, station_col, station_time, freq, max_date):
    
    station_list = []
    
    for station in tqdm(data[station_col].unique()):

        temp_series_freq = get_station_data(data, station_col, station_time, station, freq, max_date)
        temp_series_freq["date"] = temp_series_freq.index
        
        # change data to be a darts TimeSeries type
        temp_list = TimeSeries.from_dataframe(temp_series_freq, "date", "size")

        station_list.append(temp_list)
        
    return station_list