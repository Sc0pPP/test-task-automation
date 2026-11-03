import csv
import os
import tempfile
import unittest

from daily_by_sku import aggregate, normalize_status, read_orders, write_report

SAMPLE = """order_id,order_date,sku,quantity,price,status
1,2026-09-01,B-1,2,100,delivered
1,2026-09-01,B-1,2,100,delivered
2,2026-09-01,B-1,1,100,cancelled
3,2026-09-01,B-1,3,100,Delivered
4,2026-09-02,B-1,1,100,canceled
5,2026-09-01,A-1,1,50,DELIVERED
6,2026-09-01,A-1,,50,cancelled
"""


class DailyBySkuTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.tmp.name, "sales.csv")
        self.output_path = os.path.join(self.tmp.name, "out.csv")
        with open(self.input_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE)

    def tearDown(self):
        self.tmp.cleanup()

    def run_report(self):
        write_report(aggregate(read_orders(self.input_path)), self.output_path)
        with open(self.output_path, encoding="utf-8") as f:
            return list(csv.reader(f))

    def test_report(self):
        self.assertEqual(self.run_report(), [
            ["sku", "order_date", "orders", "revenue"],
            ["A-1", "2026-09-01", "2", "50"],      # отменённый с пустым quantity считается в orders
            ["B-1", "2026-09-01", "3", "500"],     # дубль заказа 1 не удваивает: 2*100 + 3*100
            ["B-1", "2026-09-02", "1", "0"],       # canceled -> cancelled, выручки нет
        ])

    def test_status_typos(self):
        for raw in ["delivered ", "Delivered", "DELIVERED"]:
            self.assertEqual(normalize_status(raw), "delivered")
        for raw in ["Cancelled", "CANCELLED", "canceled"]:
            self.assertEqual(normalize_status(raw), "cancelled")
        with self.assertRaises(ValueError):
            normalize_status("returned")

    def test_conflicting_duplicate_fails(self):
        with open(self.input_path, "a", encoding="utf-8") as f:
            f.write("1,2026-09-01,B-1,5,100,delivered\n")
        with self.assertRaises(ValueError):
            read_orders(self.input_path)


if __name__ == "__main__":
    unittest.main()
