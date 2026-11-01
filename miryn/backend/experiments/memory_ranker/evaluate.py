"""Baseline (repo hand weights) vs learned ranker, persona-grouped CV. Synthetic data only."""
import json, re, math, numpy as np
from fastembed import TextEmbedding
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
rows=[json.loads(l) for l in open('data/personas.jsonl')]
emb=TextEmbedding('BAAI/bge-small-en-v1.5')
CATS=sorted({m['category'] for r in rows for m in r['memories']})
tok=lambda s:set(re.findall(r'[a-z0-9]+',s.lower()))
X=[];y=[];g=[];qid=[];kind=[];base=[]
q=0
for pi,r in enumerate(rows):
    M=r['memories'];me=np.array(list(emb.embed([m['text'] for m in M])))
    qe=np.array(list(emb.embed([x['text'] for x in r['queries']])))
    for qi,qq in enumerate(r['queries']):
        sims=me@qe[qi]; qt=tok(qq['text'])
        for mi,m in enumerate(M):
            d=m['days_ago'];rec=math.exp(-0.1*d)
            lex=len(qt&tok(m['text']))/max(1,len(qt))
            f=[sims[mi],rec,0.5,math.log1p(d),lex,sims[mi]-sims.max(),(sims>sims[mi]).sum()]+[m['category']==c for c in CATS]
            X.append(f);y.append(m['id'] in qq['relevant']);g.append(pi);qid.append(q)
            base.append(0.5*sims[mi]+0.3*rec+0.2*0.5)
        kind.append(qq['kind']);q+=1
X=np.array(X,float);y=np.array(y);g=np.array(g);qid=np.array(qid);base=np.array(base)
def metrics(score):
    out=[]
    for k in range(q):
        i=np.where(qid==k)[0];o=i[np.argsort(-score[i])];rel=y[o]
        if rel.sum()==0: out.append((np.nan,)*3);continue
        top=rel[:5];dcg=sum(t/math.log2(j+2) for j,t in enumerate(top))
        idcg=sum(1/math.log2(j+2) for j in range(min(5,int(rel.sum()))))
        mrr=1/(np.argmax(rel)+1);out.append((dcg/idcg,top.sum()/rel.sum(),mrr))
    return np.array(out)
lr=np.zeros(len(y));gb=np.zeros(len(y))
for tr,te in GroupKFold(5).split(X,y,g):
    s=lambda m:m.fit(X[tr],y[tr]).predict_proba(X[te])[:,1]
    lr[te]=s(LogisticRegression(max_iter=2000,C=1.0)) if False else s(LogisticRegression(max_iter=2000))
    gb[te]=s(HistGradientBoostingClassifier(max_iter=100,max_depth=3,learning_rate=0.05,random_state=0))
sem=X[:,0]
res={n:metrics(s) for n,s in [('semantic_only',sem),('baseline_0.5/0.3/0.2',base),('logreg',lr),('gbdt',gb)]}
qp=np.array([g[np.where(qid==k)[0][0]] for k in range(q)]);kind=np.array(kind)
rng=np.random.default_rng(0);up=np.unique(qp)
def ci(a,b=None):
    v=[]
    for _ in range(2000):
        s=rng.choice(up,len(up));idx=np.concatenate([np.where(qp==p)[0] for p in s])
        x=a[idx]-(b[idx] if b is not None else 0);v.append(np.nanmean(x))
    return np.nanmean(a if b is None else a-b),np.percentile(v,2.5),np.percentile(v,97.5)
out=[f"personas={len(rows)} queries={q} memories/persona=24 (candidate pool = all memories; recall ceiling 1.0)\n","## Overall (5-fold persona-grouped CV; mean [95% persona-bootstrap CI])\n","| ranker | nDCG@5 | recall@5 | MRR |","|---|---|---|---|"]
for n,a in res.items():
    out.append(f"| {n} | "+" | ".join("%.3f [%.3f,%.3f]"%ci(a[:,j]) for j in range(3))+" |")
out+=["\n## Paired difference vs baseline (positive = learned better)\n","| ranker | dnDCG@5 | drecall@5 | dMRR |","|---|---|---|---|"]
for n in('semantic_only','logreg','gbdt'):
    out.append(f"| {n} | "+" | ".join("%+.3f [%+.3f,%+.3f]"%ci(res[n][:,j],res['baseline_0.5/0.3/0.2'][:,j]) for j in range(3))+" |")
out+=["\n## Learned vs semantic-only (the honest comparison)\n","| ranker | dnDCG@5 | drecall@5 | dMRR |","|---|---|---|---|",*[f"| {n} | "+" | ".join("%+.3f [%+.3f,%+.3f]"%ci(res[n][:,j],res['semantic_only'][:,j]) for j in range(3))+" |" for n in('logreg','gbdt')],"\n## nDCG@5 by query kind (baseline / logreg / gbdt)\n","| kind | n | baseline | logreg | gbdt |","|---|---|---|---|---|"]
for k in sorted(set(kind)):
    m=kind==k;out.append(f"| {k} | {m.sum()} | "+" | ".join("%.3f"%np.nanmean(res[n][m,0]) for n in('baseline_0.5/0.3/0.2','logreg','gbdt'))+" |")
open('RESULTS.md','w').write("\n".join(out)+"\n");print("\n".join(out))
