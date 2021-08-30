import json, logging, os, psutil, requests, sys, traceback

from datetime import datetime
from ischedule import schedule, run_loop
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from os import environ

def create_logger() :
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(format)
    log.addHandler(ch)
    return log

log = create_logger()

pid = os.getpid()

def die():
    log.fatal("Dying.")
    thisApp = psutil.Process(pid)
    thisApp.terminate()

def parse_metrics_config(config_line):
    if not config_line or config_line.strip() == "":
        log.fatal("No metrics found in config. At least 1 metric must be configured!")
        die()
    parts = config_line.split(",")
    result = []
    for part in parts:
        if part.strip() == "":
            continue
        result.append(part.strip())
    if len(result) < 1 or len(result) > 5:
        log.fatal("At least one metric is required and no more than 5 are allowed. Found %d." % len(result))
        die()
    return result

def construct_data_url(base_url, metrics):
    result = base_url
    for metric in metrics:
        log.info("base_url => [%s]; Result => [%s]; metric => [%s]" % (base_url, result, metric))
        result = "%s&metric=%s" % (result, metric)
    return result

influx_url = environ.get('DOCKER_INFLUXDB_HOST')
influx_org = environ.get('DOCKER_INFLUXDB_INIT_ORG')
influx_bucket = environ.get('DOCKER_INFLUXDB_INIT_BUCKET')
influx_token = environ.get('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')

data_url = environ.get('DATA_URL')
fetch_interval_mins = float(environ.get('FETCH_INTERVAL_MINUTES'))
fetch_interval_seconds = fetch_interval_mins * 60
json_archive_path = os.path.abspath(environ.get('JSON_ARCHIVE_DIR'))
metrics_str = environ.get('DATA_METRICS')
metrics = parse_metrics_config(metrics_str)
data_url = construct_data_url(data_url, metrics)

log.info("Initialising UK Covid Data Fetcher on PID %s ..." % pid)
log.info("Fetch poll interval set to %s minutes (%s seconds)." % (fetch_interval_mins, fetch_interval_seconds))
if not data_url:
    log.fatal("Missing data API URL to fetch data from.")
log.info("Influx DB URL [%s], org [%s], bucket [%s]." % (influx_url, influx_org, influx_bucket))
log.info("API responses will be archived under directory: [%s]." % json_archive_path)

def save_covid_data(data_json):
    log.info("Saving...")
    influx_client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
    influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    json_records = data_json['body']
    for json_record in json_records:
        timestamp = datetime.strptime(json_record['date'], '%Y-%m-%d')
        record = Point("uk_covid_day") \
            .time(timestamp) \
            .tag("areaType", json_record['areaType']) \
            .tag("areaCode", json_record['areaCode']) \
            .tag("areaName", json_record['areaName'])
        for metric in metrics:
            record = record.field(metric, json_record[metric])
        influx_write_api.write(bucket=influx_bucket, record=record)
    influx_write_api.close()
    influx_client.close()
    log.info("Latest data persisted to Influx DB.")

def build_save_path():
    return "%s/%s.json" % (json_archive_path, datetime.today().strftime('%Y-%m-%d_%H%M%S'))
    
def fetch_data():
    log.info("Fetching data from: [%s]" % data_url)
    response = None
    try:
        response = requests.get(data_url)
    except Exception as e:
        log.error(traceback.format_exc())
        die()
    status_code = response.status_code
    log.info("Received status code: %s" % status_code)
    log.debug("Received output: %s" % response.text)
    json_output = response.json()
    save_path = build_save_path()
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent = 4)
    log.info("Data archived under: [%s]" % save_path)
    save_covid_data(json_output)

fetch_data()
schedule(fetch_data, interval=fetch_interval_seconds)

run_loop()