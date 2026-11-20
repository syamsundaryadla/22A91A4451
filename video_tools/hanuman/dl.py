import json,sys,urllib.request,urllib.parse,time,urllib.error,os,re
UA="ReelBuilder/1.0 (personal video editing script)"
def fetch(url,binary=False):
    for a in range(12):
        try: return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code!=429: raise
            w=int(e.headers.get("Retry-After") or 20); print("429 wait",w,flush=True); time.sleep(min(max(w,20),660))
os.makedirs("img",exist_ok=True)
meta=json.load(open("img/meta.json")) if os.path.exists("img/meta.json") else {}
for line in open(sys.argv[1]):
    if "|" not in line: continue
    key,title=[x.strip() for x in line.split("|",1)]
    if os.path.exists(f"img/{key}.jpg"): continue
    d=json.loads(fetch("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(dict(action="query",titles=title,prop="imageinfo",iiprop="url|size|extmetadata",iiurlwidth=1920,format="json"))))
    p=list(d["query"]["pages"].values())[0]
    if "imageinfo" not in p: print("missing",key,flush=True); continue
    ii=p["imageinfo"][0]; m=ii["extmetadata"]
    u=ii.get("thumburl") or ii["url"]
    u=u.replace("https://thumb.wikimedia.org/","https://upload.wikimedia.org/").split("?")[0]
    if ii["width"]<=2600 and not title.lower().endswith(".tif"): u=ii["url"].split("?")[0]
    time.sleep(8); data=fetch(u)
    open(f"img/{key}.jpg","wb").write(data)
    meta[key]=dict(title=title,url=ii["descriptionurl"],license=m.get("LicenseShortName",{}).get("value"),artist=re.sub("<[^>]+>","",m.get("Artist",{}).get("value",""))[:200])
    json.dump(meta,open("img/meta.json","w"),indent=1); print("ok",key,len(data),flush=True); time.sleep(12)
