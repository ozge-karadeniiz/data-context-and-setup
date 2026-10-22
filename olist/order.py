import numpy as np
import pandas as pd
from olist.data import Olist
from olist.utils import haversine_distance


class Order:
    """
    DataFrames containing all orders as index,
    and various properties of these orders as columns
    """

    def __init__(self):
        self.data = Olist().get_data()

    def get_wait_time(self, is_delivered=True):
        """
        Returns a DataFrame with:
        [order_id, wait_time, expected_wait_time, delay_vs_expected, order_status]
        and filters out non-delivered orders unless specified
        """
        orders = self.data["orders"].copy()

        # Teslim edilmiş siparişleri filtrele
        if is_delivered:
            orders = orders[orders["order_status"] == "delivered"].copy()

        # Tarih sütunlarını datetime'a dönüştür
        date_cols = [
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        for col in date_cols:
            orders[col] = pd.to_datetime(orders[col])

        # Bekleme sürelerini gün (float) cinsinden hesapla
        orders["wait_time"] = (
            orders["order_delivered_customer_date"]
            - orders["order_purchase_timestamp"]
        ) / np.timedelta64(1, "D")

        orders["expected_wait_time"] = (
            orders["order_estimated_delivery_date"]
            - orders["order_purchase_timestamp"]
        ) / np.timedelta64(1, "D")

        # Gecikmeyi hesapla (erken teslim edildiyse 0)
        delay = (
            orders["order_delivered_customer_date"]
            - orders["order_estimated_delivery_date"]
        ) / np.timedelta64(1, "D")
        orders["delay_vs_expected"] = delay.clip(lower=0)

        return orders[
            [
                "order_id",
                "wait_time",
                "expected_wait_time",
                "delay_vs_expected",
                "order_status",
            ]
        ]

    def get_review_score(self):
        """
        Returns a DataFrame with:
        order_id, dim_is_five_star, dim_is_one_star, review_score
        """
        reviews = self.data["order_reviews"].copy()

        reviews["dim_is_five_star"] = (reviews["review_score"] == 5).astype(int)
        reviews["dim_is_one_star"] = (reviews["review_score"] == 1).astype(int)

        return reviews[
            ["order_id", "dim_is_five_star", "dim_is_one_star", "review_score"]
        ]

    def get_number_items(self):
        """
        Returns a DataFrame with:
        order_id, number_of_items
        """
        order_items = self.data["order_items"].copy()

        items = (
            order_items.groupby("order_id")["order_item_id"]
            .count()
            .reset_index()
        )
        items.columns = ["order_id", "number_of_items"]

        return items

    def get_number_sellers(self):
        """
        Returns a DataFrame with:
        order_id, number_of_sellers
        """
        order_items = self.data["order_items"].copy()

        sellers = (
            order_items.groupby("order_id")["seller_id"]
            .nunique()
            .reset_index()
        )
        sellers.columns = ["order_id", "number_of_sellers"]

        return sellers

    def get_price_and_freight(self):
        """
        Returns a DataFrame with:
        order_id, price, freight_value
        """
        order_items = self.data["order_items"].copy()

        price_freight = (
            order_items.groupby("order_id")[["price", "freight_value"]]
            .sum()
            .reset_index()
        )

        return price_freight

    def get_distance_seller_customer(self):
        """
        Returns a DataFrame with:
        order_id, distance_seller_customer
        """
        orders = self.data["orders"][["order_id", "customer_id"]].copy()
        customers = self.data["customers"][
            ["customer_id", "customer_zip_code_prefix"]
        ].copy()
        order_items = self.data["order_items"][
            ["order_id", "seller_id"]
        ].copy()
        sellers = self.data["sellers"][
            ["seller_id", "seller_zip_code_prefix"]
        ].copy()
        geo = self.data["geolocation"].copy()

        # Posta kodları koordinatlarını tekilleştir
        geo_unique = geo.groupby("geolocation_zip_code_prefix", as_index=False)[
            ["geolocation_lat", "geolocation_lng"]
        ].mean()

        # Müşteri koordinatlarını eşleştir
        customers_geo = customers.merge(
            geo_unique,
            left_on="customer_zip_code_prefix",
            right_on="geolocation_zip_code_prefix",
            how="inner",
        )[["customer_id", "geolocation_lat", "geolocation_lng"]].rename(
            columns={
                "geolocation_lat": "customer_lat",
                "geolocation_lng": "customer_lng",
            }
        )

        # Satıcı koordinatlarını eşleştir
        sellers_geo = sellers.merge(
            geo_unique,
            left_on="seller_zip_code_prefix",
            right_on="geolocation_zip_code_prefix",
            how="inner",
        )[["seller_id", "geolocation_lat", "geolocation_lng"]].rename(
            columns={
                "geolocation_lat": "seller_lat",
                "geolocation_lng": "seller_lng",
            }
        )

        # Tabloları birleştir
        df = order_items.merge(orders, on="order_id", how="inner")
        df = df.merge(customers_geo, on="customer_id", how="inner")
        df = df
