import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from product_inventory import inventory,app_products
class Inventory(unittest.TestCase):
 def test_unpriced_captions_remain_in_inventory(self):
  rows=[{'id':'a','page':1,'name':'Pane','price':None},{'id':'b','page':2,'name':'Latte','price':1.2}]
  report=inventory(dict(market='Effe Gros',id='new',validFrom='2026-11-13',validTo='2026-11-23',url='https://example.com',pages=['a','b','c'],products=rows))
  self.assertEqual(report['productCount'],2)
  self.assertEqual(report['pagesWithoutProducts'],[3])
  self.assertEqual(report['completeness'],'unverified')
  self.assertEqual(app_products(rows),[rows[1]])
 def test_invalid_prices_cannot_break_android_catalog(self):
  rows=[{'price':p} for p in [None,0,-1,float('nan'),float('inf'),'1.2',True,1.2]]
  self.assertEqual(app_products(rows),[{'price':1.2}])
