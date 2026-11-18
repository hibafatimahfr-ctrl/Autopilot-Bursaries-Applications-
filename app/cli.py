import argparse
from .core import ROOT,load,save,draft

def main():
    parser=argparse.ArgumentParser(description='Manage manually verified scholarships')
    sub=parser.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('add',help='Add a verified or unverified award from an official URL')
    for key in ('title','url','source'): a.add_argument('--'+key,required=True)
    a.add_argument('--deadline',default=None,help='YYYY-MM-DD')
    a.add_argument('--amount',type=float,default=None)
    a.add_argument('--eligibility',default='')
    a.add_argument('--verified',action='store_true',help='Use only after personally checking official terms')
    d=sub.add_parser('draft'); d.add_argument('id')
    args=parser.parse_args()
    from .core import uid,score
    profile=load('config/profile.json',load('config/profile.example.json',{}))
    items=load('data/opportunities.json',[])
    if args.cmd=='add':
        item={'id':uid(args.url),'title':args.title,'url':args.url,'source':args.source,'summary':'',
              'kind':'candidate','deadline':args.deadline,'amount_cad':args.amount,
              'eligibility_text':args.eligibility,'verified':args.verified}
        item['match']=score(item,profile)
        items=[i for i in items if i['id']!=item['id']]+[item]
        save('data/opportunities.json',items)
        print('Added',item['id'])
    elif args.cmd=='draft':
        item=next((x for x in items if x['id']==args.id),None)
        if not item: raise SystemExit('Unknown ID')
        target=ROOT/'drafts'/(args.id+'.md');target.parent.mkdir(exist_ok=True)
        target.write_text(draft(item,profile),encoding='utf-8');print(target)

if __name__=='__main__':main()
