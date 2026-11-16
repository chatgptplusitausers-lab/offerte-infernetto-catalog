"""Locate source product crops on their exact edition page using feature geometry."""
import concurrent.futures,hashlib,json,os
from pathlib import Path
import cv2
import numpy as np
from flyer_sources import get
VERSION='sift-crops-v1'
cv2.setNumThreads(1)

def locate(page,crop):
    detector=cv2.SIFT_create(nfeatures=3500)
    ka,da=detector.detectAndCompute(crop,None);kb,db=detector.detectAndCompute(page,None)
    if da is None or db is None:return None
    pairs=cv2.BFMatcher().knnMatch(da,db,k=2)
    good=[a for pair in pairs if len(pair)==2 for a,b in [pair] if a.distance<.68*b.distance]
    if len(good)<8:return None
    src=np.float32([ka[m.queryIdx].pt for m in good]);dst=np.float32([kb[m.trainIdx].pt for m in good])
    h,mask=cv2.findHomography(src,dst,cv2.RANSAC,3)
    if h is None or int(mask.sum())<8 or mask.mean()<.7:return None
    ch,cw=crop.shape[:2];ph,pw=page.shape[:2]
    corners=cv2.perspectiveTransform(np.float32([[[0,0],[cw,0],[cw,ch],[0,ch]]]),h)[0]
    x,y=corners.min(axis=0);r,b=corners.max(axis=0)
    if x< -3 or y< -3 or r>pw+3 or b>ph+3 or r-x<15 or b-y<15:return None
    if not cv2.isContourConvex(corners.astype(np.float32)):return None
    # Genuine crops undergo almost uniform scaling, not arbitrary projective warps.
    sx=(r-x)/cw;sy=(b-y)/ch
    if not .85<sx/sy<1.18:return None
    return dict(x=round(max(0,float(x))/pw,6),y=round(max(0,float(y))/ph,6),w=round((min(pw,float(r))-max(0,float(x)))/pw,6),h=round((min(ph,float(b))-max(0,float(y)))/ph,6))

def enrich_mapping(data,cache=None):
    cache=Path(cache or os.environ.get('OCR_CACHE','work/ocr-cache'));cache.mkdir(parents=True,exist_ok=True)
    def image(url):
        path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.img')
        if not path.exists():path.write_bytes(get(url,True,timeout=8,attempts=1))
        im=cv2.imdecode(np.frombuffer(path.read_bytes(),dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
        if im is None:raise ValueError('Immagine non decodificabile')
        return im
    def page_work(pair):
        i,url=pair;rows=[p for p in data['products'] if p['page']==i+1]
        if not rows:return
        page=image(url)
        for p in rows:
            if not p.get('image'):continue
            key=hashlib.sha256((VERSION+'|'+url+'|'+p['image']).encode()).hexdigest();path=cache/(key+'.map.json')
            try:
                if path.exists():box=json.loads(path.read_text())
                else:
                    crop=image(p['image'])
                    box=locate(page,crop) or locate_template(page,crop)
                    if box:path.write_text(json.dumps(box))
                if box:p.update(bbox=box,bboxSpace='normalized',sourceWidth=page.shape[1],sourceHeight=page.shape[0],mappingVerified=True,mappingMethod=VERSION)
            except (OSError,ValueError,cv2.error):continue
        print(f"Mappa {data['market']} pagina {i+1}: {sum(bool(p.get('bbox')) for p in rows)}/{len(rows)}",flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(page_work,enumerate(data['pages'])))
    data['mappingVersion']=VERSION;data['mappedProductCount']=sum(bool(p.get('bbox')) for p in data['products'])
    return data

def locate_template(page,crop):
    # Secondary check for low-texture crops where feature homography is unstable.
    ph,pw=page.shape;ch,cw=crop.shape;scale=min(1,1000/ph)
    pg=cv2.resize(page,None,fx=scale,fy=scale);best=None
    for factor in np.arange(.7,1.31,.01):
        w,h=round(cw*factor*scale),round(ch*factor*scale)
        if min(w,h)<20 or w>pg.shape[1] or h>pg.shape[0]:continue
        cc=cv2.resize(crop,(w,h));scores=cv2.matchTemplate(pg,cc,cv2.TM_CCOEFF_NORMED)
        _,score,_,(x,y)=cv2.minMaxLoc(scores)
        if score<.93 or best and score<=best[0]:continue
        scores[max(0,y-h//2):min(scores.shape[0],y+h//2+1),max(0,x-w//2):min(scores.shape[1],x+w//2+1)]=-1
        second=cv2.minMaxLoc(scores)[1]
        if score-second<.08:continue
        best=(score,dict(x=x/scale/pw,y=y/scale/ph,w=w/scale/pw,h=h/scale/ph))
    return best[1] if best else None
