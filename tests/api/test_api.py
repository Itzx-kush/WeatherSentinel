import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.models import AWSObservation, StationMetadata

@pytest.mark.asyncio
async def test_health_and_processing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health = await client.get('/health')
        assert health.status_code == 200
        station = StationMetadata(station_id='TEST-1', name='Test', latitude=17.7, longitude=83.3)
        await client.post('/api/v1/stations/register', json={'stations':[station.model_dump(mode='json')]})
        rows=[]
        from datetime import datetime, UTC, timedelta
        for i in range(10):
            rows.append(AWSObservation(station_id='TEST-1', timestamp=datetime(2026,1,1,tzinfo=UTC)+timedelta(minutes=10*i), temperature_c=25+i*0.1, pressure_hpa=1013, relative_humidity_pct=70))
        response=await client.post('/api/v1/observations/process',json={'dataset_id':'test','observations':[r.model_dump(mode='json') for r in rows]})
        assert response.status_code == 200
        assert len(response.json()['results']) == 10

@pytest.mark.asyncio
async def test_status_models():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        status=await client.get('/api/v1/status')
        models=await client.get('/api/v1/models')
        assert status.status_code==200
        assert models.status_code==200
        assert models.json()['models'][0]['integrated'] is True
