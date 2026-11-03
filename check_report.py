"""Сверка daily_by_sku.csv с контрольными цифрами, посчитанными напрямую из sales.csv.

Контрольные цифры считаются здесь отдельно, без функций из daily_by_sku.py,
чтобы ошибка в основном скрипте не повторилась в проверке.

Запуск:
    python3 check_report.py [путь_к_sales.csv] [путь_к_daily_by_sku.csv]
"""

import csv
import sys

sales_path = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
report_path = sys.argv[2] if len(sys.argv) > 2 else "daily_by_sku.csv"

with open(sales_path, encoding="utf-8-sig", newline="") as f:
    raw_rows = list(csv.reader(f))[1:]

# Дубли убираем как одинаковые строки целиком, а не по order_id, как в основном скрипте
unique_rows = set(tuple(row) for row in raw_rows)
expected_orders = len(unique_rows)
expected_revenue = sum(
    int(qty) * int(price)
    for _, _, _, qty, price, status in unique_rows
    if status.strip().lower() == "delivered"
)

with open(report_path, encoding="utf-8", newline="") as f:
    report = list(csv.DictReader(f))

report_orders = sum(int(r["orders"]) for r in report)
report_revenue = sum(int(r["revenue"]) for r in report)
keys = [(r["sku"], r["order_date"]) for r in report]

checks = [
    ("строк в выгрузке", len(raw_rows), None),
    ("удалено дублей", len(raw_rows) - expected_orders, None),
    ("заказов всего", expected_orders, report_orders),
    ("выручка всего", expected_revenue, report_revenue),
    ("ключи sku+дата уникальны", len(keys), len(set(keys))),
    ("сортировка sku, дата", keys, sorted(keys)),
]

failed = False
for name, expected, actual in checks:
    if actual is None:
        print(f"  {name}: {expected}")
    elif expected == actual:
        shown = "ok" if isinstance(expected, list) else expected
        print(f"OK {name}: {shown}")
    else:
        failed = True
        print(f"FAIL {name}: ожидалось {expected}, в отчёте {actual}")

sys.exit(1 if failed else 0)
