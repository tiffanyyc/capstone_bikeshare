import pandas as pd
from tqdm import tqdm


# organize data required for the DeepAR model
def organize_data(data, station_col, max_date):
    
    station_dict = {}
    
    for station in tqdm(data[station_col].unique()):

        temp_dict = {}

        # filter for each station
        temp_series = data[data[station_col] == station]
        temp_series.set_index("starttime", inplace = True)

        # downsample trips to 15-minute increments
        temp_series_15min = temp_series.resample("15min").sum()
        temp_daterange = pd.date_range(start = temp_series_15min.index[0], end = max_date, freq = "15min")

        # ensure the series reaches the end/max_date
        temp_series_15min = temp_series_15min.reindex(temp_daterange).fillna(0)
        temp_series_15min["size"] = temp_series_15min["size"].astype(int)

        # specify the start of the series and the series itself
        temp_dict = {"start": str(temp_series_15min.index[0]),
                     "target": temp_series_15min["size"].tolist()}

        station_dict[station] = temp_dict
        
    return station_dict