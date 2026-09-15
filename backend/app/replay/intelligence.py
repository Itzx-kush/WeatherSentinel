from collections.abc import AsyncIterator
from app.replay.engine import replay_observations
from app.schemas.models import DatasetProvenance,IngestionResult,SourceType
from app.services.intelligence import IntelligenceRecord,IntelligenceService
async def replay_intelligence(observations,*,dataset_id,source_type=SourceType.UNKNOWN,speed=0,max_sleep_seconds=5,sleeper=None)->AsyncIterator[IntelligenceRecord]:
 ordered=sorted(observations,key=lambda r:r.timestamp);ing=IngestionResult(observations=ordered,errors=[],provenance=DatasetProvenance(dataset_id=dataset_id,source_filename="replay",source_type=source_type,record_count=len(ordered)));records=IntelligenceService().run(ing).records;kwargs={"speed":speed,"max_sleep_seconds":max_sleep_seconds}
 if sleeper is not None:kwargs["sleeper"]=sleeper
 i=0
 async for _ in replay_observations(ordered,**kwargs):yield records[i];i+=1
