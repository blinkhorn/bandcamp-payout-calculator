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
latest_bmr_day_year = 0
latest_bmr_day_date = None

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
with open(release_info_file_name, newline="") as release_info_csv_file:
    release_info_reader = csv.reader(release_info_csv_file, delimiter=",")
    next(release_info_reader, None)
    for row in release_info_reader:
        release_info_data[parse_data(row[0])] = {
            "release_date": parse_data(row[1]),
            "mastering_opt_in": parse_data(row[2]) == "yes",
            "mastering_fee": float(parse_data(row[3])),
            "mastering_fee_amount_left_to_recover": float(parse_data(row[4])),
            "total_bandcamp_revenue": 0.00,
            "total_revenue_from_subscriptions": 0.00,
        }
        latest_bmr_day_year = (
            int(row[1][-4:])
            if int(row[1][-4:]) > latest_bmr_day_year
            else latest_bmr_day_year
        )

latest_bmr_day_date = datetime(latest_bmr_day_year, 6, 6)
bmr_day_subscriber_split_count = 12

for release in release_info_data:
    release_date = release_info_data[release]["release_date"]
    if (
        datetime(int(release_date[-4:]), int(release_date[:2]), int(release_date[3:5]))
        <= latest_bmr_day_date
    ):
        bmr_day_subscriber_split_count += 1
bmr_day_subscriber_split_count -= 2


def calculate_subscription_revenue_share_for_release(
    catalog_number: str, release_date: str, subscription_revenue_data: dict
) -> float:
    revenue_share_owed = 0.00
    next_bmr_day_date = datetime(latest_bmr_day_year + 1, 6, 6)
    for subscriber_id in subscription_revenue_data:
        subscriber_since = datetime(
            int(subscription_revenue_data[subscriber_id]["subscriber_since"][-4:]),
            int(subscription_revenue_data[subscriber_id]["subscriber_since"][:2]),
            int(subscription_revenue_data[subscriber_id]["subscriber_since"][3:5]),
        )
        print(catalog_number)
        print(next_bmr_day_date)
        print(subscriber_since)
        print(subscriber_id)
        print(subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"])
        print( subscriber_since < next_bmr_day_date)
        print(catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"])
        print(not subscription_revenue_data[subscriber_id]["all_releases_paid"])
        print(not subscription_revenue_data[subscriber_id]["is_renewal"])
        print(datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:])
                + 1,
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            > datetime(
                int(release_date[-4:]), int(release_date[:2]), int(release_date[3:5])
            ))
        print("sdjfidsjfsdjfids")
        print(
            subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and subscriber_since < next_bmr_day_date
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"]
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"])
        print(
            not subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and not subscription_revenue_data[subscriber_id]["is_renewal"]
            and datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:])
                + 1,
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            > datetime(
                int(release_date[-4:]), int(release_date[:2]), int(release_date[3:5])
            )
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"]
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"])
        print(
            not subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and subscription_revenue_data[subscriber_id]["is_renewal"]
            and datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:])
                + 1,
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            > datetime(
                int(release_date[-4:]), int(release_date[:2]), int(release_date[3:5])
            )
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"]
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"])
        if (
            subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and subscriber_since < next_bmr_day_date
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"]
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"]
        ):
            revenue_share_owed += float(subscription_revenue_data[subscriber_id][
                "amount_received"
            ]) / float(bmr_day_subscriber_split_count)
        elif (
            not subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and not subscription_revenue_data[subscriber_id]["is_renewal"]
            and datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:])
                + 1,
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            > datetime(
                int(release_date[-4:]), int(release_date[:2]), int(release_date[3:5])
            )
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"]
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"]
        ):
            revenue_share_owed += float(
                subscription_revenue_data[subscriber_id]["amount_received"]
            ) / float(12)
        elif (
            not subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and subscription_revenue_data[subscriber_id]["is_renewal"]
            and datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:])
                + 1,
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            > datetime(
                int(release_date[-4:]), int(release_date[:2]), int(release_date[3:5])
            )
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id]["catalog_numbers_paid"]
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"]
        ):
            revenue_share_owed += float(subscription_revenue_data[subscriber_id][
                "amount_received"
            ]) / float(12)
    return revenue_share_owed


bandcamp_sales_data = {}
with open(
    bandcamp_raw_sales_report_file_name, encoding="utf-16", newline=""
) as bandcamp_sales_csv_file:
    bandcamp_sales_reader = csv.reader(bandcamp_sales_csv_file, delimiter=",")
    next(bandcamp_sales_reader, None)
    for row in bandcamp_sales_reader:
        if parse_data(row[2]) != "payout":
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
        subscription_revenue_data[parse_data(row[0])] = {
            "is_renewal": parse_data(row[1]) == "yes",
            "subscriber_country": parse_data(row[2]),
            "subscriber_since": parse_data(row[3]),
            "transaction_date": parse_data(row[4]),
            "transaction_amount": parse_data(row[5]),
            "amount_received": parse_data(row[6]),
            "new_bmr_day_subscriber": parse_data(row[7]) == "yes",
            "catalog_numbers_paid": parse_data(row[8]),
            "all_releases_paid": parse_data(row[8]) == "yes",
        }


def calculate_mastering_fee_left_to_recover(
    release_catalog_number: str, total_revenue: float
):
    remaining_amount = 0.00
    if release_info_data[release_catalog_number]["mastering_opt_in"]:
        remaining_amount = (
            release_info_data[release_catalog_number][
                "mastering_fee_amount_left_to_recover"
            ]
            - total_revenue
        )
    return remaining_amount


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
            release_info_data[release_catalog_number][
                "total_bandcamp_revenue"
            ] += float(sale["net_amount"]) - float(sale["paypal_payout_fee"])
            csvwriter.writerow(sale.values())
        for j in range(3):
            csvwriter.writerow([None] * len(CSV_ROWS))
        results_headers = [
            f"Total Revenue from direct {release_catalog_number} Bandcamp sales",
            f"Total revenue from Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']}",
            "Amount of mastering fee left to recover before split",
            "Total revenue after mastering fee recovered",
            f"{release_sales_data[0]['artist']} split",
            "BMR Split",
            f"Amount Owed {release_sales_data[0]['artist']}",
        ]
        csvwriter.writerow(results_headers)

        total_subscription_revenue_share = (
            calculate_subscription_revenue_share_for_release(
                release_catalog_number,
                release_info_data[release_catalog_number]["release_date"],
                subscription_revenue_data,
            )
        )
        gross_revenue = (
            release_info_data[release_catalog_number]["total_bandcamp_revenue"]
            + total_subscription_revenue_share
        )
        mastering_fee_left = calculate_mastering_fee_left_to_recover(
            release_catalog_number, gross_revenue
        )
        if mastering_fee_left < 0.00:
            gross_revenue = mastering_fee_left * -1.00
            mastering_fee_left = 0.00

        release_results = [
            release_info_data[release_catalog_number]["total_bandcamp_revenue"],
            total_subscription_revenue_share,
            release_info_data[release_catalog_number]["total_bandcamp_revenue"]
            + total_subscription_revenue_share,
            mastering_fee_left,
            gross_revenue - mastering_fee_left if mastering_fee_left > 0.00 else 0.00,
            gross_revenue * 0.60 if mastering_fee_left == 0.00 else 0.00,
            gross_revenue * 0.40 if mastering_fee_left == 0.00 else gross_revenue,
            gross_revenue * 0.60 if mastering_fee_left == 0.00 else 0.00,
        ]
        csvwriter.writerow(release_results)
