import csv
import sys
from datetime import datetime


def calculate_paypal_fee(net_amount: float) -> float:
    rounded_net_amount = round(net_amount * 0.01, 2)
    return rounded_net_amount if rounded_net_amount < 1.00 else 1.00


def parse_data(data: float | str | int) -> float | str | int | None:
    if type(data) == str:
        return data.replace(",", "")
    elif type(data) == float or type(data) == int:
        return data
    return None


RELEASES_NOT_INCLUDED_IN_BMR_DAY_PAYOUTS = {"BMRX001", "BMR000"}
bandcamp_raw_sales_report_file_name = sys.argv[1]
release_info_file_name = sys.argv[2]
subscription_revenue_data_file_name = sys.argv[3]

CSV_ROWS = [
    "date",
    "item_type",
    "artist",
    "item_name",
    "item_price",
    "quantity",
    "sub_total",
    "additional_fan_contribution",
    "transaction_fee",
    "bandcamp_revenue_fee",
    "paypal_payout_fee",
    "net_amount",
    "buyer_country",
    "catalog_number",
]

release_info_data = {}
with open(release_info_file_name, newline="") as release_info_csv_file:
    latest_bmr_day_year = 0

    release_info_reader = csv.reader(release_info_csv_file, delimiter=",")
    next(release_info_reader, None)
    for row in release_info_reader:
        release_info_data[parse_data(row[0])] = {
            "artist_name": parse_data(row[1]),
            "release_date": parse_data(row[2]),
            "mastering_opt_in": parse_data(row[3]) == "yes",
            "mastering_fee": float(parse_data(row[4])),
            "mastering_fee_amount_left_to_recover": float(parse_data(row[5])),
            "multiple_artist_release": parse_data(row[6]) == "yes",
            "artist_split_distribution_by_track_and_overall_release": parse_data(
                row[7]
            ),
            "total_bandcamp_revenue": 0.00,
            "total_revenue_from_subscriptions": 0.00,
        }
        latest_bmr_day_year = (
            int(row[2][-4:])
            if int(row[2][-4:]) > latest_bmr_day_year
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
bmr_day_subscriber_split_count -= len(RELEASES_NOT_INCLUDED_IN_BMR_DAY_PAYOUTS)

bandcamp_sales_data = {}
with open(
    bandcamp_raw_sales_report_file_name, encoding="utf-16", newline=""
) as bandcamp_sales_csv_file:
    bandcamp_sales_reader = csv.reader(bandcamp_sales_csv_file, delimiter=",")
    next(bandcamp_sales_reader, None)
    for row in bandcamp_sales_reader:
        if parse_data(row[2]) != "payout" and parse_data(row[2]) != "package":
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
            "all_releases_paid": parse_data(row[9]) == "yes",
            "tier_2_subscriber": parse_data(row[10]) == "yes",
        }


def calculate_subscription_revenue_share_for_release(catalog_number: str) -> float:
    revenue_share_owed = 0.00
    next_bmr_day_date = datetime(latest_bmr_day_year + 1, 6, 6)
    release_date = release_info_data[catalog_number]["release_date"]
    for subscriber_id in subscription_revenue_data:
        if subscription_revenue_data[subscriber_id]["tier_2_subscriber"]:
            subscription_revenue_data[subscriber_id]["amount_received"] = (
                float(subscription_revenue_data[subscriber_id]["amount_received"])
                - 12.87
            )
        subscriber_since = datetime(
            int(subscription_revenue_data[subscriber_id]["subscriber_since"][-4:]),
            int(subscription_revenue_data[subscriber_id]["subscriber_since"][:2]),
            int(subscription_revenue_data[subscriber_id]["subscriber_since"][3:5]),
        )
        if (
            subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and subscriber_since < next_bmr_day_date
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id][
                "catalog_numbers_paid"
            ].lower()
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"]
        ):
            revenue_share_owed += float(
                subscription_revenue_data[subscriber_id]["amount_received"]
            ) / float(bmr_day_subscriber_split_count)
        elif (
            not subscription_revenue_data[subscriber_id]["new_bmr_day_subscriber"]
            and datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            < datetime(
                int(release_date[-4:]),
                int(release_date[:2]),
                int(release_date[3:5]),
            )
            and datetime(
                int(subscription_revenue_data[subscriber_id]["transaction_date"][-4:])
                + 1,
                int(subscription_revenue_data[subscriber_id]["transaction_date"][:2]),
                int(subscription_revenue_data[subscriber_id]["transaction_date"][3:5]),
            )
            >= datetime(
                int(release_date[-4:]),
                int(release_date[:2]),
                int(release_date[3:5]),
            )
            and catalog_number.lower()
            not in subscription_revenue_data[subscriber_id][
                "catalog_numbers_paid"
            ].lower()
            and not subscription_revenue_data[subscriber_id]["all_releases_paid"]
        ):
            revenue_share_owed += float(
                subscription_revenue_data[subscriber_id]["amount_received"]
            ) / float(12)
    return revenue_share_owed


def calculate_mastering_fee_left_to_recover(
    release_catalog_number: str, total_revenue: float
) -> float | str:
    remaining_amount = "Not Applicable"
    if release_info_data[release_catalog_number]["mastering_opt_in"]:
        remaining_amount = (
            release_info_data[release_catalog_number][
                "mastering_fee_amount_left_to_recover"
            ]
            - total_revenue
        )
    return remaining_amount


def parse_artist_split_distribution_by_track_and_overall_release(
    release_catalog_number: str,
) -> dict:
    distribution_rules = {"recording_artists": {}}
    distributions = release_info_data[release_catalog_number][
        "artist_split_distribution_by_track_and_overall_release"
    ].split(";")
    for distribution in distributions:
        music_recording_item, _, distribution_rule = distribution.partition(":")
        splits_by_recording = [distribution_rule]
        distribution_rules[music_recording_item] = {}
        if "&" in distribution_rule:
            splits_by_recording = distribution_rule.split("&")
        for split in splits_by_recording:
            artist_name, _, split_amount = split.partition("=")
            if artist_name in distribution_rules["recording_artists"]:
                distribution_rules["recording_artists"][artist_name][
                    "payable_recordings"
                ].append(music_recording_item)
            else:
                distribution_rules["recording_artists"][artist_name] = {
                    "payable_recordings": [music_recording_item]
                }

            distribution_rules[music_recording_item][artist_name] = split_amount

    return distribution_rules


current_date = datetime.today().strftime("%Y-%m-%d")


def create_payout_csv(
    release_catalog_number: str,
    artist_name: str | None = None,
    distribution_rules: dict | None = None,
):
    release_catalog_number_report_id = release_catalog_number
    if release_info_data[release_catalog_number]["multiple_artist_release"]:
        release_catalog_number_report_id = f"{artist_name}_{release_catalog_number}"
        if (
            "bandcamp_revenue_by_artist"
            not in release_info_data[release_catalog_number]
            or not release_info_data[release_catalog_number][
                "bandcamp_revenue_by_artist"
            ]
        ):
            release_info_data[release_catalog_number]["bandcamp_revenue_by_artist"] = {
                artist: 0.00
            }
        else:
            release_info_data[release_catalog_number]["bandcamp_revenue_by_artist"][
                artist
            ] = 0.00
    with open(
        f"{current_date}_{release_catalog_number_report_id}_bandcamp_sales_report.csv",
        "w",
        newline="",
    ) as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        release_sales_data = []
        if release_catalog_number in bandcamp_sales_data:
            release_sales_data = bandcamp_sales_data[release_catalog_number]
        csvwriter.writerow(CSV_ROWS)
        if len(release_sales_data):
            for sale in release_sales_data:
                release_info_data[release_catalog_number][
                    "total_bandcamp_revenue"
                ] += float(sale["net_amount"]) - float(sale["paypal_payout_fee"])
                if not release_info_data[release_catalog_number][
                    "multiple_artist_release"
                ]:
                    csvwriter.writerow(sale.values())
                else:
                    if sale["item_type"] == "album":
                        if (
                            "overall_release"
                            in distribution_rules["recording_artists"][artist_name][
                                "payable_recordings"
                            ]
                        ):
                            release_info_data[release_catalog_number][
                                "bandcamp_revenue_by_artist"
                            ][artist] += (
                                float(sale["net_amount"])
                                - float(sale["paypal_payout_fee"])
                            ) * float(
                                f"0.{distribution_rules["overall_release"][artist_name]}"
                            )
                            csvwriter.writerow(sale.values())
                    elif sale["item_type"] == "track":
                        if (
                            sale["item_name"]
                            in distribution_rules["recording_artists"][artist_name][
                                "payable_recordings"
                            ]
                        ):
                            release_info_data[release_catalog_number][
                                "bandcamp_revenue_by_artist"
                            ][artist] += float(sale["net_amount"]) - float(
                                sale["paypal_payout_fee"]
                            ) * float(
                                f"0.{distribution_rules[sale["item_name"]][artist_name]}"
                            )
                            csvwriter.writerow(sale.values())
        else:
            csvwriter.writerow(
                ["No direct Bandcamp sales this accounting cycle"] * len(CSV_ROWS)
            )

        for _ in range(3):
            csvwriter.writerow([None] * len(CSV_ROWS))

        results_headers_artist_name = (
            artist_name
            if artist_name
            else release_info_data[release_catalog_number]["artist_name"]
        )

        results_headers = [
            "Total overall release revenue from direct Bandcamp sales",
            "Total artist-specific revenue from direct Bandcamp sales (relevant for multi-artist releases)",
            f"Total overall release revenue from BMR Day Bandcamp Annual Subscriptions or Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']}",
            f"Total artist-specific revenue from BMR Day Bandcamp Annual Subscriptions or Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']} (relevant for multi-artist releases)",
            f"Total overall revenue from direct Bandcamp sales, BMR Day Bandcamp Annual Subscriptions, and Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']}",
            f"Total artist-specific revenue from direct Bandcamp sales, BMR Day Bandcamp Annual Subscriptions, and Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']} (relevant for multi-artist releases)",
            "Amount of mastering fee left to recover for overall release before split",
            "Total revenue from overall release after mastering fee recovered",
            "Total artist-specific revenue from release after mastering fee recovered (relevant for multi-artist releases)",
            f"{results_headers_artist_name} split",
            "BMR Split",
            f"Amount Owed {results_headers_artist_name}",
        ]
        csvwriter.writerow(results_headers)

        overall_release_subscription_revenue_share = (
            release_artist_specific_subscription_revenue_share
        ) = calculate_subscription_revenue_share_for_release(release_catalog_number)

        overall_net_revenue = artist_specific_net_revenue = (
            release_info_data[release_catalog_number]["total_bandcamp_revenue"]
            + overall_release_subscription_revenue_share
        )

        mastering_fee_left = calculate_mastering_fee_left_to_recover(
            release_catalog_number, overall_net_revenue
        )

        # TODO: add logic to to calculate artist-specific share if overall release mastering fee is recovered in the current payout cycle
        release_broke_even = False
        if mastering_fee_left == 0.00:
            release_broke_even = True
            total_revenue_after_mastering_fee_recovered = (
                total_artist_specific_revenue_after_mastering_fee_recovered
            ) = 0.00
        elif mastering_fee_left == "Not Applicable":
            total_revenue_after_mastering_fee_recovered = (
                total_artist_specific_revenue_after_mastering_fee_recovered
            ) = mastering_fee_left
        elif mastering_fee_left < 0.00:
            total_revenue_after_mastering_fee_recovered = (
                total_artist_specific_revenue_after_mastering_fee_recovered
            ) = (mastering_fee_left * -1.00)
            mastering_fee_left = 0.00
        else:
            total_revenue_after_mastering_fee_recovered = (
                total_artist_specific_revenue_after_mastering_fee_recovered
            ) = 0.00

        net_revenue_after_mastering_fee_recovered = (
            overall_net_revenue
            if total_revenue_after_mastering_fee_recovered == "Not Applicable"
            else total_revenue_after_mastering_fee_recovered
        )

        if (
            release_info_data[release_catalog_number]["multiple_artist_release"]
            and "overall_release"
            in distribution_rules["recording_artists"][artist_name][
                "payable_recordings"
            ]
        ):
            release_artist_specific_subscription_revenue_share = (
                overall_release_subscription_revenue_share
                * float(f"0.{distribution_rules["overall_release"][artist_name]}")
            )
            artist_specific_net_revenue = (
                release_info_data[release_catalog_number]["bandcamp_revenue_by_artist"][
                    artist
                ]
                + release_artist_specific_subscription_revenue_share
            )
            # TODO: add logic to to calculate artist-specific share if overall release mastering fee is recovered in the current payout cycle
        
        # TODO: add logic to to calculate artist-specific payout results if overall release mastering fee is recovered in the current payout cycle
        release_results = [
            release_info_data[release_catalog_number]["total_bandcamp_revenue"],
            release_info_data[release_catalog_number]["bandcamp_revenue_by_artist"][
                artist
            ] if release_info_data[release_catalog_number]["multiple_artist_release"] else release_info_data[release_catalog_number]["total_bandcamp_revenue"],
            overall_release_subscription_revenue_share,
            release_artist_specific_subscription_revenue_share,
            overall_net_revenue,
            artist_specific_net_revenue,
            mastering_fee_left,
            'total_revenue_after_mastering_fee_recovered',
            (
                net_revenue_after_mastering_fee_recovered * 0.60
                if mastering_fee_left == "Not Applicable" or mastering_fee_left == 0.00
                else 0.00
            ),
            (
                net_revenue_after_mastering_fee_recovered * 0.40
                if mastering_fee_left == "Not Applicable"
                or (mastering_fee_left == 0.00 and not release_broke_even)
                else overall_net_revenue
            ),
            (
                net_revenue_after_mastering_fee_recovered * 0.60
                if mastering_fee_left == "Not Applicable" or mastering_fee_left == 0.00
                else 0.00
            ),
        ]
        csvwriter.writerow(release_results)


for release_catalog_number in release_info_data:
    artist_split_distribution_by_track_and_overall_release = None
    if release_catalog_number not in RELEASES_NOT_INCLUDED_IN_BMR_DAY_PAYOUTS or (
        release_catalog_number != "BMRX001" and "BMR000" in bandcamp_sales_data
    ):
        if release_info_data[release_catalog_number]["multiple_artist_release"]:
            distribution_rules = (
                parse_artist_split_distribution_by_track_and_overall_release(
                    release_catalog_number
                )
            )
            for artist in distribution_rules["recording_artists"]:
                create_payout_csv(release_catalog_number, artist, distribution_rules)
        else:
            create_payout_csv(release_catalog_number)
