import json,sys,urllib.request,urllib.parse,time,urllib.error
UA="ReelBuilder/1.0 (personal video editing script)"
def get(params):
    params.update(format="json")
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params)
    for a in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=30))
        except urllib.error.HTTPError as e:
            if e.code!=429: raise
            w=int(e.headers.get("Retry-After") or 30); print("429, waiting",w,file=sys.stderr,flush=True); time.sleep(min(max(w,20),120))
out={}
for q in sys.argv[1:]:
    d=get(dict(action="query",generator="search",gsrnamespace=6,gsrsearch=q,gsrlimit=25,prop="imageinfo",iiprop="url|size|extmetadata",iiurlwidth=1600))
    res=[]
    for p in (d or {}).get("query",{}).get("pages",{}).values():
        ii=p["imageinfo"][0]; m=ii.get("extmetadata",{})
        if ii["width"]<700: continue
        res.append(dict(t=p["title"],w=ii["width"],h=ii["height"],lic=m.get("LicenseShortName",{}).get("value","?"),art=m.get("Artist",{}).get("value","")[:150],thumb=ii.get("thumburl"),url=ii["url"]))
    out[q]=res; print("done",q,len(res),flush=True)
    json.dump(out,open("search.json","w"),indent=1); time.sleep(10)
