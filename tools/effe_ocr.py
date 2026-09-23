"""Read flyer captions once on the server and retain their exact text rectangles."""
import concurrent.futures, csv, hashlib, io, json, os, re, subprocess, tempfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps
from flyer_sources import get
from effe_layouts import reviewed

VERSION='caption-regions-v9'

def sections(im):
    a=np.asarray(im.convert('RGB'))
    red=(((a.max(axis=2).astype(int)-a.min(axis=2))>65)&(a.min(axis=2)<130)|(a.max(axis=2)<50)).astype('uint8')*255
    h=cv2.morphologyEx(red,cv2.MORPH_OPEN,np.ones((1,max(40,im.width//17)),np.uint8))
    v=cv2.morphologyEx(red,cv2.MORPH_OPEN,np.ones((max(40,im.height//18),1),np.uint8))
    barriers=cv2.dilate(h|v,np.ones((3,3),np.uint8))
    # Reconnect thin rules interrupted by JPEG compression. Their long spans
    # distinguish printed section boundaries from lettering and photographs.
    cols=np.where((v>0).sum(axis=0)>im.height*.55)[0]
    rows=np.where((h>0).sum(axis=1)>im.width*.65)[0]
    if len(cols)>10 and len(rows)>10:
        for x in cols:barriers[rows.min():rows.max()+1,x]=255
        for y in rows:barriers[y,cols.min():cols.max()+1]=255
    _,_,stats,_=cv2.connectedComponentsWithStats(255-barriers)
    return sorted([(int(x),int(y),int(w),int(h)) for x,y,w,h,area in stats[1:] if w>70 and h>65 and area>5000 and area/(w*h)>.85 and w<im.width*.96],key=lambda r:(r[1]//10,r[0]))

def circles(im):
    rgb=np.asarray(im.convert('RGB'));a=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    mask=(((rgb[:,:,0]>90)&(rgb[:,:,0]<180)&(rgb[:,:,1]<40)&(rgb[:,:,2]<65))|((a[:,:,0]>32)&(a[:,:,0]<78)&(a[:,:,1]>135)&(a[:,:,2]>70)&(a[:,:,2]<180))).astype('uint8')*255
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
    contours,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    boxes=[]
    for c in contours:
        x,y,w,h=cv2.boundingRect(c);area=cv2.contourArea(c);perimeter=cv2.arcLength(c,True)
        if 65<=w<=160 and 65<=h<=160 and .72<w/h<1.4 and area/(w*h)>.70 and perimeter and 4*np.pi*area/(perimeter*perimeter)>.5:boxes.append((x,y,w,h))
    return boxes

def recognize(im,rect,work,name,psm=6,threshold=None):
    x,y,w,h=rect;scale_x,scale_y=6,4;pad=24
    crop=im.crop((x,y,x+w,y+h)).resize((w*scale_x,h*scale_y),Image.Resampling.LANCZOS)
    if threshold is not None:crop=crop.convert('L').point(lambda v:255 if v>threshold else 0).convert('RGB')
    path=work/(name+'.png');ImageOps.expand(crop,border=pad,fill='white').save(path)
    env=os.environ.copy();env['OMP_THREAD_LIMIT']='1'
    result=subprocess.run([os.environ.get('TESSERACT_CMD','tesseract'),str(path),'stdout','-l','ita','--psm',str(psm),'tsv'],capture_output=True,text=True,encoding='utf-8',check=True,timeout=30,env=env)
    words=[]
    for r in csv.DictReader(result.stdout.splitlines(),delimiter='\t'):
        if r.get('level')!='5' or not r.get('text','').strip():continue
        if float(r['conf'])<25:continue
        words.append({'t':r['text'],'confidence':float(r['conf']),
            'x':x+max(0,(int(r['left'])-pad)/scale_x),'y':y+max(0,(int(r['top'])-pad)/scale_y),
            'w':int(r['width'])/scale_x,'h':int(r['height'])/scale_y})
    if not words and threshold is None:
        return recognize(im,rect,work,name+'-threshold',psm,120)
    return words

def rectangle(words,width,height):
    x=max(0,min(w['x'] for w in words)-3);y=max(0,min(w['y'] for w in words)-3)
    x1=min(width,max(w['x']+w['w'] for w in words)+3);y1=min(height,max(w['y']+w['h'] for w in words)+3)
    return dict(x=round(x/width,6),y=round(y/height,6),w=round((x1-x)/width,6),h=round((y1-y)/height,6))

def read_page(im,page,work):
    products=[]
    regions=[(r,False) for r in sections(im)]+[(r,True) for r in circles(im)]
    for ix,((x,y,w,h),circle) in enumerate(regions):
        # Captions sit along the bottom of the printed product section.
        # No cross-product proximity matching: both reads stay in this section.
        ph=min(45,max(27,int(h*.18)));pw=min(85,max(44,int(w*.26)))
        price_rect=(x+w-pw,y+h-ph,pw,ph)
        if circle:price_rect=(x+int(w*.16),y+int(h*.56),int(w*.72),int(h*.38))
        pwds=recognize(im,price_rect,work,f'{page}-{ix}-price',7)
        raw_price=' '.join(q['t'] for q in pwds)
        matches=re.findall(r'(?<!\d)(\d{1,3})\s*[,\.]\s*(\d{2})(?!\d)',raw_price)
        price=float(matches[-1][0]+'.'+matches[-1][1]) if matches else None
        if price is not None and not 0<price<1000:price=None
        nh=min(65,max(36,int(h*.23)))
        name_rect=(x,y+h-nh,max(30,w-pw),nh)
        if circle:name_rect=(x+int(w*.1),y+int(h*.1),int(w*.8),int(h*.52))
        words=recognize(im,name_rect,work,f'{page}-{ix}-name')
        labels=[q for q in words if re.search(r'[A-Za-zÀ-ÿ]{2}',q['t']) and not re.search(r'€/|€|\d[,\.]\d',q['t'])]
        # Some captions are printed vertically to the right of the photograph.
        if sum(len(q['t']) for q in labels)<10:
            words=recognize(im,(x+w-max(pw,65),y+int(h*.40),max(pw,65),max(20,int(h*.60)-ph)),work,f'{page}-{ix}-side')
            labels=[q for q in words if re.search(r'[A-Za-zÀ-ÿ]{2}',q['t'])]
        name=' '.join(q['t'] for q in labels).strip()
        if len(re.sub(r'[^A-Za-zÀ-ÿ]','',name))<7:continue
        name=re.sub(r"\bL['’]?ETTO\b",'',name,flags=re.I).strip()
        if len(name)<5:continue
        bbox=rectangle(labels,im.width,im.height)
        price_box=rectangle(pwds,im.width,im.height) if pwds else None
        identity=f'{page}|{x}|{y}|{name}|{price}'
        products.append(dict(id=hashlib.sha256(identity.encode()).hexdigest()[:18],market='Effe Gros',name=name,
          price=price,brand='',format="l'etto" if any('ETTO' in q['t'] for q in labels) else '',page=page,
          bbox=bbox,textBoxes=[bbox],priceBox=price_box,bboxSpace='normalized',hotspotType='text',
          mappingVerified=True,mappingConfidence=1,sourceWidth=im.width,sourceHeight=im.height,
          ocrConfidence=round(sum(q['confidence'] for q in labels)/len(labels),1),
          category='Altro',rating='NORMALE',ranking=999,pageIndex=len(products)+1,
          note='Testo letto dal volantino. Tocca il testo o il prezzo stampato per selezionarlo.'))
    return products

def read_reviewed(im,page,url,work):
    regions=reviewed(page,url)
    if regions is None:return read_page(im,page,work)
    products=[]
    def box(rect):
        x,y,w,h=rect
        return dict(x=round(x/im.width,6),y=round(y/im.height,6),w=round(w/im.width,6),h=round(h/im.height,6))
    for ix,r in enumerate(regions):
        words=recognize(im,r['caption'],work,f'{page}-{ix}-caption')
        name=r.get('name') or ' '.join(q['t'] for q in words).strip()
        name=re.sub(r'\s+',' ',name)
        if not name:name=f'Articolo pagina {page}, riquadro {ix+1}'
        price=r.get('price');pr=r.get('priceBox')
        # This edition's compressed price font confuses 9 with 8/6. Only
        # visually confirmed prices are exported; captions remain selectable.
        caption=rectangle(words,im.width,im.height) if words else box(r['caption'])
        # Manual descriptions retain the full printed region, including letters
        # the OCR did not read. Neither price confidence nor OCR confidence can
        # discard an independently verified product caption.
        if r.get('name'):caption=box(r['caption'])
        p=dict(id=hashlib.sha256(f'{url}|caption|{ix}'.encode()).hexdigest()[:18],market='Effe Gros',name=name,
            price=price,priceRead=price is not None,brand='',format=r.get('format',''),page=page,pageIndex=ix+1,
            category='Altro',rating='NORMALE',ranking=999,bbox=caption,textBoxes=[caption],
            captionCrop=box(r['caption']),priceBox=box(pr) if pr else None,
            bboxSpace='normalized',hotspotType='text',mappingVerified=True,mappingConfidence=1,
            sourceWidth=im.width,sourceHeight=im.height,regionReview='visual',
            note='Selezione della descrizione stampata. Il prezzo non determina la presenza del prodotto.')
        for k in ['validFrom','validTo']:
            if r.get(k):p[k]=r[k]
        products.append(p)
    return products

def enrich(data,cache=None):
    if data['market']!='Effe Gros':return data
    cache=Path(cache or os.environ.get('OCR_CACHE','work/ocr-cache'));cache.mkdir(parents=True,exist_ok=True)
    def one(pair):
        i,url=pair;key=hashlib.sha256((VERSION+'|'+url).encode()).hexdigest();saved=cache/(key+'.json')
        if saved.exists():return json.loads(saved.read_text(encoding='utf-8'))
        image=cache/(key+'.jpg')
        if not image.exists():
            local=Path(os.environ.get('OCR_PAGE_DIR',''))/f'page-{i+1:02}.jpg'
            if os.environ.get('OCR_PAGE_DIR') and local.exists():image.write_bytes(local.read_bytes())
            else:image.write_bytes(get(url,True))
        with Image.open(image) as im,tempfile.TemporaryDirectory() as tmp:
            rows=read_reviewed(im.convert('RGB'),i+1,url,Path(tmp))
        saved.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
        print(f'OCR pagina {i+1}: {len(rows)} prodotti',flush=True)
        return rows
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pages=list(pool.map(one,enumerate(data['pages'])))
    products=[p for rows in pages for p in rows]
    if not products:raise ValueError('OCR non ha estratto prodotti: catalogo precedente conservato')
    for p in products:p['validity']=data['period']
    data.update(products=products,offerCount=len(products),ocrVersion=VERSION,ocrPages=len([p for p in pages if p]),staleProducts=False)
    return data

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('--cache');args=ap.parse_args()
    d=enrich(json.loads(args.manifest.read_text(encoding='utf-8')),args.cache)
    args.manifest.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('Totale:',len(d['products']))

