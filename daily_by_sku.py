"""Агрегация выгрузки заказов sales.csv в отчёт daily_by_sku.csv (артикул × день).

Запуск:
    python3 daily_by_sku.py [путь_к_sales.csv] [путь_к_результату.csv]
"""

import csv
import sys
from collections import defaultdict

STATUS_ALIASES = {
    "delivered": "delivered",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def normalize_status(raw):
    """Приводит статус к delivered/cancelled, исправляя регистр, пробелы и опечатки."""
    status = STATUS_ALIASES.get(raw.strip().lower())
    if status is None:
        raise ValueError(f"неизвестный статус заказа: {raw!r}")
    return status


def read_orders(path):
    """Читает выгрузку и возвращает уникальные заказы: {order_id: строка}.

    Повтор order_id считается дублем. Если дубль отличается по содержимому,
    это уже не копия, а противоречие в данных, — тогда падаем с ошибкой.
    """
    orders = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            row = {key: value.strip() for key, value in row.items()}
            row["status"] = normalize_status(row["status"])

            order_id = row["order_id"]
            if order_id in orders:
                if orders[order_id] != row:
                    raise ValueError(f"строка {line_no}: заказ {order_id} повторяется с другими данными")
                continue
            orders[order_id] = row
    return orders


def aggregate(orders):
    """Считает orders и revenue по ключу (sku, order_date)."""
    stats = defaultdict(lambda: {"orders": 0, "revenue": 0})
    for row in orders.values():
        day = stats[(row["sku"], row["order_date"])]
        day["orders"] += 1
        if row["status"] == "delivered":
            day["revenue"] += int(row["quantity"]) * int(row["price"])
    return stats


def write_report(stats, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["sku", "order_date", "orders", "revenue"])
        for (sku, order_date) in sorted(stats):
            day = stats[(sku, order_date)]
            writer.writerow([sku, order_date, day["orders"], day["revenue"]])


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "daily_by_sku.csv"

    orders = read_orders(input_path)
    stats = aggregate(orders)
    write_report(stats, output_path)
    print(f"Уникальных заказов: {len(orders)}, строк в отчёте: {len(stats)} -> {output_path}")


if __name__ == "__main__":
    main()
