#!/usr/bin/env python3
"""Build a fail-closed product/area manifest from the current Effepiù flyer."""
import argparse, csv, hashlib, html, json, math, re, statistics, subprocess, tempfile, urllib.request
from pathlib import Path

STORE="https://www.cedigros.com/insegne/effepiu/via-dobbiaco-1-angolo-viale-castel-porziano"
UA={"User-Agent":"OfferteInfernettoCatalogBot/1.0"}

def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=35) as r:
        data=r.read()
    return data if binary else data.decode("utf-8","replace")

def discover():
    page=get(STORE); ids=re.findall(r"view=flyer(?:&amp;|&)id=(\d+)",page)
    if not ids: raise RuntimeError("current flyer id not found on Infernetto store page")
    fid=ids[0]; url=f"https://www.cedigros.com/insegne/effepiu?view=flyer&id={fid}"; detail=get(url)
    text=re.sub(r"<[^>]+>"," ",html.unescape(detail)); text=re.sub(r"\s+"," ",text)
    match=re.search(r"Dal\s+(\d{1,2}\s+[^<]{1,80}?\s+\d{4})",text,re.I)
    period=match.group(1).strip() if match else ""
    found=re.findall(r"https://(?:www\.)?cedigros\.com/media/com_myegojwt/contents/flyers/"+re.escape(fid)+r"/[^\"']+?page_\d+\.jpg",html.unescape(detail))
    by_number={}
    for candidate in found:
        number=int(re.search(r"page_(\d+)",candidate).group(1))
        by_number.setdefault(number,candidate.replace("https://cedigros.com/","https://www.cedigros.com/"))
    pages=[by_number[n] for n in sorted(by_number)]
    if not period or len(pages)<2: raise RuntimeError("flyer metadata incomplete")
    return fid,period,url,pages

def ocr_pass(image,psm):
    proc=subprocess.run(["tesseract",str(image),"stdout","-l","ita+eng","--psm",str(psm),"tsv"],capture_output=True,text=True,check=True)
    rows=[]
    for r in csv.DictReader(proc.stdout.splitlines(),delimiter="\t"):
        try:
            conf=float(r["conf"]); txt=r["text"].strip(); left=int(r["left"]); top=int(r["top"]); width=int(r["width"]); height=int(r["height"])
            line=(int(r["block_num"]),int(r["par_num"]),int(r["line_num"]))
        except (ValueError,KeyError): continue
        if conf>=35 and txt: rows.append({"t":txt,"c":conf,"x":left,"y":top,"w":width,"h":height,"line":line})
    return rows

def ocr(image):
    sparse=ocr_pass(image,11)
    direct=sum(bool(re.fullmatch(r"\d{1,3}[,.]\d{2}",w["t"].replace("€",""))) for w in sparse)
    return sparse if direct>=3 else sparse+ocr_pass(image,6)

def price_tokens(words,median_height):
    prices=[];seen=set()
    for w in words:
        raw=w["t"].replace("€","").strip()
        if re.fullmatch(r"\d{1,3}[,.]\d{2}",raw):
            q=dict(w);q["value"]=float(raw.replace(",","."));prices.append(q);seen.add((w["x"],w["y"],w["w"],w["h"]))
    lines={}
    for w in words:lines.setdefault(w["line"],[]).append(w)
    for line in lines.values():
        line.sort(key=lambda w:w["x"])
        for i,w in enumerate(line):
            if not re.fullmatch(r"\d{1,3}",w["t"].strip()) or w["h"]<median_height*1.15:continue
            tail=line[i+1:i+4]; digits=None; used=[]
            for z in tail:
                gap=z["x"]-(used[-1]["x"]+used[-1]["w"] if used else w["x"]+w["w"])
                if gap>max(24,w["h"]*1.4):break
                used.append(z); token="".join(x["t"] for x in used).replace(" ","")
                m=re.fullmatch(r"[,.:]?(\d{2})",token)
                if m:digits=m.group(1);break
            if digits:
                x1=max(z["x"]+z["w"] for z in used);key=(w["x"],w["y"],x1-w["x"],max([w["h"]]+[z["h"] for z in used]))
                if key not in seen:prices.append({"t":w["t"]+","+digits,"value":float(w["t"]+"."+digits),"c":min([w["c"]]+[z["c"] for z in used]),"x":w["x"],"y":min([w["y"]]+[z["y"] for z in used]),"w":x1-w["x"],"h":key[3],"line":w["line"]});seen.add(key)
    return prices

def candidates(words,width,height,page):
    med=statistics.median([w["h"] for w in words]);prices=price_tokens(words,med)
    if not prices:return []
    prices=[p for p in prices if p["h"]>=med*1.15]
    out=[]
    for i,p in enumerate(prices):
        cx=p["x"]+p["w"]/2; cy=p["y"]+p["h"]/2
        near=[w for w in words if abs((w["y"]+w["h"]/2)-cy)<height*.13 and abs((w["x"]+w["w"]/2)-cx)<width*.18 and w is not p]
        labels=[w for w in near if not re.fullmatch(r"[€%\d,./-]+",w["t"]) and len(w["t"])>1]
        labels.sort(key=lambda w:(w["y"],w["x"])); name=" ".join(w["t"] for w in labels[:8]).strip()
        if len(name)<4:continue
        # The clickable area is the printed sale price, not an inferred product tile.
        pad_x=max(8,p["w"]*.22);pad_y=max(8,p["h"]*.20)
        x0=max(0,p["x"]-pad_x);y0=max(0,p["y"]-pad_y);x1=min(width,p["x"]+p["w"]+pad_x);y1=min(height,p["y"]+p["h"]+pad_y)
        conf=min(.99,.58+p["c"]/250+(min(6,len(labels))/100)); price=float(p["t"].replace("€","").replace(",","."))
        key=f"{page}|{name}|{price}|{round(x0)}|{round(y0)}"; pid=hashlib.sha1(key.encode()).hexdigest()[:14]
        out.append({"id":pid,"name":name,"brand":"","format":"","category":"Altro","page":page,"price":price,"priceText":p["t"],"hotspotType":"price","confidence":round(conf,3),"bbox":{"x":round(x0/width,5),"y":round(y0/height,5),"w":round((x1-x0)/width,5),"h":round((y1-y0)/height,5)}})
    return out

def image_size(path):
    from PIL import Image
    with Image.open(path) as im:return im.size

def build(output):
    fid,period,url,pages=discover(); products=[]
    with tempfile.TemporaryDirectory() as tmp:
        for page_no,page_url in enumerate(pages,1):
            path=Path(tmp)/f"page-{page_no}.jpg";path.write_bytes(get(page_url,True));w,h=image_size(path)
            products.extend(candidates(ocr(path),w,h,page_no))
    accepted=[p for p in products if p["confidence"]>=.86]
    manifest={"schemaVersion":1,"market":"Effe Gros","sourceId":f"cedigros_effepiu_infernetto_{fid}","period":period,"catalog":url,"pages":pages,"detectedProducts":len(products),"products":accepted}
    covered=len(set(p["page"] for p in accepted));coverage=len(accepted)/max(1,len(products))
    required_pages=max(3,math.ceil(len(pages)*.75))
    if covered<required_pages or coverage<.70: raise RuntimeError(f"manifest quarantined: pages={covered}/{len(pages)} (required {required_pages}), confidenceCoverage={coverage:.2%}")
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(manifest,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"accepted {len(accepted)}/{len(products)} products on {covered}/{len(pages)} pages")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);args=ap.parse_args();build(args.output)
