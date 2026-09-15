"""Part 1 command-line interface; outputs computed records as JSON Lines."""

import argparse
import asyncio
from pathlib import Path

from app.data.loaders import DataIngestor
from app.replay.engine import replay_observations
from app.schemas.models import SourceType
from app.services.pipeline import FoundationPipeline


def process(args):
    ingestor = DataIngestor()
    source = SourceType(args.source_type)
    loaded = (
        ingestor.from_parquet(args.input, dataset_id=args.dataset_id, source_type=source)
        if Path(args.input).suffix.lower() in {".parquet", ".pq"}
        else ingestor.from_csv(args.input, dataset_id=args.dataset_id, source_type=source)
    )
    result = FoundationPipeline().run(loaded)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.output).open("w", encoding="utf-8") as f:
        for record in result.records:
            f.write(record.model_dump_json() + "\n")
    print(result.model_dump_json(exclude={"records"}))


async def replay(args):
    loaded = DataIngestor().from_csv(
        args.input, dataset_id=args.dataset_id, source_type=SourceType(args.source_type)
    )
    async for row in replay_observations(loaded.observations, speed=args.speed):
        print(row.model_dump_json())


def main():
    parser = argparse.ArgumentParser(prog="weather-sentinel")
    sub = parser.add_subparsers(required=True)
    for name in ("process", "replay"):
        p = sub.add_parser(name)
        p.add_argument("--input", required=True)
        p.add_argument("--dataset-id", default="example")
        p.add_argument("--source-type", choices=[x.value for x in SourceType], default="unknown")
        if name == "process":
            p.add_argument("--output", default="data/processed/features.jsonl")
            p.set_defaults(fn=process)
        else:
            p.add_argument("--speed", type=float, default=60)
            p.set_defaults(fn=lambda a: asyncio.run(replay(a)))
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
