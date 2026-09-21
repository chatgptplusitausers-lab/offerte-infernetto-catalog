"""Discover live editions independently; never label future/expired offers as current."""
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import math
import re
import time
import urllib.request
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

STORE = 'https://www.cedigros.com/insegne/effepiu/via-dobbiaco-1-angolo-viale-castel-porziano'
MONTHS = 'gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre'.split()
MONTH = '(?:' + '|'.join(MONTHS) + ')'
PERIOD = re.compile(r"\b(?:dal|dall['’])\s*(\d{1,2})(?:\s+("+MONTH+r"))?(?:\s+(\d{4}))?\s+(?:al|all['’])\s*(\d{1,2})\s+("+MONTH+r")\s+(\d{4})", re.I)

def today():
    return dt.datetime.now(ZoneInfo('Europe/Rome')).date()

def get(url, binary=False):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; OfferteInfernetto/3.6)'})
            with urllib.request.urlopen(req,timeout=25) as r:
                data=r.read()
            return data if binary else data.decode('utf-8','replace')
        except (OSError, TimeoutError) as exc:
            last=exc
            if attempt<2: time.sleep(attempt+1)
    raise last

def parse_period(text):
    text=re.sub(r'\s+',' ',html.unescape(text))
    m=PERIOD.search(text)
    if not m: raise ValueError('Intervallo di validità non riconosciuto')
    d1,m1,y1,d2,m2,y2=m.groups()
    end=dt.date(int(y2),MONTHS.index(m2.lower())+1,int(d2))
    month1=MONTHS.index((m1 or m2).lower())+1
    start=dt.date(int(y1 or (end.year-(month1>end.month))),month1,int(d1))
    if start>end or (end-start).days>100: raise ValueError('Intervallo di validità incoerente')
    return start,end

def edition(market,url,pages,start,end,products,source):
    # Includes page filenames: Cedigros reuses the same numeric flyer ID.
    identity='|'.join([market,start.isoformat(),end.isoformat()]+[u.split('?')[0] for u in pages])
    return dict(market=market,id=hashlib.sha256(identity.encode()).hexdigest()[:20],
        period=f'{start.day} {MONTHS[start.month-1]} {start.year} – {end.day} {MONTHS[end.month-1]} {end.year}',
        validFrom=start.isoformat(),validTo=end.isoformat(),url=url,catalog=url,pages=pages,products=products,
        source=source,offerCount=len(products),start=int(dt.datetime.combine(start,dt.time(),dt.timezone.utc).timestamp()*1000),
        end=int(dt.datetime.combine(end,dt.time(23,59,59),dt.timezone.utc).timestamp()*1000))

def parse_effe(detail,url,fid):
    soup=BeautifulSoup(detail,'html.parser')
    start,end=parse_period(soup.get_text(' ',strip=True))
    decoded=html.unescape(detail).replace('\\/','/')
    pattern=r'(?:https?://(?:www\.)?cedigros\.com)?/media/com_myegojwt/contents/flyers/'+re.escape(str(fid))+r'/[^\s"\'<>]*?page[_-]?(\d+)\.(?:jpe?g|png|webp)'
    pages={}
    for m in re.finditer(pattern,decoded,re.I):
        u=urljoin(url,m.group(0)).replace('https://cedigros.com/','https://www.cedigros.com/')
        pages.setdefault(int(m.group(1)),u)
    expected=re.search(r'(\d{1,3})\s+pagine',soup.get_text(' ',strip=True),re.I)
    if not pages or sorted(pages)!=list(range(1,len(pages)+1)) or (expected and len(pages)!=int(expected[1])):
        raise ValueError('Pagine Effe Gros incomplete')
    return edition('Effe Gros',url,[pages[n] for n in sorted(pages)],start,end,[], 'CE.DI. GROS — punto vendita Infernetto')

def discover_effe():
    store=get(STORE)
    ids=list(dict.fromkeys(re.findall(r'view=flyer(?:&amp;|&)id=(\d+)',store)))
    if not ids: raise ValueError('Nessun volantino nel punto vendita Infernetto')
    found=[]
    for fid in ids[:5]:
        url=f'https://www.cedigros.com/insegne/effepiu?view=flyer&id={fid}'
        found.append(parse_effe(get(url),url,fid))
    return choose_current(found)

def parse_nuovo(market,url,raw):
    soup=BeautifulSoup(raw,'html.parser')
    start,end=parse_period(soup.get_text(' ',strip=True))
    pages=list(dict.fromkeys(urljoin(url,i.get('data-src') or i.get('data-lazy-src') or i.get('src') or '') for i in soup.select('img') if 'nuovo volantino pagina' in i.get('alt','').lower()))
    if not pages or not all(urlsplit(u).hostname=='publications.nuovovolantino.it' for u in pages):
        raise ValueError('Immagini volantino non riconosciute')
    products=[]; seen=set()
    for card in soup.select('article.nv-single-offer'):
        button=card.select_one('[data-add-offer]')
        if not button: continue
        try:
            raw=json.loads(button['data-add-offer'])
            name=str(raw.get('product_name') or '').strip()
            price=float(raw.get('price_value'))
            pm=re.search(r'pag\.\s*(\d+)',card.get_text(' ',strip=True),re.I)
            page=int(pm[1]) if pm else 0
            pid=str(raw['offer_id'])
            if not name or not math.isfinite(price) or price<=0 or not 1<=page<=len(pages) or pid in seen: continue
            image=raw.get('crop_url') or ''
            if image and urlsplit(image).hostname!='media.nuovovolantino.it': image=''
            seen.add(pid)
            products.append(dict(id=pid,market=market,name=name,brand=raw.get('brand_name') or '',format=raw.get('quantity_text') or '',
                price=price,page=page,image=image,category='Altro',rating='NORMALE',ranking=999,
                validity=f'{start.isoformat()} – {end.isoformat()}',pageIndex=len(products)+1,
                note='Prezzo riportato da NuovoVolantino; verifica sul volantino e nel punto vendita.'))
        except (ValueError,TypeError,KeyError): continue
    return edition(market,url,pages,start,end,products,'NuovoVolantino — verificare adesione del punto vendita')

def choose_current(editions,day=None):
    day=(day or today()).isoformat()
    current=[d for d in editions if d['validFrom']<=day<=d['validTo']]
    if not current:
        upcoming=[d for d in editions if day<d['validFrom']<=(dt.date.fromisoformat(day)+dt.timedelta(days=10)).isoformat()]
        if not upcoming: raise ValueError('Nessuna edizione valida o in anteprima')
        result=min(upcoming,key=lambda d:(d['validFrom'],-len(d['products'])))
        result['upcoming']=True
        return result
    # Prefer the main grocery flyer over small concurrent themed supplements.
    return max(current,key=lambda d:(len(d['products']),d['validFrom'],len(d['pages'])))

def discover_nuovo(market,slug):
    landing='https://www.nuovovolantino.it/'+slug
    soup=BeautifulSoup(get(landing),'html.parser')
    urls=list(dict.fromkeys(urljoin(landing,a['href']) for a in soup.select('a[href]') if re.search('/'+slug+r'/\d+(?:[/?#]|$)',a['href'])))[:8]
    def read(url):
        try:return parse_nuovo(market,url,get(url))
        except (ValueError,OSError):return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        found=[x for x in ex.map(read,urls) if x]
    return choose_current(found)
