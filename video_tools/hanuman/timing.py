import json,re
lines=["Do you know why Shani Dev never troubles Hanuman's devotees?","He made a promise,","in pain.","Shani Dev was very powerful.","Even kings and gods feared him.","One day, he became proud and went to find Hanuman.","Hanuman was sitting and chanting Rama's name.","Shani said,","\"I have come to put my influence on you.\"","Hanuman said,","\"Not now.","I am serving Rama.\"","Shani laughed and climbed on his shoulder.","Hanuman smiled and said,","\"Then stay.\"","He started lifting mountains and placing them on his head.","The weight crushed Shani.","He cried,","\"Stop!","I can't bear this!\"","Shani begged for mercy and promised,","\"I will never trouble anyone who worships you.\"","That is why people offer mustard oil to Hanuman on Saturdays.","Follow for more untold stories of Hanuman."]
s=[float(x.split()[1]) for x in open("sil.txt")]
starts=[0.0]+s[1::2]; ends=s[0::2]+[56.19]
# trim tail of last segment: find actual end
segs=list(zip(starts,ends)); assert len(segs)==len(lines),(len(segs),len(lines))
def vow(w): return max(1,len(re.findall(r"[aeiouy]+",w.lower())))
out=[]
for (a,b),l in zip(segs,lines):
    ws=l.split(); wt=[vow(w)+0.35*len(re.sub(r'\W','',w))/3+(0.25 if re.search(r"[,.!?]$",w) else 0) for w in ws]
    T=sum(wt); t=a+0.03; words=[]
    for w,x in zip(ws,wt):
        d=(b-a-0.05)*x/T; words.append(dict(w=w,s=round(t,3),e=round(t+d,3))); t+=d
    out.append(dict(text=l,s=round(a,3),e=round(b,3),words=words))
json.dump(out,open("timing.json","w"),indent=1)
for o in out: print(f'{o["s"]:6.2f}-{o["e"]:6.2f} {o["text"]}')
