"""Publish each available source, preserve dated cache on a source failure."""
import argparse, concurrent.futures, datetime as dt, json, os
from pathlib import Path
from flyer_sources import discover_effe, discover_nuovo, get, today
from product_inventory import inventory, app_products

MARKETS={'Effe Gros':('effegros',discover_effe),'Lidl':('lidl',lambda:discover_nuovo('Lidl','lidl')),'Eurospin':('eurospin',lambda:discover_nuovo('Eurospin','eurospin'))}

def collect(output, previous=None):
    output.mkdir(parents=True,exist_ok=True)
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    index={'schemaVersion':2,'checkedAt':stamp,'markets':{}}
    successful=0; warnings=[]
    def load(item):
        market,(slug,fn)=item
        try:
            data=fn()
            if market=='Effe Gros':
                # Product extraction is optional: never discard a newly discovered
                # flyer or attach products from a different edition when OCR fails.
                import copy
                flyer=copy.deepcopy(data)
                try:
                    from effe_ocr import enrich, VERSION
                    cached=None
                    if previous:
                        try:cached=json.loads(get(previous.rstrip('/')+'/latest-'+slug+'.json'))
                        except (OSError,ValueError):pass
                    if cached and cached.get('id')==data['id'] and cached.get('pages')==data['pages'] and cached.get('ocrVersion')==VERSION and cached.get('products'):
                        for field in ['products','offerCount','ocrVersion','ocrPages','inventoryProducts']:data[field]=cached.get(field)
                    else:data=enrich(data)
                except Exception as exc:
                    data=flyer
                    data.update(products=[],offerCount=0,ocrStatus='unavailable',ocrError=str(exc))
                    return market,slug,data,'Estrazione prodotti non disponibile: '+str(exc)
            return market,slug,data,None
        except Exception as e:return market,slug,None,str(e)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results=list(ex.map(load,MARKETS.items()))
    for market,slug,data,error in results:
        status='ok'
        if data:
            successful+=1
            if error:warnings.append(f'{market}: {error}')
            data.update(schemaVersion=2,checkedAt=stamp,sourceId=data['id'],staleProducts=not bool(data['products']))
        else:
            warnings.append(f'{market}: {error}')
            status='unavailable'
            if previous:
                try:
                    cached=json.loads(get(previous.rstrip('/')+'/latest-'+slug+'.json'))
                    if cached.get('market')==market and cached.get('schemaVersion')==2 and cached.get('pages'):
                        data=cached;status='cached'
                        seed=Path(__file__).parent/'seeds'/'effegros.json'
                        if market=='Effe Gros' and seed.exists():
                            known=json.loads(seed.read_text(encoding='utf-8'))
                            if known.get('id')==data.get('id') and known.get('pages')==data.get('pages') and known.get('ocrVersion')!=data.get('ocrVersion'):
                                data=known
                        # The store can remove its landing-page link before the
                        # printed expiry date. Recover text from the exact saved
                        # pages, retaining the original dates and cached status.
                        if market=='Effe Gros' and not data.get('products'):
                            from effe_ocr import enrich
                            data=enrich(data)
                except (OSError,ValueError):pass
        record={'status':status,'checkedAt':stamp,'error':error}
        if data:
            all_products=data.pop('inventoryProducts',None)
            if all_products is None:all_products=data['products']
            report=inventory({**data,'products':all_products})
            inventory_path='inventory-'+slug+'.json'
            (output/inventory_path).write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            # Preserve captions without a read price for reuse by the next run.
            data['inventoryProducts']=all_products
            data['products']=app_products(data['products'])
            data['offerCount']=len(data['products'])
            record.update(inventoryPath=inventory_path,productCount=len(all_products),completeness='unverified',pagesWithoutProducts=report['pagesWithoutProducts'])
            record.update(path='latest-'+slug+'.json',validFrom=data['validFrom'],validTo=data['validTo'],editionId=data['id'])
            data['sourceStatus']=status
            (output/record['path']).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        index['markets'][market]=record
    (output/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    summary=['## Aggiornamento volantini',f'Controllo: {stamp}']
    for market,record in index['markets'].items():
        summary.append(f"- {market}: {record['status']} ({record.get('validFrom','—')} / {record.get('validTo','—')})")
    summary+=warnings
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write('\n'.join(summary)+'\n')
    print('\n'.join(summary))
    for warning in warnings: print('::warning::'+warning.replace('\n',' '))
    # A complete outage is still an actionable failure, never silently green.
    if not successful: raise RuntimeError('Tutte le sorgenti non disponibili')
    return index

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--previous');args=ap.parse_args()
    collect(args.output,args.previous)
