import csv
import sys
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

current_date = datetime.today().strftime("%Y-%m-%d")


def csv_to_pdf_table(csv_filename: str, pdf_filename: str, catalog_number: str) -> None:
    try:
        csv_data = pd.read_csv(csv_filename).fillna("")
    except FileNotFoundError:
        print(f"Error: The file {csv_filename} was not found.")
        return

    pdf_doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=landscape(letter),
        rightMargin=15,
        leftMargin=15,
        topMargin=20,
        bottomMargin=20,
    )
    story = []

    page_width, _ = landscape(letter)
    available_width = page_width - 30
    col_width = available_width / len(csv_data.columns)
    col_widths_list = [col_width] * len(csv_data.columns)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        textColor=colors.HexColor("#1A365D"),
        alignment=0,
        spaceAfter=10,
    )

    header_cell_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6,
        leading=7,
        textColor=colors.whitesmoke,
        alignment=1,
    )

    body_cell_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=5,
        leading=6,
        textColor=colors.HexColor("#1E293B"),
        alignment=0,
    )

    story.append(
        Paragraph(
            f"{catalog_number} | BMR BI-Annual Revenue Report ({current_date})",
            title_style,
        )
    )
    story.append(Spacer(1, 5))

    headers = [Paragraph(str(col), header_cell_style) for col in csv_data.columns]

    data_rows = []
    for _, row in csv_data.iterrows():
        wrapped_row = []
        for val in row:
            cell_text = str(val).strip()

            if len(cell_text) > 12 and " " not in cell_text:
                cell_text = "".join(
                    cell_text[i : i + 12] for i in range(0, len(cell_text), 12)
                )

            wrapped_row.append(Paragraph(cell_text, body_cell_style))
        data_rows.append(wrapped_row)

    table_data = [headers] + data_rows

    pdf_table = Table(table_data, colWidths=col_widths_list, repeatRows=1)

    style_config = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ]
    )

    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_config.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8FAFC"))

    pdf_table.setStyle(style_config)
    story.append(pdf_table)

    pdf_doc.build(story)


def calculate_paypal_fee(net_amount: float, fee_percentage: float) -> float:
    rounded_net_amount = round(net_amount * fee_percentage, 2)
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
artist_info_file_name = sys.argv[4]
routenote_revenue_data_file_name = None
if len(sys.argv) > 5:
    routenote_revenue_data_file_name = sys.argv[5]

CSV_ROWS = [
    "date",
    "platform",
    "item_type",
    "artist",
    "item_name",
    "dsp_retailer",
    "dsp_retailer_currency",
    "dsp_customer_territory",
    "dsp_download_unit_count",
    "dsp_stream_unit_count",
    "dsp_total_revenue_usd",
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

release_catalog_number_by_upc_hash = {}
release_info_data = {}
with open(release_info_file_name, newline="") as release_info_csv_file:
    latest_bmr_day_year = 0
    release_info_reader = csv.reader(release_info_csv_file, delimiter=",")
    next(release_info_reader, None)
    for row in release_info_reader:
        release_catalog_number_by_upc_hash[parse_data(row[8])] = parse_data(row[0])
        release_info_data[parse_data(row[0])] = {
            "artist_name": parse_data(row[1]).split("/")[0],
            "artist_email": parse_data(row[1]).split("/")[1],
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
            "total_routenote_revenue": 0.00,
        }
        latest_bmr_day_year = (
            int(row[2][-4:])
            if int(row[2][-4:]) > latest_bmr_day_year
            else latest_bmr_day_year
        )

artist_info_data = {}
with open(artist_info_file_name, newline="") as artist_info_csv_file:
    artist_info_reader = csv.reader(artist_info_csv_file, delimiter=",")
    next(artist_info_reader, None)
    for row in artist_info_reader:
        artist_info_data[parse_data(row[2])] = {
            "observed_preferred_name": parse_data(row[0]),
            "catalog_releases": parse_data(row[1]),
            "observed_preferred_contact_method": parse_data(row[3]),
            "preferred_payment_method": parse_data(row[4]),
            "paypal_id": parse_data(row[5]),
            "zelle_id": parse_data(row[6]),
            "is_international_artist": parse_data(row[7]) == "yes",
        }

routenote_revenue_data = None
if routenote_revenue_data_file_name:
    routenote_revenue_data = {}
    with open(
        routenote_revenue_data_file_name, newline=""
    ) as routenote_revenue_csv_file:
        routenote_revenue_reader = csv.reader(routenote_revenue_csv_file, delimiter=",")
        next(routenote_revenue_reader, None)
        for row in routenote_revenue_reader:
            routenote_revenue_data_item = {
                "date": f"{parse_data(row[9])[:2]}/01/{parse_data(row[10])}",
                "platform": "routenote",
                "item_type": "track" if parse_data(row[2]) else "album",
                "album_artist": parse_data(row[5]),
                "item_name": (
                    parse_data(row[2]) if parse_data(row[2]) else parse_data(row[4])
                ),
                "retailer": parse_data(row[11]),
                "retailer_currency": parse_data(row[12]),
                "customer_territory": parse_data(row[13]),
                "download_unit_count": parse_data(row[15]),
                "stream_unit_count": parse_data(row[17]),
                "total_revenue_usd": parse_data(row[18]),
                "bandcamp_item_price": "Not Applicable",
                "bandcamp_quantity": "Not Applicable",
                "bandcamp_sub_total": "Not Applicable",
                "bandcamp_additional_fan_contribution": "Not Applicable",
                "bandcamp_transaction_fee": "Not Applicable",
                "bandcamp_revenue_fee": "Not Applicable",
                "paypal_payout_fee": calculate_paypal_fee(
                    parse_data(float(row[18])), 0.045
                ),
                "net_amount": parse_data(row[18]),
                "bandcamp_buyer_country": "Not Applicable",
                "catalog_number": release_catalog_number_by_upc_hash[
                    parse_data(row[8])
                ],
            }
            if (
                parse_data(release_catalog_number_by_upc_hash[row[8]])
                not in routenote_revenue_data
            ):
                routenote_revenue_data[
                    release_catalog_number_by_upc_hash[parse_data(row[8])]
                ] = [routenote_revenue_data_item]
            else:
                routenote_revenue_data[
                    release_catalog_number_by_upc_hash[parse_data(row[8])]
                ].append(routenote_revenue_data_item)


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
                "platform": "bandcamp",
                "item_type": parse_data(row[2]),
                "artist": parse_data(row[4]),
                "item_name": parse_data(row[3]),
                "retailer": "Not Applicable",
                "retailer_currency": "Not Applicable",
                "customer_territory": "Not Applicable",
                "download_unit_count": "Not Applicable",
                "stream_unit_count": "Not Applicable",
                "total_revenue_usd": "Not Applicable",
                "item_price": parse_data(row[6]),
                "quantity": parse_data(row[7]),
                "sub_total": parse_data(row[9]),
                "additional_fan_contribution": parse_data(row[10]),
                "transaction_fee": parse_data(row[16]),
                "bandcamp_revenue_fee": parse_data(row[22]),
                "paypal_payout_fee": calculate_paypal_fee(
                    parse_data(float(row[27])), 0.01
                ),
                "net_amount": parse_data(row[27]),
                "buyer_country": parse_data(row[47]),
                "catalog_number": parse_data(row[32]),
            }
            if parse_data(row[32]) not in bandcamp_sales_data:
                bandcamp_sales_data[parse_data(row[32])] = [bandcamp_sale]
            else:
                bandcamp_sales_data[parse_data(row[32])].append(bandcamp_sale)


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
        amount_received = float(
            subscription_revenue_data[subscriber_id]["amount_received"]
        )
        if subscription_revenue_data[subscriber_id]["tier_2_subscriber"]:
            amount_received -= 12.87
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
            revenue_share_owed += amount_received / float(
                bmr_day_subscriber_split_count
            )
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
            revenue_share_owed += amount_received / float(12)
    return revenue_share_owed


def calculate_mastering_fee_left_to_recover(
    release_catalog_number: str, total_revenue: float
) -> float | str:
    remaining_amount = "Not Applicable"
    if (
        release_info_data[release_catalog_number]["mastering_opt_in"]
        and release_info_data[release_catalog_number][
            "mastering_fee_amount_left_to_recover"
        ]
        != 0.00
    ):
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
            artist, _, split_amount = split.partition("=")
            if artist in distribution_rules["recording_artists"]:
                distribution_rules["recording_artists"][artist][
                    "payable_recordings"
                ].append(music_recording_item)
            else:
                distribution_rules["recording_artists"][artist] = {
                    "payable_recordings": [music_recording_item]
                }

            distribution_rules[music_recording_item][artist] = split_amount

    return distribution_rules


def create_payout_csv(
    release_catalog_number: str,
    artist_name: str | None = None,
    distribution_rules: dict | None = None,
):
    release_catalog_number_report_id = release_catalog_number
    artist_email = (
        artist_name.split("/")[1]
        if artist_name
        else release_info_data[release_catalog_number]["artist_email"]
    )
    if release_info_data[release_catalog_number]["multiple_artist_release"]:
        release_catalog_number_report_id = (
            f"{artist_name.split('/')[0]}_{release_catalog_number}"
        )
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
        if (
            "routenote_revenue_by_artist"
            not in release_info_data[release_catalog_number]
            or not release_info_data[release_catalog_number][
                "routenote_revenue_by_artist"
            ]
        ):
            release_info_data[release_catalog_number]["routenote_revenue_by_artist"] = {
                artist: 0.00
            }
        else:
            release_info_data[release_catalog_number]["routenote_revenue_by_artist"][
                artist
            ] = 0.00
        if (
            "total_revenue_by_artist" not in release_info_data[release_catalog_number]
            or not release_info_data[release_catalog_number]["total_revenue_by_artist"]
        ):
            release_info_data[release_catalog_number]["total_revenue_by_artist"] = {
                artist: 0.00
            }
        else:
            release_info_data[release_catalog_number]["total_revenue_by_artist"][
                artist
            ] = 0.00
    with open(
        f"generated-files/{current_date}_{release_catalog_number_report_id}_revenue_report.csv",
        "w",
        newline="",
    ) as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        routenote_release_revenue_data = []
        if routenote_revenue_data and release_catalog_number in routenote_revenue_data:
            routenote_release_revenue_data = routenote_revenue_data[
                release_catalog_number
            ]
        bandcamp_release_sales_data = []
        if release_catalog_number in bandcamp_sales_data:
            bandcamp_release_sales_data = bandcamp_sales_data[release_catalog_number]
        csvwriter.writerow(CSV_ROWS)
        if len(routenote_release_revenue_data):
            for revenue_data_item in routenote_release_revenue_data:
                release_info_data[release_catalog_number][
                    "total_routenote_revenue"
                ] += float(revenue_data_item["net_amount"]) - float(
                    revenue_data_item["paypal_payout_fee"]
                )
                if not release_info_data[release_catalog_number][
                    "multiple_artist_release"
                ]:
                    csvwriter.writerow(revenue_data_item.values())
                else:
                    if revenue_data_item["item_type"] == "album":
                        if (
                            "overall_release"
                            in distribution_rules["recording_artists"][artist_name][
                                "payable_recordings"
                            ]
                        ):
                            distribution_owed_artist = (
                                "1"
                                if distribution_rules["overall_release"][artist_name]
                                == "100"
                                else f"0.{distribution_rules["overall_release"][artist_name.split('/')[1]]}"
                            )
                            release_info_data[release_catalog_number][
                                "routenote_revenue_by_artist"
                            ][artist] += (
                                float(revenue_data_item["net_amount"])
                                - float(revenue_data_item["paypal_payout_fee"])
                            ) * float(
                                distribution_owed_artist
                            )
                            csvwriter.writerow(revenue_data_item.values())
                    elif revenue_data_item["item_type"] == "track":
                        if (
                            revenue_data_item["item_name"]
                            in distribution_rules["recording_artists"][artist_name][
                                "payable_recordings"
                            ]
                        ):
                            distribution_owed_artist = (
                                "1"
                                if distribution_rules[revenue_data_item["item_name"]][
                                    artist_name
                                ]
                                == "100"
                                else f"0.{distribution_rules[revenue_data_item["item_name"]][artist_name.split('/')[1]]}"
                            )
                            release_info_data[release_catalog_number][
                                "routenote_revenue_by_artist"
                            ][artist] += (
                                float(revenue_data_item["net_amount"])
                                - float(revenue_data_item["paypal_payout_fee"])
                            ) * float(
                                distribution_owed_artist
                            )
                            csvwriter.writerow(revenue_data_item.values())

        else:
            csvwriter.writerow(
                ["No direct RouteNote Revenue this accounting cycle"] * len(CSV_ROWS)
            )
        if len(bandcamp_release_sales_data):
            for sale in bandcamp_release_sales_data:
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
                            distribution_owed_artist = (
                                "1"
                                if distribution_rules["overall_release"][artist_name]
                                == "100"
                                else f"0.{distribution_rules["overall_release"][artist_name]}"
                            )
                            release_info_data[release_catalog_number][
                                "bandcamp_revenue_by_artist"
                            ][artist] += (
                                float(sale["net_amount"])
                                - float(sale["paypal_payout_fee"])
                            ) * float(
                                distribution_owed_artist
                            )
                            csvwriter.writerow(sale.values())
                    elif sale["item_type"] == "track":
                        if (
                            sale["item_name"]
                            in distribution_rules["recording_artists"][artist_name][
                                "payable_recordings"
                            ]
                        ):
                            distribution_owed_artist = (
                                "1"
                                if distribution_rules[sale["item_name"]][artist_name]
                                == "100"
                                else f"0.{distribution_rules[sale["item_name"]][artist_name.split('/')[1]]}"
                            )
                            release_info_data[release_catalog_number][
                                "bandcamp_revenue_by_artist"
                            ][artist] += (
                                float(sale["net_amount"])
                                - float(sale["paypal_payout_fee"])
                            ) * float(
                                distribution_owed_artist
                            )
                            csvwriter.writerow(sale.values())
        else:
            csvwriter.writerow(
                ["No direct Bandcamp sales this accounting cycle"] * len(CSV_ROWS)
            )

        for _ in range(3):
            csvwriter.writerow([None] * len(CSV_ROWS))

        results_headers_artist_name = (
            artist_name.split("/")[0]
            if artist_name
            else release_info_data[release_catalog_number]["artist_name"]
        )

        results_headers = [
            "Total overall release revenue from direct Bandcamp sales",
            "Total artist-specific revenue from direct Bandcamp sales (relevant for multi-artist releases)",
            "Total overall release revenue from RouteNote distribution",
            "Total artist-specific revenue from RouteNote distribution (relevant for multi-artist releases)",
            f"Total overall release revenue from BMR Day Bandcamp Annual Subscriptions or Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']}",
            f"Total artist-specific revenue from BMR Day Bandcamp Annual Subscriptions or Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']} (relevant for multi-artist releases)",
            f"Total overall release revenue from direct Bandcamp sales + BMR Day Bandcamp Annual Subscriptions + Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']} + RouteNote Revenue",
            f"Total artist-specific revenue from direct Bandcamp sales + BMR Day Bandcamp Annual Subscriptions + Bandcamp annual Subscriptions purchased on or before {release_info_data[release_catalog_number]['release_date']}  + RouteNote Revenue (relevant for multi-artist releases)",
            "Amount of mastering fee left to recover for overall release before split",
            "Total revenue from overall release after mastering fee recovered",
            "Total artist-specific revenue from release after mastering fee recovered (relevant for multi-artist releases)",
            "Total overall artist(s) release split",
            f"{results_headers_artist_name} split (relevant for multi-artist releases)",
            "BMR Split",
            "Amount owed overall release",
            f"Amount Owed {results_headers_artist_name} (relevant for multi-artist releases)",
        ]
        csvwriter.writerow(results_headers)

        overall_release_subscription_revenue_share = (
            release_artist_specific_subscription_revenue_share
        ) = calculate_subscription_revenue_share_for_release(release_catalog_number)

        overall_total_net_revenue = artist_specific_total_net_revenue = (
            release_info_data[release_catalog_number]["total_bandcamp_revenue"]
            + overall_release_subscription_revenue_share
            + release_info_data[release_catalog_number]["total_routenote_revenue"]
        )

        mastering_fee_left = calculate_mastering_fee_left_to_recover(
            release_catalog_number, overall_total_net_revenue
        )

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
            total_revenue_after_mastering_fee_recovered = mastering_fee_left * -1.00
            total_artist_specific_revenue_after_mastering_fee_recovered = (
                "turned_a_profit_this_cycle"
            )
            mastering_fee_left = 0.00
        else:
            total_revenue_after_mastering_fee_recovered = (
                total_artist_specific_revenue_after_mastering_fee_recovered
            ) = 0.00

        total_net_revenue_after_mastering_fee_recovered = (
            artist_specific_total_net_revenue_after_mastering_fee_recovered
        ) = (
            overall_total_net_revenue
            if total_revenue_after_mastering_fee_recovered == "Not Applicable"
            else total_revenue_after_mastering_fee_recovered
        )

        if release_info_data[release_catalog_number]["multiple_artist_release"]:
            artist_specific_total_net_revenue = release_info_data[
                release_catalog_number
            ]["bandcamp_revenue_by_artist"][artist]

        if (
            release_info_data[release_catalog_number]["multiple_artist_release"]
            and "overall_release"
            in distribution_rules["recording_artists"][artist_name][
                "payable_recordings"
            ]
        ):
            release_artist_specific_subscription_revenue_share = (
                overall_release_subscription_revenue_share
                * float(
                    "1"
                    if distribution_rules["overall_release"][artist_name] == "100"
                    else f"0.{distribution_rules["overall_release"][artist_name]}"
                )
            )
            artist_specific_total_net_revenue += (
                release_artist_specific_subscription_revenue_share
            )

        if (
            release_info_data[release_catalog_number]["multiple_artist_release"]
            and total_artist_specific_revenue_after_mastering_fee_recovered
            == "turned_a_profit_this_cycle"
        ):
            artist_specific_total_net_revenue_after_mastering_fee_recovered = (
                float(artist_specific_total_net_revenue / overall_total_net_revenue)
                * total_revenue_after_mastering_fee_recovered
            )
        elif release_info_data[release_catalog_number]["multiple_artist_release"]:
            artist_specific_total_net_revenue_after_mastering_fee_recovered = (
                artist_specific_total_net_revenue
                if total_revenue_after_mastering_fee_recovered == "Not Applicable"
                else total_net_revenue_after_mastering_fee_recovered
            )

        release_results = [
            round(
                release_info_data[release_catalog_number]["total_bandcamp_revenue"], 3
            ),
            (
                round(
                    (
                        release_info_data[release_catalog_number][
                            "bandcamp_revenue_by_artist"
                        ][artist]
                        if release_info_data[release_catalog_number][
                            "multiple_artist_release"
                        ]
                        else release_info_data[release_catalog_number][
                            "total_bandcamp_revenue"
                        ]
                    ),
                    3,
                )
            ),
            round(
                release_info_data[release_catalog_number]["total_routenote_revenue"], 3
            ),
            (
                round(
                    (
                        release_info_data[release_catalog_number][
                            "routenote_revenue_by_artist"
                        ][artist]
                        if release_info_data[release_catalog_number][
                            "multiple_artist_release"
                        ]
                        else release_info_data[release_catalog_number][
                            "total_routenote_revenue"
                        ]
                    ),
                    3,
                )
            ),
            round(overall_release_subscription_revenue_share, 3),
            round(release_artist_specific_subscription_revenue_share, 3),
            round(overall_total_net_revenue, 3),
            round(artist_specific_total_net_revenue, 3),
            (
                round(mastering_fee_left, 3)
                if isinstance(mastering_fee_left, float)
                else mastering_fee_left
            ),
            round(total_net_revenue_after_mastering_fee_recovered, 3),
            round(artist_specific_total_net_revenue_after_mastering_fee_recovered, 3),
            (
                round(
                    (
                        total_net_revenue_after_mastering_fee_recovered * 0.60
                        if mastering_fee_left == "Not Applicable"
                        or mastering_fee_left == 0.00
                        else 0.00
                    ),
                    3,
                )
            ),
            (
                round(
                    (
                        artist_specific_total_net_revenue_after_mastering_fee_recovered
                        * 0.60
                        if mastering_fee_left == "Not Applicable"
                        or mastering_fee_left == 0.00
                        else 0.00
                    ),
                    3,
                )
            ),
            (
                round(
                    (
                        artist_specific_total_net_revenue_after_mastering_fee_recovered
                        * 0.40
                        if mastering_fee_left == "Not Applicable"
                        or (mastering_fee_left == 0.00 and not release_broke_even)
                        else overall_total_net_revenue
                    ),
                    3,
                )
            ),
            (
                round(
                    (
                        total_net_revenue_after_mastering_fee_recovered * 0.60
                        if mastering_fee_left == "Not Applicable"
                        or mastering_fee_left == 0.00
                        else 0.00
                    ),
                    3,
                )
            ),
            (
                round(
                    (
                        artist_specific_total_net_revenue_after_mastering_fee_recovered
                        * 0.60
                        if mastering_fee_left == "Not Applicable"
                        or mastering_fee_left == 0.00
                        else 0.00
                    ),
                    3,
                )
            ),
        ]
        csvwriter.writerow(release_results)

        if (
            "catalog_release_revenue" in artist_info_data[artist_email]
            and artist_info_data[artist_email]["catalog_release_revenue"] is not None
        ):
            artist_info_data[artist_email]["catalog_release_revenue"][
                release_catalog_number
            ] = round(
                (
                    artist_specific_total_net_revenue_after_mastering_fee_recovered
                    * 0.60
                    if mastering_fee_left == "Not Applicable"
                    or mastering_fee_left == 0.00
                    else 0.00
                ),
                3,
            )
        else:
            artist_info_data[artist_email]["catalog_release_revenue"] = {
                release_catalog_number: round(
                    (
                        artist_specific_total_net_revenue_after_mastering_fee_recovered
                        * 0.60
                        if mastering_fee_left == "Not Applicable"
                        or mastering_fee_left == 0.00
                        else 0.00
                    ),
                    3,
                )
            }
        if release_info_data[release_catalog_number]["multiple_artist_release"]:
            release_info_data[release_catalog_number]["total_routenote_revenue"] = 0.00
            release_info_data[release_catalog_number]["total_bandcamp_revenue"] = 0.00

    csv_to_pdf_table(
        f"generated-files/{current_date}_{release_catalog_number_report_id}_revenue_report.csv",
        f"generated-files/{current_date}_{release_catalog_number_report_id}_revenue_report.pdf",
        release_catalog_number_report_id,
    )


for release_catalog_number in release_info_data:
    artist_split_distribution_by_track_and_overall_release = None
    if (
        release_catalog_number not in RELEASES_NOT_INCLUDED_IN_BMR_DAY_PAYOUTS
        or (release_catalog_number != "BMRX001" and "BMR000" in bandcamp_sales_data)
        or routenote_revenue_data
    ):
        if release_info_data[release_catalog_number]["multiple_artist_release"]:
            distribution_rules = (
                parse_artist_split_distribution_by_track_and_overall_release(
                    release_catalog_number
                )
            )
            for index, artist in enumerate(distribution_rules["recording_artists"]):
                distribution_rules["current_index"] = index
                create_payout_csv(release_catalog_number, artist, distribution_rules)
        else:
            create_payout_csv(release_catalog_number)

for artist_name, artist_metadata in artist_info_data.items():
    artist_email_starter_text_txt_file_name = f"generated-files/{artist_name.split('@')[0]}.txt"
    itemized_catalog_release_payouts_text = ""
    total_amount_owed = 0.00
    if "catalog_release_revenue" in artist_metadata:
        for catalog_number, amount_owed in artist_metadata[
            "catalog_release_revenue"
        ].items():
            itemized_catalog_release_payouts_text += (
                f"We owe you ${amount_owed} for {catalog_number}. "
            )
            total_amount_owed += amount_owed
    email_subject = f"<EMAIL SUBJECT>: {artist_metadata["catalog_releases"].replace(";", ", ")} Accounting{" + Payout" if total_amount_owed else ""} ({current_date})"
    payout_method = (
        artist_metadata["preferred_payment_method"]
        if artist_metadata["preferred_payment_method"] == "zelle"
        and total_amount_owed >= 1.00
        else "paypal"
    )
    payment_method_id = artist_metadata[f"{payout_method}_id"]
    payment_method_name_format = "PayPal" if payout_method == "paypal" else "Zelle"
    payment_method_text = (
        f"Since we owe you less than $1 this payout cycle and our bank requires Zelle payouts to be $1 or more, I will send you ${total_amount_owed} via PayPal to your {payment_method_id} PayPal ID"
        if artist_metadata["preferred_payment_method"] == "zelle"
        and total_amount_owed < 1.00
        else f"I will send you the ${total_amount_owed} we owe you this payout cycle via {payment_method_name_format} to your {payment_method_id} {payment_method_name_format} ID"
    )
    payment_email_text = f"{payment_method_text} on Friday. If you would like me to send the ${total_amount_owed} to a different {payment_method_name_format} ID, please let me know before Friday."
    with open(artist_email_starter_text_txt_file_name, "w", encoding="utf-8") as file:
        file.write(f"{email_subject}\n\n\n\n\n")
        file.write(f"Hey {artist_metadata["observed_preferred_name"]},\n\n")
        file.write(
            f"I hope you're well! Here is the accounting for the past 6 months for: {artist_metadata["catalog_releases"].replace(";", ", ")}. {itemized_catalog_release_payouts_text}In total, we owe you ${total_amount_owed}.{payment_email_text if total_amount_owed else ""} {"" if routenote_revenue_data else f"There was not a payout from our distributor this payout cycle, so I've attached screenshots of available stats I could find for {artist_metadata["catalog_releases"].replace(";", ", ")} on our distributor's online dashboard."}\n\n"
        )
        file.write(
            f"<INSERT_PERSONAL_NOTE_TO_{artist_metadata["observed_preferred_name"]}_HERE>\n\n"
        )
        file.write("Be well,\nPatrick @ BMR")
