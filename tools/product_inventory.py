"""Auditable product inventory; coverage never implies visual completeness."""
from collections import Counter
import math

def inventory(data):
    rows=data.get('products',[])
    counts=Counter(p.get('page') for p in rows)
    pages=[{'page':i,'productCount':counts[i],'reviewStatus':'requires-visual-review'} for i in range(1,len(data['pages'])+1)]
    return dict(schemaVersion=1,market=data['market'],editionId=data['id'],
        validFrom=data['validFrom'],validTo=data['validTo'],source=data['url'],
        completeness='unverified',method='ocr' if data['market']=='Effe Gros' else 'structured-source',
        productCount=len(rows),pages=pages,products=rows,
        pagesWithoutProducts=[p['page'] for p in pages if not p['productCount']],
        note='Inventario da verificare sul volantino: pagine coperte non significa tutti i prodotti riconosciuti.')

def app_products(rows):
    # Current Android versions reject a whole manifest if a single price is null.
    # Keep those captions in the inventory, separately from comparable offers.
    return [p for p in rows if isinstance(p.get('price'),(int,float)) and not isinstance(p['price'],bool) and math.isfinite(p['price']) and p['price']>0]
