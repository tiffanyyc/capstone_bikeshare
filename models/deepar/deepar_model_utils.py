import json
import pandas as pd
from tqdm import tqdm


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

# organize data required for the DeepAR model
def deepar_station_data(data, station_col, station_time, freq, max_date, train_date, test_date):
    
    train_list = []
    test_list = []
    
    for station in tqdm(data[station_col].unique()):

        temp_train_dict = {}
        temp_test_dict = {}
        
        temp_series_freq = get_station_data(data, station_col, station_time, station, freq, max_date)
        
        # make sure all stations have existed before the test period
        if temp_series_freq.index[0] < pd.to_datetime(test_date):
            
            # TRAIN: specify the start of the series and the series itself
            temp_train_dict = {"start": str(temp_series_freq.loc[:train_date].index[0]),
                               "target": temp_series_freq.loc[:train_date]["size"].tolist()}

            # TEST: specify the start of the series and the series itself
            temp_test_dict = {"start": str(temp_series_freq.loc[test_date:].index[0]),
                              "target": temp_series_freq.loc[test_date:]["size"].tolist()}

            train_list.append(temp_train_dict)
            test_list.append(temp_test_dict)
        
    return train_list, test_list

# write dictionary to jsonlines file format
def write_dicts_to_file(path, data):
    with open(path, "wb") as fp:
        for d in data:
            fp.write(json.dumps(d).encode("utf-8"))
            fp.write("\n".encode("utf-8"))