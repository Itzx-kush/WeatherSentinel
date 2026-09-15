from pydantic import BaseModel
class DetectionMetrics(BaseModel):precision:float;recall:float;f1:float;specificity:float;false_positive_rate:float;false_negative_rate:float;tp:int;fp:int;tn:int;fn:int
def detection_metrics(truth,pred):
 if len(truth)!=len(pred) or not truth:raise ValueError("equal non-empty inputs required")
 tp=sum(bool(t) and bool(p) for t,p in zip(truth,pred));fp=sum(not bool(t) and bool(p) for t,p in zip(truth,pred));tn=sum(not bool(t) and not bool(p) for t,p in zip(truth,pred));fn=sum(bool(t) and not bool(p) for t,p in zip(truth,pred));div=lambda a,b:a/b if b else 0;p=div(tp,tp+fp);r=div(tp,tp+fn);return DetectionMetrics(precision=p,recall=r,f1=div(2*p*r,p+r),specificity=div(tn,tn+fp),false_positive_rate=div(fp,fp+tn),false_negative_rate=div(fn,fn+tp),tp=tp,fp=fp,tn=tn,fn=fn)
def detection_delay(truth,pred,timestamps):
 starts=[i for i,x in enumerate(truth) if x and (i==0 or not truth[i-1])];return [None if (hit:=next((i for i in range(start,len(pred)) if pred[i]),None)) is None else (timestamps[hit]-timestamps[start]).total_seconds() for start in starts]
def classification_metrics(truth,pred):
 if len(truth)!=len(pred) or not truth:raise ValueError("equal non-empty inputs required")
 labels=sorted(set(truth)|set(pred));matrix={a:{p:0 for p in labels} for a in labels}
 for a,p in zip(truth,pred):matrix[a][p]+=1
 per={}
 for label in labels:
  tp=matrix[label][label];fp=sum(matrix[a][label] for a in labels if a!=label);fn=sum(matrix[label][p] for p in labels if p!=label);precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0;per[label]={"precision":precision,"recall":recall,"f1":2*precision*recall/(precision+recall) if precision+recall else 0,"support":sum(matrix[label].values())}
 return {"accuracy":sum(a==p for a,p in zip(truth,pred))/len(truth),"macro_f1":sum(v["f1"] for v in per.values())/len(labels),"confusion_matrix":matrix,"per_class":per}
