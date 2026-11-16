import unittest,sys
from pathlib import Path
import cv2,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from product_mapping import locate,locate_template
class Mapping(unittest.TestCase):
 def test_exact_crop_with_resize(self):
  rng=np.random.default_rng(42);page=rng.integers(0,256,(600,500),dtype=np.uint8);page=cv2.GaussianBlur(page,(3,3),0);crop=page[180:380,70:270];crop=cv2.resize(crop,(300,300));b=locate(page,crop);self.assertIsNotNone(b);self.assertAlmostEqual(b['x'],70/500,delta=.015);self.assertAlmostEqual(b['y'],180/600,delta=.015)
 def test_template_recovers_low_feature_crop(self):
  rng=np.random.default_rng(42);page=rng.integers(0,256,(600,500),dtype=np.uint8);box=locate_template(page,page[180:380,70:270]);self.assertIsNotNone(box);self.assertAlmostEqual(box["x"],.14,delta=.01)
 def test_unrelated_picture_is_not_mapped(self):
  rng=np.random.default_rng(42);self.assertIsNone(locate(rng.integers(0,256,(600,500),dtype=np.uint8),rng.integers(0,256,(200,200),dtype=np.uint8)))
