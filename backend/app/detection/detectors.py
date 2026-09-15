import math,random,statistics
from dataclasses import dataclass
from app.detection.contracts import DetectorEvidence,ModelMetadata
SENSORS=("temperature_c","pressure_hpa","relative_humidity_pct")
def ev(r,n,f,s,score,threshold,hit,reason,features=None,severity=0,enough=True):return DetectorEvidence(detector_name=n,family=f,timestamp=r.observation.timestamp,station_id=r.observation.station_id,affected_sensors=s,raw_score=score,normalized_score=None if score is None else max(0,min(1,score)),threshold=threshold,triggered=hit,reason=reason,features=features or {},severity_contribution=max(0,min(1,severity)),sufficient_history=enough)
class RuleDetector:
 weights={"missing_value":.9,"physical_range":1,"duplicate_timestamp":.8,"communication_gap":.8,"frozen_value":.8,"abrupt_change":.6}
 def detect(self,r):
  out=[]
  for flag in r.quality_flags:
   score=self.weights.get(flag.code,.3);s=[flag.field] if flag.field in SENSORS else [];out.append(ev(r,"quality_rules","rule",s,score,.5,True,f"{flag.code}: {flag.message}",{"code":flag.code,"observed":flag.observed,"expected":flag.expected},score))
  return out or [ev(r,"quality_rules","rule",[],0,.5,False,"No quality rule triggered")]
class StatisticalDetector:
 def __init__(self,threshold=4):self.threshold=threshold
 def detect(self,r):
  out=[]
  for s in SENSORS:
   cur=getattr(r.observation,s);med=r.normal_baseline[s];std=r.temporal_features[s].get("rolling_std")
   if cur is None or med is None or std is None or std<=1e-9:out.append(ev(r,"rolling_z","statistical",[s],None,self.threshold,False,"Insufficient past-only variance",{"median":med,"std":std},enough=False));continue
   z=abs(cur-med)/std;score=min(1,z/(self.threshold*1.25));out.append(ev(r,"rolling_z","statistical",[s],score,.8,z>=self.threshold,f"Past-only z score {z:.3f}",{"z_score":z,"median":med,"std":std,"observed":cur},score))
  return out
class TemporalDetector:
 def __init__(self,rate=None,persistence=4):self.rate=rate or {"temperature_c":12,"pressure_hpa":12,"relative_humidity_pct":45};self.persistence=persistence;self.state={}
 def detect(self,r):
  out=[]
  for s in SENSORS:
   f=r.temporal_features[s];cur=getattr(r.observation,s);delta=f.get("rate_of_change");count=f.get("persistence_count",0);base=r.normal_baseline[s];key=(r.observation.station_id,s);st=self.state.setdefault(key,{"candidate":None,"age":0,"residuals":[]});res=cur-base if cur is not None and base is not None else 0;st["residuals"].append(res);del st["residuals"][:-6];score=min(1,abs(delta or 0)/self.rate[s]);pattern="normal";hit=False
   if count>=self.persistence:pattern="freeze";hit=True;score=1
   elif score>=1:pattern="abrupt";hit=True;st["candidate"]=(base,cur);st["age"]=0
   elif st["candidate"] and cur is not None:
    old,new=st["candidate"];st["age"]+=1
    if old is not None and new is not None and abs(cur-new)<abs(cur-old) and st["age"]>=2:pattern="step";hit=True;score=.9
    elif st["age"]>4:st["candidate"]=None
   recent=st["residuals"][-4:]
   if not hit and len(recent)==4 and all(abs(x)>0 for x in recent):
    same=all(x>0 for x in recent) or all(x<0 for x in recent);mono=all(abs(recent[i])<=abs(recent[i+1]) for i in range(3))
    if same and mono and abs(recent[-1])>=self.rate[s]/2:pattern="drift";hit=True;score=.85
    elif same and max(recent)-min(recent)<=max(1,abs(sum(recent)/4)*.2) and abs(sum(recent)/4)>=self.rate[s]/2:pattern="bias";hit=True;score=.82
   out.append(ev(r,"temporal_patterns","temporal",[s],score,.8,hit,f"pattern={pattern}",{"pattern":pattern,"rate_of_change":delta,"persistence_count":count,"residual":res},score))
  return out
class MultivariateDetector:
 def __init__(self,threshold=4.5):self.threshold=threshold
 def detect(self,r):
  z={}
  for s in SENSORS:
   cur=getattr(r.observation,s);med=r.normal_baseline[s];std=r.temporal_features[s].get("rolling_std")
   if cur is not None and med is not None and std is not None and std>1e-9:z[s]=(cur-med)/std
  if len(z)<2:return [ev(r,"diagonal_mahalanobis","multivariate",[],None,self.threshold,False,"Insufficient joint history",{"residuals":z},enough=False)]
  d=math.sqrt(sum(x*x for x in z.values()));score=min(1,d/(self.threshold*1.25));affected=[max(z,key=lambda s:abs(z[s]))];return [ev(r,"diagonal_mahalanobis","multivariate",affected,score,.8,d>=self.threshold,f"Joint distance {d:.3f}",{"distance":d,"residuals":z},score)]
@dataclass
class Node:size:int;feature:int|None=None;split:float|None=None;left:object=None;right:object=None
def c(n):return 0 if n<=1 else 1 if n==2 else 2*(math.log(n-1)+.5772156649)-2*(n-1)/n
class IsolationForestDetector:
 def __init__(self,trees=64,sample_size=64,threshold=.62,seed=26073):self.tree_count=trees;self.sample_size=sample_size;self.threshold=threshold;self.seed=seed;self.trees=[];self.metadata=None
 @staticmethod
 def vector(r):return [r.observation.temperature_c,r.observation.pressure_hpa,r.observation.relative_humidity_pct]
 def build(self,rows,depth,limit,rng):
  if len(rows)<=1 or depth>=limit:return Node(len(rows))
  choices=[j for j in range(3) if min(x[j] for x in rows)<max(x[j] for x in rows)]
  if not choices:return Node(len(rows))
  j=rng.choice(choices);lo=min(x[j] for x in rows);hi=max(x[j] for x in rows);split=rng.uniform(lo,hi);left=[x for x in rows if x[j]<split];right=[x for x in rows if x[j]>=split]
  return Node(len(rows)) if not left or not right else Node(len(rows),j,split,self.build(left,depth+1,limit,rng),self.build(right,depth+1,limit,rng))
 def fit(self,records,dataset_id):
  raw=[self.vector(r) for r in records];raw=[x for x in raw if all(v is not None for v in x)]
  if len(raw)<8:raise ValueError("at least 8 complete baseline rows required")
  cols=list(zip(*raw));self.center=[statistics.median(x) for x in cols];self.scale=[max(statistics.quantiles(x,n=4)[2]-statistics.quantiles(x,n=4)[0],1e-9) for x in cols];rows=[[(v-a)/b for v,a,b in zip(x,self.center,self.scale)] for x in raw];rng=random.Random(self.seed);size=min(self.sample_size,len(rows));limit=math.ceil(math.log2(size));self.trees=[self.build(rng.sample(rows,size),0,limit,rng) for _ in range(self.tree_count)];self.metadata=ModelMetadata(model_name="IsolationForest",model_version="1.0.0",training_dataset_id=dataset_id,feature_version="aws-core-v1",preprocessing_version="median-iqr-v1",random_seed=self.seed,threshold=self.threshold,training_rows=len(rows),configuration={"trees":self.tree_count,"sample_size":size});return self
 def path(self,x,n,d=0):return d+c(n.size) if n.feature is None else self.path(x,n.left if x[n.feature]<n.split else n.right,d+1)
 def detect(self,r):
  if not self.trees:return [ev(r,"isolation_forest","ml",[],None,self.threshold,False,"Model not fitted; inference never retrains",enough=False)]
  raw=self.vector(r)
  if any(v is None for v in raw):return [ev(r,"isolation_forest","ml",[],None,self.threshold,False,"Incomplete ML vector",enough=False)]
  x=[(v-a)/b for v,a,b in zip(raw,self.center,self.scale)];size=self.metadata.configuration["sample_size"];score=2**(-statistics.fmean(self.path(x,t) for t in self.trees)/c(size));sensor=SENSORS[max(range(3),key=lambda i:abs(x[i]))];return [ev(r,"isolation_forest","ml",[sensor],score,self.threshold,score>=self.threshold,f"Isolation score {score:.4f}",{"scaled_features":dict(zip(SENSORS,x)),"model":self.metadata.model_dump(mode="json")},score)]
