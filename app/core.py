import json, re, html, os, smtplib, ssl
from datetime import datetime, timezone, date
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlparse
import requests, feedparser
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
KEYWORDS=['scholarship','bursary','award','grant','fellowship','funding']

def load(path, default):
    f=ROOT/path
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else default

def save(path,obj):
    f=ROOT/path; f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def clean(text): return re.sub(r'\s+',' ',BeautifulSoup(text or '', 'html.parser').get_text(' ',strip=True)).strip()

def uid(url):
    import hashlib
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def valid_url(url):
    u=urlparse(url)
    return u.scheme=='https' and bool(u.hostname) and not (u.hostname in ('localhost','127.0.0.1') or u.hostname.endswith('.local'))

def discover():
    found=[]
    for source in load('config/sources.json',[]):
        if not source.get('enabled') or not source.get('url'): continue
        url=source['url']
        if not valid_url(url): continue
        if source.get('type')=='links':
            # A discovery bookmark, not an individual award. Never pretend this is a verified scholarship.
            found.append({'id':uid(url),'title':source['name']+' — browse awards','url':url,
                          'source':source['name'],'summary':source.get('notes',''),
                          'kind':'directory','deadline':None,'amount_cad':None,'eligibility_text':'',
                          'verified':False,'discovered_at':date.today().isoformat()})
        elif source.get('type')=='rss':
            try:
                response=requests.get(url,timeout=15,headers={'User-Agent':'ScholarshipAutoPilot/1.0 (personal research)'})
                response.raise_for_status()
                feed=feedparser.parse(response.content)
                for entry in feed.entries[:50]:
                    link=entry.get('link','')
                    title=clean(entry.get('title',''))
                    summary=clean(entry.get('summary',''))[:1000]
                    if not valid_url(link) or not any(k in (title+' '+summary).lower() for k in KEYWORDS): continue
                    found.append({'id':uid(link),'title':title,'url':link,'source':source['name'],
                                  'summary':summary,'kind':'candidate','deadline':None,'amount_cad':None,
                                  'eligibility_text':'','verified':False,'discovered_at':date.today().isoformat()})
            except (requests.RequestException,ValueError) as e:
                print('Could not fetch',source['name'],type(e).__name__)
    return found

def score(item,profile):
    if item.get('kind')=='directory': return {'score':0,'status':'directory','reasons':['Browse this official or external directory for individual awards']}
    text=' '.join(str(item.get(k,'') or '') for k in ('title','summary','eligibility_text')).lower()
    reasons=[]; points=0
    for term in profile.get('program_keywords',[])+profile.get('interests',[]):
        if term.lower() in text:
            points+=12; reasons.append('Mentions '+term)
    if 'canada' in text or 'canadian' in text: points+=8; reasons.append('Mentions Canada')
    if 'ontario' in text: points+=5; reasons.append('Mentions Ontario')
    if 'university of waterloo' in text or 'waterloo' in text: points+=10; reasons.append('Mentions Waterloo')
    deadline=item.get('deadline')
    if deadline:
        try:
            if date.fromisoformat(deadline)<date.today(): return {'score':0,'status':'expired','reasons':['Deadline has passed']}
        except ValueError: reasons.append('Deadline requires verification')
    if item.get('verified') is not True: reasons.append('Eligibility, deadline and amount require manual verification')
    return {'score':min(points,100),'status':'possible match — verify' if points else 'unreviewed','reasons':reasons or ['No eligibility evidence found']}

def merge(existing,new):
    by_id={x['id']:x for x in existing}
    added=[]
    for item in new:
        if item['id'] not in by_id: by_id[item['id']]=item; added.append(item)
        else:
            old=by_id[item['id']]
            for k in ('title','summary','source'):
                if item.get(k): old[k]=item[k]
    return list(by_id.values()),added

def draft(item,profile):
    title=item.get('title','the award')
    return f'''# Application preparation: {title}

Award page: {item.get('url','')}
Status: DRAFT — NOT SUBMITTED

## Eligibility checklist (verify against official rules)
- [ ] Applicant status and program
- [ ] Residency/citizenship requirements
- [ ] GPA/academic requirements (if any)
- [ ] Financial-need requirements (if any)
- [ ] Deadline and submission method
- [ ] Funding restrictions and allowed expenses

## Draft statement (EDIT BEFORE USING)
I am an engineering student at {profile.get('institution','my university')}, with interests in community service, leadership, and applying technical skills to meaningful challenges. Through my academic and volunteer experiences, I have developed teamwork, communication, and problem-solving skills. [ADD A SPECIFIC, TRUE EXAMPLE.] This opportunity would support [EXPLAIN YOUR ACTUAL GOAL AND HOW THIS AWARD PERMITS THE FUNDS TO BE USED].

## Required documents
- [ ] Official application questions (paste them here)
- [ ] Resume/CV if required
- [ ] Transcript if required (store privately, NOT in this repository)
- [ ] References if required

## Approval gate
- [ ] I reviewed every statement for accuracy.
- [ ] I confirmed eligibility and funding restrictions.
- [ ] I reviewed the official application and submitted it myself.

No automated submission occurs.
'''

def email_digest(items, added):
    host=os.getenv('SMTP_HOST'); user=os.getenv('SMTP_USER'); password=os.getenv('SMTP_PASSWORD'); recipient=os.getenv('EMAIL_TO')
    if not all((host,user,password,recipient)):
        print('Email skipped: SMTP secrets not configured.'); return
    msg=EmailMessage(); msg['From']=os.getenv('EMAIL_FROM',user); msg['To']=recipient
    msg['Subject']='Scholarship AutoPilot — weekly opportunities'
    lines=[f'New listings this run: {len(added)}','', 'All newly discovered items are unverified until you review official requirements.','']
    for x in added[:25]: lines += [f"{x['title']}",x['url'],f"Match: {x.get('match',{}).get('status','unreviewed')}",'']
    if not added: lines.append('No new listings found. Check your dashboard for existing opportunities.')
    msg.set_content('\n'.join(lines))
    with smtplib.SMTP(host,int(os.getenv('SMTP_PORT','587')),timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context()); smtp.login(user,password); smtp.send_message(msg)

def run():
    profile=load('config/profile.json',load('config/profile.example.json',{}))
    previous=load('data/opportunities.json',[])
    items,added=merge(previous,discover())
    for item in items: item['match']=score(item,profile)
    items.sort(key=lambda x:(x.get('kind')=='directory',-x['match']['score'],x['title']))
    save('data/opportunities.json',items)
    out=ROOT/'drafts'; out.mkdir(exist_ok=True)
    for item in items:
        if item.get('kind')!='directory':
            target=out/(item['id']+'.md')
            if not target.exists(): target.write_text(draft(item,profile),encoding='utf-8')
    print(f'{len(items)} total listings, {len(added)} new. No applications submitted.')
    email_digest(items,added)

if __name__=='__main__': run()
