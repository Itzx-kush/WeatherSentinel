from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel,Field
from app.schemas.models import AWSObservation
class FaultType(StrEnum):SPIKE="spike";FREEZE="freeze";DRIFT="drift";STEP_CHANGE="step_change";BIAS="bias";DROPOUT="dropout";COMMUNICATION_GAP="communication_gap"
class InjectionMetadata(BaseModel):source_dataset_id:str;dataset_id:str;fault_type:FaultType;station_id:str;sensor:str;start_time:datetime;end_time:datetime;magnitude:float|None;parameters:dict=Field(default_factory=dict);random_seed:int=26073;generation_version:str="fault-injection-v1"
class InjectedDataset(BaseModel):observations:list[AWSObservation];labels:list[bool];metadata:InjectionMetadata
def inject(rows,*,source_dataset_id,dataset_id,fault_type,sensor,start,end,magnitude=10,station_id=None,random_seed=26073):
 original=[r.model_copy(deep=True) for r in rows];idx=[i for i,r in enumerate(original) if start<=i<=end and (station_id is None or r.station_id==station_id)]
 if not idx:raise ValueError("injection selects no rows")
 station_id=station_id or original[idx[0]].station_id;base=getattr(original[max(0,idx[0]-1)],sensor);labels=[False]*len(original)
 if fault_type==FaultType.COMMUNICATION_GAP:output=[r for i,r in enumerate(original) if i not in idx];labels=[False]*len(output);labels[min(start,len(output)-1)]=True
 else:
  output=original
  for offset,i in enumerate(idx,1):
   labels[i]=True;cur=getattr(output[i],sensor)
   if fault_type==FaultType.SPIKE:setattr(output[i],sensor,cur+magnitude);labels[i]=i==idx[0]
   elif fault_type==FaultType.FREEZE:setattr(output[i],sensor,base)
   elif fault_type==FaultType.DRIFT:setattr(output[i],sensor,cur+magnitude*offset/len(idx))
   elif fault_type==FaultType.STEP_CHANGE:setattr(output[i],sensor,cur+magnitude)
   elif fault_type==FaultType.BIAS:setattr(output[i],sensor,cur+magnitude*min(1,offset/3))
   elif fault_type==FaultType.DROPOUT:setattr(output[i],sensor,None)
 meta=InjectionMetadata(source_dataset_id=source_dataset_id,dataset_id=dataset_id,fault_type=fault_type,station_id=station_id,sensor=sensor,start_time=original[idx[0]].timestamp,end_time=original[idx[-1]].timestamp,magnitude=magnitude,parameters={"start":start,"end":end},random_seed=random_seed);return InjectedDataset(observations=output,labels=labels,metadata=meta)
