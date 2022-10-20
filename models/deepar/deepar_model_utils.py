import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import sagemaker
from sagemaker.serializers import IdentitySerializer


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
            
class DeepARPredictor(sagemaker.predictor.Predictor):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            # serializer=JSONSerializer(),
            serializer=IdentitySerializer(content_type="application/json"),
            **kwargs,
        )

    def predict(
        self,
        ts,
        cat=None,
        dynamic_feat=None,
        num_samples=100,
        return_samples=False,
        quantiles=["0.1", "0.5", "0.9"],
    ):
        """Requests the prediction of for the time series listed in `ts`, each with the (optional)
        corresponding category listed in `cat`.

        ts -- `pandas.Series` object, the time series to predict
        cat -- integer, the group associated to the time series (default: None)
        num_samples -- integer, number of samples to compute at prediction time (default: 100)
        return_samples -- boolean indicating whether to include samples in the response (default: False)
        quantiles -- list of strings specifying the quantiles to compute (default: ["0.1", "0.5", "0.9"])

        Return value: list of `pandas.DataFrame` objects, each containing the predictions
        """
        prediction_time = ts.index[-1] + ts.index.freq
        quantiles = [str(q) for q in quantiles]
        req = self.__encode_request(ts, cat, dynamic_feat, num_samples, return_samples, quantiles)
        res = super(DeepARPredictor, self).predict(req)
        return self.__decode_response(res, ts.index.freq, prediction_time, return_samples)

    def __encode_request(self, ts, cat, dynamic_feat, num_samples, return_samples, quantiles):
        instance = series_to_dict(
            ts, cat if cat is not None else None, dynamic_feat if dynamic_feat else None
        )

        configuration = {
            "num_samples": num_samples,
            "output_types": ["quantiles", "samples"] if return_samples else ["quantiles"],
            "quantiles": quantiles,
        }

        http_request_data = {"instances": [instance], "configuration": configuration}

        return json.dumps(http_request_data).encode("utf-8")

    def __decode_response(self, response, freq, prediction_time, return_samples):
        # we only sent one time series so we only receive one in return
        # however, if possible one will pass multiple time series as predictions will then be faster
        predictions = json.loads(response.decode("utf-8"))["predictions"][0]
        prediction_length = len(next(iter(predictions["quantiles"].values())))
        prediction_index = pd.date_range(
            start=prediction_time, freq=freq, periods=prediction_length
        )
        if return_samples:
            dict_of_samples = {"sample_" + str(i): s for i, s in enumerate(predictions["samples"])}
        else:
            dict_of_samples = {}
        return pd.DataFrame(
            data={**predictions["quantiles"], **dict_of_samples}, index=prediction_index
        )

    def set_frequency(self, freq):
        self.freq = freq


def encode_target(ts):
    return [x if np.isfinite(x) else "NaN" for x in ts]


def series_to_dict(ts, cat=None, dynamic_feat=None):
    """Given a pandas.Series object, returns a dictionary encoding the time series.

    ts -- a pands.Series object with the target time series
    cat -- an integer indicating the time series category

    Return value: a dictionary
    """
    obj = {"start": str(ts.index[0]), "target": encode_target(ts)}
    if cat is not None:
        obj["cat"] = cat
    if dynamic_feat is not None:
        obj["dynamic_feat"] = dynamic_feat
    return obj