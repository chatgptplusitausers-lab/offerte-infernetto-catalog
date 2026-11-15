import datetime as dt
import json
import sys
import tempfile
import unittest
import types
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import flyer_sources as f
import publish_catalogs as pub

class Sources(unittest.TestCase):
    def test_dates(self):
        for text,start,end in [("Dall'11 al 22 Settembre 2026",'2026-09-11','2026-09-22'),('Dal 21 Agosto all’1 Settembre 2026','2026-08-21','2026-09-01'),('Valido dal 24 settembre al 4 ottobre 2026.','2026-09-24','2026-10-04'),('Dal 28 dicembre al 5 gennaio 2027','2026-12-28','2027-01-05')]:
            self.assertEqual(tuple(x.isoformat() for x in f.parse_period(text)),(start,end))
    def test_reused_id_is_new_edition(self):
        def parse(stamp):return f.parse_effe(f"Dall'11 al 22 Settembre 2026 2 pagine <img src='/media/com_myegojwt/contents/flyers/198/{stamp}-page_02.jpg'><img src='/media/com_myegojwt/contents/flyers/198/{stamp}-page_01.jpg'>",'https://www.cedigros.com/insegne/effepiu?view=flyer&id=198','198')
        self.assertNotEqual(parse('a')['id'],parse('b')['id'])
        self.assertTrue(parse('a')['pages'][0].endswith('page_01.jpg'))
    def test_missing_pages(self):
        with self.assertRaises(ValueError):f.parse_effe("Dal 11 al 22 settembre 2026 2 pagine <img src='/media/com_myegojwt/contents/flyers/198/a-page_01.jpg'>",'https://www.cedigros.com/','198')
    def test_current_before_future(self):
        past={'validFrom':'2026-08-01','validTo':'2026-08-30','pages':['p'],'products':[1]}
        live={**past,'validFrom':'2026-09-10','validTo':'2026-09-22'}
        future={**past,'validFrom':'2026-09-24','validTo':'2026-10-04','products':list(range(20))}
        day=dt.date(2026,9,21)
        self.assertIs(f.choose_current([past,live,future],day),live)
        self.assertTrue(f.choose_current([past,future],day)['upcoming'])
        with self.assertRaises(ValueError):f.choose_current([past],day)
    def test_partial_outage_publishes_healthy_market(self):
        d=f.edition('Lidl','https://example.com',['https://publications.nuovovolantino.it/a.webp'],dt.date(2026,9,17),dt.date(2026,9,23),[],'fixture')
        def fail():raise OSError('timeout')
        with tempfile.TemporaryDirectory() as tmp,patch.dict(pub.MARKETS,{'Lidl':('lidl',lambda:d),'Eurospin':('eurospin',fail)},clear=True):
            result=pub.collect(Path(tmp))
            self.assertEqual(result['markets']['Eurospin']['status'],'unavailable')
            self.assertTrue((Path(tmp)/'latest-lidl.json').exists())
    def test_total_outage_fails(self):
        def fail():raise OSError('timeout')
        with tempfile.TemporaryDirectory() as tmp,patch.dict(pub.MARKETS,{'Lidl':('lidl',fail)},clear=True):
            with self.assertRaises(RuntimeError):pub.collect(Path(tmp))

    def test_ocr_failure_keeps_new_flyer_without_old_products(self):
        current=f.edition('Effe Gros','https://example.com/new',['https://www.cedigros.com/new.jpg'],dt.date(2026,11,13),dt.date(2026,11,23),[],'fixture')
        old={**current,'id':'old','pages':['https://www.cedigros.com/old.jpg'],'products':[{'name':'Old offer'}]}
        def fail(data):
            data['products']=[{'name':'Partial OCR result'}]
            raise ValueError('OCR non ha estratto prodotti')
        ocr=types.SimpleNamespace(VERSION='test',enrich=fail)
        with tempfile.TemporaryDirectory() as tmp,patch.dict(pub.MARKETS,{'Effe Gros':('effegros',lambda:current)},clear=True),patch.dict(sys.modules,{'effe_ocr':ocr}),patch.object(pub,'get',return_value=json.dumps(old)):
            result=pub.collect(Path(tmp),'https://example.com/catalog')
            saved=json.loads((Path(tmp)/'latest-effegros.json').read_text())
            self.assertEqual(result['markets']['Effe Gros']['status'],'ok')
            self.assertIn('Estrazione prodotti',result['markets']['Effe Gros']['error'])
            self.assertEqual(saved['validFrom'],'2026-11-13')
            self.assertEqual(saved['pages'],current['pages'])
            self.assertEqual(saved['products'],[])
            self.assertTrue(saved['staleProducts'])
            self.assertEqual(saved['ocrStatus'],'unavailable')

if __name__=='__main__':unittest.main()
