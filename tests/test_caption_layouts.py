import unittest,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effe_layouts import reviewed

class Captions(unittest.TestCase):
    def test_all_pages_and_edition_guard(self):
        expected=[18,20,21,35,18,34,44,49,48,46,47,47,49,49,47,10]
        for page,count in enumerate(expected,1):
            rows=reviewed(page,f'https://www.cedigros.com/202609090934-page_{page:02}.jpg')
            self.assertEqual(len(rows),count)
            for r in rows:
                x,y,w,h=r['caption'];self.assertGreater(w,0);self.assertGreater(h,0)
                self.assertTrue(0<=x<x+w<=1200 and 0<=y<y+h<=1269)
        self.assertIsNone(reviewed(4,'https://www.cedigros.com/another-edition-page_04.jpg'))
    def test_seed_is_complete_without_price_gate(self):
        d=json.loads((Path(__file__).resolve().parents[1]/'tools/seeds/effegros.json').read_text(encoding='utf8'))
        self.assertEqual(len(d['products']),582)
        page=[p for p in d['products'] if p['page']==4]
        self.assertEqual(len(page),35)
        self.assertTrue(all(p['price'] is not None for p in page))
        self.assertTrue(any(p['price'] is None and p['textBoxes'] for p in d['products']))
        self.assertEqual(len({p['id'] for p in d['products']}),582)
        self.assertFalse(any(p['name'].startswith('Articolo pagina') for p in d['products']))
if __name__=='__main__':unittest.main()
