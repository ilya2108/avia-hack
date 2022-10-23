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
def open_weights():
    for filename in ("best_model_mult_lstm.h5", "scaler.pkl", "Ural_model.pkl", "Sev_Zap_model.pkl"):
        try:
            f = open("/scripts/weights/"+filename, "rb")
        except FileNotFoundError:
            logging.error("File {} not found".format(filename))
        else:
            f.close()
            logging.info("File {} found".format(filename))
        