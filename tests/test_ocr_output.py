import sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from PIL import Image
from effe_ocr import recognize
class OcrOutput(unittest.TestCase):
 def test_explicit_tsv_output_even_without_system_config_files(self):
  tsv='level\tconf\ttext\tleft\ttop\twidth\theight\n5\t95\tPane\t24\t24\t60\t40\n'
  with tempfile.TemporaryDirectory() as tmp,patch('effe_ocr.subprocess.run',return_value=SimpleNamespace(stdout=tsv)) as run:
   words=recognize(Image.new('RGB',(100,100)),(0,0,100,100),Path(tmp),'read')
   self.assertEqual(words[0]['t'],'Pane')
   self.assertIn('tessedit_create_tsv=1',run.call_args.args[0])
 def test_plain_text_is_an_error_not_an_empty_catalog(self):
  with tempfile.TemporaryDirectory() as tmp,patch('effe_ocr.subprocess.run',return_value=SimpleNamespace(stdout='Pane')):
   with self.assertRaisesRegex(ValueError,'TSV'):recognize(Image.new('RGB',(100,100)),(0,0,100,100),Path(tmp),'read')
