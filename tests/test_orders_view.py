import os
import unittest
import importlib


class OrdersViewTests(unittest.TestCase):
    def setUp(self):
        os.environ['FLASK_ENV'] = 'testing'
        import app as app_module
        self.app_module = app_module
        self.client = app_module.app.test_client()

    def test_process_orders_list_with_data(self):
        rows = [{
            'Name': 'Datavault AI Inc',
            'Symbol': 'DVLT',
            'Side': 'Buy',
            'Status': 'Filled',
            'Filled': '23013',
            'Total Qty': '23013',
            'Price': '1.73',
            'Avg Price': '$1.73',
            'Placed Time': '11/04/2025 13:51:17 EST',
            'Filled Time': '11/04/2025 14:07:30 EST',
            'Total Value': '39812.49'
        }]
        out = self.app_module.process_orders_list(rows)
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertTrue(o['id'].startswith('ORD-'))
        self.assertEqual(o['customer'], 'Datavault AI Inc')
        self.assertEqual(o['date'], '11/04/2025')
        self.assertEqual(o['status'], 'Filled')
        self.assertAlmostEqual(o['total'], 39812.49, places=2)

    def test_process_orders_list_empty(self):
        out = self.app_module.process_orders_list([])
        self.assertEqual(out, [])

    def test_api_data_returns_orders_list(self):
        orig_get = self.app_module.get_sheet_data
        def fake_get(spreadsheet_id=None, worksheet_gid=None):
            if spreadsheet_id == self.app_module.ORDERS_SPREADSHEET_ID and worksheet_gid == self.app_module.ORDERS_WORKSHEET_GID:
                return [{
                    'Name': 'Datavault AI Inc',
                    'Symbol': 'DVLT',
                    'Side': 'Buy',
                    'Status': 'Filled',
                    'Filled': '10',
                    'Price': '2.00',
                    'Total Value': '20.00',
                    'Placed Time': '11/04/2025 13:51:17 EST'
                }]
            return [{'Date': '01/01/2024', 'Amount': '0'}]
        self.app_module.get_sheet_data = fake_get
        resp = self.client.get('/api/data')
        self.app_module.get_sheet_data = orig_get
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('orders_list', data)
        self.assertGreaterEqual(len(data['orders_list']), 1)
        self.assertIn('id', data['orders_list'][0])
        self.assertIn('customer', data['orders_list'][0])
        self.assertIn('date', data['orders_list'][0])
        self.assertIn('status', data['orders_list'][0])
        self.assertIn('total', data['orders_list'][0])

    def test_template_contains_orders_view_elements(self):
        p = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
        with open(p, 'r', encoding='utf-8') as f:
            html = f.read()
        self.assertIn('Orders', html)
        self.assertIn('Order ID', html)
        self.assertIn('Customer', html)
        self.assertIn('Order Date', html)
        self.assertIn('Status', html)
        self.assertIn('Total Amount', html)
        self.assertIn('Actions', html)


if __name__ == '__main__':
    unittest.main()