import os
import pandas as pd
from pathlib import Path


class Olist:
    def __init__(self):
        pass

    def ping(self):
        print("pong")

    def get_data(self):
        """
        This function returns a Python dict.
        Its keys should be 'sellers', 'orders', 'order_items' etc...
        Its values should be pandas.DataFrames loaded from csv files
        """
        csv_path = Path("~/.workintech/olist/data/csv").expanduser()

        data = {}
        for file in csv_path.iterdir():
            if file.name.endswith(".csv"):
                key = (
                    file.name.replace("olist_", "")
                    .replace("_dataset.csv", "")
                    .replace(".csv", "")
                )
                data[key] = pd.read_csv(file)

        return data
