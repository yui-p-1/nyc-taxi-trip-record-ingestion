from flask import Flask
import requests
from google.cloud import storage
from google.cloud import bigquery
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

BUCKET_NAME = "nyc-taxi-dwh-raw"
PREFIX = "yellow/"


def get_latest_available_month():
    """
    NYC Taxi が公開している最新年月を取得する。
    過去12か月をチェックし、存在する中で最新を返す。
    """
    today = datetime.today()
    available_months = []

    for i in range(0, 12):
        dt = today - relativedelta(months=i)
        year_month = dt.strftime("%Y-%m")
        file = f"yellow_tripdata_{year_month}.parquet"
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{file}"

        try:
            r = requests.get(url, stream=True, timeout=10)
            if r.status_code == 200:
                available_months.append(year_month)
            r.close()
        except requests.RequestException:
            continue

    if not available_months:
        return None

    latest = max(available_months)
    print(f"Available months: {available_months}")
    print(f"Selected latest month: {latest}")

    return latest


def get_latest_month_in_gcs(bucket_name, prefix):
    """
    GCS にすでに存在する最新年月を返す。
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))

    months = []
    for blob in blobs:
        parts = blob.name.split('/')
        if len(parts) >= 3:
            year = parts[1]
            filename = parts[2]
            if filename.startswith("yellow_tripdata_"):
                months.append(f"{year}-{filename[17:24]}")

    if not months:
        return None

    latest = max(months)
    print(f"Latest month in GCS: {latest}")
    return latest


@app.route("/")
def pipeline():
    # ① NYCサイトの最新公開月
    latest_nyc_month = get_latest_available_month()
    if not latest_nyc_month:
        return "No NYC Taxi file found for recent months."

    # ② GCSにすでにある最新月
    latest_gcs_month = get_latest_month_in_gcs(BUCKET_NAME, PREFIX)

    if latest_nyc_month == latest_gcs_month:
        return f"Latest data ({latest_nyc_month}) already exists in GCS."

    # ③ ファイルダウンロード
    file = f"yellow_tripdata_{latest_nyc_month}.parquet"
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{file}"

    print(f"Downloading {file}...")

    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            return f"File {file} not found on NYC site."
    except requests.RequestException as e:
        return f"Error downloading file: {e}"

    # ④ GCSアップロード
    year, month = latest_nyc_month.split("-")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"yellow/{year}/{file}")
    blob.upload_from_string(r.content, content_type="application/octet-stream")

    print(f"Uploaded {file} to gs://{BUCKET_NAME}/yellow/{year}/")

    # ⑤ BigQuery 外部テーブル作成
    bq = bigquery.Client()
    table_name = f"raw.ext_{latest_nyc_month.replace('-', '_')}"

    query = f"""
    CREATE OR REPLACE EXTERNAL TABLE {table_name}
    OPTIONS(
      format='PARQUET',
      uris=['gs://{BUCKET_NAME}/yellow/{year}/{file}']
    )
    """

    print(f"Creating external table {table_name}...")

    bq.query(query).result()

    return f"Pipeline complete for {latest_nyc_month}."
