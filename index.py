import csv
import sys
from datetime import datetime


def calculate_paypal_fee(net_amount: float):
    rounded_net_amount = round(net_amount * 0.01, 2)
    return rounded_net_amount if rounded_net_amount < 1.00 else 1.00


def parse_data(data: float | str | int) -> float | str | int | None:
    if type(data) == str:
        return data.replace(",", "")
    elif type(data) == float or type(data) == int:
        return data
    return None


bandcamp_raw_sales_report_file_name = sys.argv[1]
release_info_file_name = sys.argv[2]
subscription_revenue_data_file_name = sys.argv[3]
current_date = datetime.today().strftime("%Y-%m-%d")
total_release_revenue = total_release_fees = (
    total_bandcamp_subscription_revenue_owed
) = mastering_fee_amount_left_to_recovered = (
    total_revenue_after_mastering_fee_recovered
) = artist_split = bmr_split = amount_owed_artist = 0
opted_in_for_mastering = False
MASTERING_FEE = 45.00

CSV_ROWS = [
    "date",
    "item_type",
    "artist",
    "item_name",
    "quantity",
    "item_price",
    "sub_total",
    "additional_fan_contribution",
    "transaction_fee",
    "bandcamp_revenue_fee",
    "net_amount",
    "buyer_country",
    "buyer_country",
    "catalog_number",
]

release_info_data = {}
with open(
    release_info_file_name, newline=""
) as release_info_csv_file:
    release_info_reader = csv.reader(release_info_csv_file, delimiter=",")
    next(release_info_reader, None)
    for row in release_info_reader:
        release_info_data[parse_data(row[0])] = {
            "release_date": parse_data(row[1]),
            "mastering_opt_in": parse_data(row[2]),
            "mastering_fee": parse_data(row[3]),
            "mastering_fee_amount_left_to_recover": parse_data(row[4]),
            "total_bandcamp_revenue": 0.00,
            "total_revenue_from_subscriptions": 0.00
        }
bandcamp_sales_data = {}
with open(
    bandcamp_raw_sales_report_file_name, encoding="utf-16", newline=""
) as bandcamp_sales_csv_file:
    bandcamp_sales_reader = csv.reader(bandcamp_sales_csv_file, delimiter=",")
    next(bandcamp_sales_reader, None)
    for row in bandcamp_sales_reader:
        if row[2] != "payout":
            bandcamp_sale = {
                "date": parse_data(row[0]),
                "item_type": parse_data(row[2]),
                "artist": parse_data(row[4]),
                "item_name": parse_data(row[3]),
                "item_price": parse_data(row[6]),
                "quantity": parse_data(row[7]),
                "sub_total": parse_data(row[9]),
                "additional_fan_contribution": parse_data(row[10]),
                "transaction_fee": parse_data(row[16]),
                "bandcamp_revenue_fee": parse_data(row[22]),
                "paypal_payout_fee": calculate_paypal_fee(parse_data(float(row[27]))),
                "net_amount": parse_data(row[27]),
                "buyer_country": parse_data(row[47]),
                "catalog_number": parse_data(row[31]),
            }
            if parse_data(row[31]) not in bandcamp_sales_data:
                bandcamp_sales_data[parse_data(row[31])] = [bandcamp_sale]
            else:
                bandcamp_sales_data[parse_data(row[31])].append(bandcamp_sale)

subscription_revenue_data = {}
with open(
    subscription_revenue_data_file_name, newline=""
) as subscription_revenue_data_csv_file:
    subscription_revenue_data_reader = csv.reader(
        subscription_revenue_data_csv_file, delimiter=","
    )
    next(subscription_revenue_data_reader, None)
    for row in subscription_revenue_data_reader:
        if row
        subscription_revenue_data[parse_data(row[0])] = {
            "status": parse_data(row[1]),
            "subscriber_country": parse_data(row[2]),
            "subscriber_since": parse_data(row[3]),
            "transaction_date": parse_data(row[4]),
            "transaction_amount": parse_data(row[5]),
            "amount_received": parse_data(row[6]),
            "new_bmr_day_subscriber": parse_data(row[7]) == "yes",
            "catalog_numbers_paid": parse_data(row[8]),
        }

for release_catalog_number in bandcamp_sales_data:
    with open(
        f"{current_date}_{release_catalog_number}_bandcamp_sales_report.csv",
        "w",
        newline="",
    ) as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        release_sales_data = bandcamp_sales_data[release_catalog_number]
        csvwriter.writerow(CSV_ROWS)
        for sale in release_sales_data:
            release_info_data[release_catalog_number].total_bandcamp_revenue += (sale.net_amount - sale.paypal_payout_fee)
            csvwriter.writerow(sale.values())
        for j in range(3):
            csvwriter.writerow([","] * len(CSV_ROWS))
        results_headers = [
            None * (len(CSV_ROWS) - 9),
            f"Total Revenue from direct {release_catalog_number} Bandcamp sales",
            f"Total revenue from Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']}",
            "Amount of mastering fee left to recover before split",
            "Total revenue after mastering fee recovered",
            f"{release_sales_data[0]['artist']} split",
            "BMR Split",
            f"Amount Paid to {release_sales_data[0]['artist']}",
        ]
        csvwriter.writerow(results_headers)
        release_results = [
            None * (len(CSV_ROWS) - 9),jhu]
