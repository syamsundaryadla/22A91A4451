import json,re
S=[(0.10,2.13,"IPL 2026 lo death overs lo dominate chesina"),(2.39,5.95,"Top 5 bowling teams evaro telusa?"),
(6.37,8.95,"Economy, wickets tho ee teams performance chuddam!"),
(9.41,10.12,"Number 5..."),(10.46,11.56,"Rajasthan Royals!"),(11.84,13.39,"9.95 economy..."),(13.67,14.79,"26 wickets!"),
(15.20,15.75,"Number 4..."),(16.09,17.02,"Delhi Capitals!"),(17.34,18.79,"9.91 economy..."),(19.04,20.01,"24 wickets!"),
(20.40,21.00,"Number 3..."),(21.29,22.76,"Royal Challengers Bengaluru!"),(23.04,24.71,"9.70 economy..."),(24.93,25.89,"34 wickets!"),
(26.31,26.88,"Number 2..."),(27.24,28.39,"Kolkata Knight Riders!"),(28.69,30.22,"9.53 economy..."),(30.45,31.39,"34 wickets!"),
(31.73,33.43,"And finally... Number 1!"),(33.76,35.18,"Sunrisers Hyderabad!"),(35.53,37.37,"Just 9.49 economy..."),(37.63,38.63,"32 wickets!"),
(38.90,39.48,"Yes!"),(39.76,45.21,"IPL 2026 lo death overs lo, most economical bowling team Sunrisers Hyderabad!"),
(45.69,47.53,"Mari mee favourite death-over bowling team edi?"),(47.88,48.51,"SRH aa?"),(48.81,49.42,"KKR aa?"),(49.70,50.30,"RCB aa?"),
(50.66,51.26,"Comment cheyyandi!"),(51.60,55.08,"Follow for more exciting IPL statistics and cricket analysis!")]
spoken={"9.95":"ninepointninefive","9.91":"ninepointnineone","9.70":"ninepointseventy","9.53":"ninepointfivethree","9.49":"ninepointfournine","26":"twentysix","24":"twentyfour","34":"thirtyfour","32":"thirtytwo","2026":"twentytwentysix","5":"five","4":"four","3":"three","2":"two","1":"one"}
def wt(w):
    c=re.sub(r"[^\w.]","",w); c=spoken.get(c.rstrip("."),c)
    return max(1,len(re.findall(r"[aeiouy]+",c.lower())))+(0.4 if re.search(r"[.,!?]$",w) else 0)
out=[]
for a,b,l in S:
    ws=l.split(); x=[wt(w) for w in ws]; T=sum(x); t=a; words=[]
    for w,v in zip(ws,x):
        d=(b-a)*v/T; words.append(dict(w=w,s=round(t,3),e=round(t+d,3))); t+=d
    out.append(dict(text=l,s=a,e=b,words=words))
json.dump(out,open("timing.json","w"),indent=1); print(len(out))
