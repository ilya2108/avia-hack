from pandas.core.tools.datetimes import to_datetime
import datetime
import pickle
import pandas as pd
import statistics
from datetime import datetime, timedelta
import sys
from io import StringIO
import numpy as np
import keras
from pathlib import Path
import logging
# def open_weights():
#     for filename in ("best_model_mult_lstm.h5", "scaler.pkl", "Ural_model.pkl", "Sev_Zap_model.pkl"):
#         try:
#             f = open("/scripts/weights/"+filename, "rb")
#         except FileNotFoundError:
#             logging.error("File {} not found".format(filename))
#         else:
#             f.close()
#             logging.info("File {} found".format(filename))

def to_pandas(value, value_temp, dti):
    return pd.DataFrame([dti, value, value_temp], index=["Date", "Volume", "Volume_temp"]).T


def load_models():
    names = ['/scripts/weights/Moscow_model.pkl', '/scripts/weights/Sev_Zap_model.pkl',
             '/scripts/weights/Ural_model.pkl']
    models_objects = []
    for model_name in names:
        with open(model_name, 'rb') as f:
            models_objects.append(pickle.load(f))
    return models_objects


moscow, sev_zap, ural = load_models()


def predict(date: str, region: str):
    future = pd.DataFrame({"ds": [np.datetime64(date)]})
    future["is_weekend"] = future['ds'].dt.dayofweek > 4  # выходной 0/1
    future["season"] = future['ds'].dt.month % 12 // 3 + 1  # winter summer etc

    if region == 'МР Москва':
        return moscow.predict(future)['yhat'][0]
    if region == 'МР Северо-Запад':
        return sev_zap.predict(future)['yhat'][0]
    if region == 'МР Урал':
        return ural.predict(future)['yhat'][0]


def plan_to_zagr(dt, date="Date", typ='exМР'):
    TESTDATA = StringIO(dt)
    dat = pd.read_csv(TESTDATA, sep=";", index_col=date, parse_dates=[date])
    dat = dat.sort_index()
    rek = []
    for i in ['МР Москва', 'МР Северо-Запад', 'МР Урал']:
        if i == 'МР Москва':
            Basic_capacity = 10800
            k = 9.105815696019702
        if i == 'МР Северо-Запад':
            Basic_capacity = 8000
            k = 25.600395294891136
        if i == 'МР Урал':
            Basic_capacity = 3000
            k = 13.149119098565656
        ras = dat[dat[typ] == i]
        if len(ras) == 0:
            continue
        start_date = ras.index[0] - timedelta(days=7)
        Basic_capacity = predict(start_date, i)
        end_date = ras.index[len(ras) - 1]
        dti = pd.date_range(start_date, periods=7 + len(set(ras.index)) - 1, freq="D")
        value = []
        value_temp = []
        pogr = []
        shell = []
        otgr = []
        for i in dti:
            tm_d = 0
            if len(ras[ras.index == i]) != 0:
                for b in otgr:
                    tm_d += (k / 2)
                    Basic_capacity -= (k / 2)
                otgr = []
                for b in range(len(shell)):
                    if shell[b] > 0:
                        shell[b] -= 1
                    elif shell[b] == 0:
                        otgr.append(k / 2)
                        tm_d += (k / 2)
                        Basic_capacity -= (k / 2)
                        shell[b] -= 1
                for b in pogr:
                    tm_d += (k / 2)
                    Basic_capacity += (k / 2)
                    shell.append(3)
                pogr = []
                for b in range(len(ras[ras.index == i])):
                    Basic_capacity += (k / 2)
                    pogr.append(k / 2)
                    tm_d += (k / 2)
            value.append(Basic_capacity)
            value_temp.append(tm_d)
            tm_d = 0
        rek.append(to_pandas(value, value_temp, dti))
    return ml_month(rek, num_days_predicted=31)


from copy import deepcopy


def ml_month(tr, num_days_predicted=31):
    rek = deepcopy(tr)
    run = deepcopy(tr)
    lstm_mult_model1 = keras.models.load_model('/scripts/weights/best_model_mult_lstm.h5')
    for i in range(len(rek)):
        rek[i] = rek[i].set_index('Date').Volume
        ind = range(168)
        data_mn = pd.DataFrame([rek[i].tail(168).tolist()], columns=list(ind))
        max_steps = 168
        master_series = []
        for i in range(len(data_mn)):
            if (max(data_mn.iloc[i, 0:max_steps]) == 0):
                continue
            myseries = np.array(data_mn.iloc[i][0:max_steps])
            master_series.append(myseries)
        master_series = np.array(master_series)
        master_series = master_series[..., np.newaxis].astype(np.float32)
        master_series_values = master_series.reshape(-1, 1)
        log_master_series = []
        for i in range(master_series.shape[0]):
            temp_series = np.array(np.log(master_series[i][0:] + 1))
            log_master_series.append(temp_series)
        log_master_series = np.array(log_master_series)
        series = log_master_series[:, : 167 + num_days_predicted, :]
        y_train_mult = series[:2, -num_days_predicted:, 0]
        with open('/scripts/weights/skaler.pkl', 'rb') as f:
            scaler = pickle.load(f)

        def reverse_transform(arr):
            arr = arr.reshape(-1, 1)
            arr_inv_normal = scaler.inverse_transform(arr)
            arr_reverse = np.exp(arr_inv_normal) - 1
            return (arr_reverse)

        y_train_normalized = scaler.transform(y_train_mult.reshape(-1, 1))
        y_train_mult = y_train_normalized.reshape(y_train_mult.shape[0], y_train_mult.shape[1])
        result = reverse_transform(lstm_mult_model1.predict(y_train_mult))
        dt = tr[i].set_index('Date').index[-1]
        print(dt)
        df2 = None
        for b in result:
            dt = dt + timedelta(days=1)
            if df2 is None:
                df2 = pd.DataFrame([[dt, b[0], 0]], columns=['Date', 'Volume', 'Volume_temp'])
            else:
                df2 = pd.concat([df2, pd.DataFrame([[dt, b[0], 0]], columns=['Date', 'Volume', 'Volume_temp'])])
        run[i] = pd.concat([run[i], df2])
    return run

