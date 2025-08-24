import csv
import time


def exportar_log(data, log_file="trading_log.csv"):
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)
