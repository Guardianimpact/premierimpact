"""Async runner for SEO600 content generation with CLI interface."""

import argparse
import asyncio
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seo600.checkpoints import CheckpointManager
from seo600.cities import ALL_CITIES, get_city
from seo600.generator import generate_content

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "seo600", "generated")
SERVICES = ["impact-windows", "impact-doors", "roofing"]

BATCH_SIZE = 20  # Process this many at a time to avoid memory/crash issues
CONCURRENCY = 10  # Max simultaneous API calls


def get_output_path(service_slug: str, city_slug: str) -> str:
    return os.path.join(DATA_DIR, service_slug, f"{city_slug}.json")


def make_key(service_slug: str, city_slug: str) -> str:
    return f"{service_slug}/{city_slug}"


async def generate_one(
    city: dict,
    service_slug: str,
    checkpoint: CheckpointManager,
    semaphore: asyncio.Semaphore,
    counter: dict,
):
    key = make_key(service_slug, city["slug"])

    if checkpoint.is_done(key):
        counter["skipped"] += 1
        return

    async with semaphore:
        try:
            content = await generate_content(city, service_slug)

            out_path = get_output_path(service_slug, city["slug"])
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

            checkpoint.mark_done(key)
            counter["success"] += 1
            done = counter["success"] + counter["failed"] + counter["skipped"]
            print(f"  [{done}/{counter['total']}] OK: {key}", flush=True)

        except Exception as e:
            checkpoint.mark_failed(key, str(e))
            counter["failed"] += 1
            done = counter["success"] + counter["failed"] + counter["skipped"]
            print(f"  [{done}/{counter['total']}] FAIL: {key} — {e}", flush=True)


async def run_all(
    services: list[str] | None = None,
    city_slug: str | None = None,
    resume: bool = False,
    regenerate: bool = False,
):
    checkpoint = CheckpointManager()

    if regenerate:
        checkpoint.generated = []
        checkpoint.failed = {}
        checkpoint.save()
        print("Cleared all checkpoints for regeneration.", flush=True)

    target_services = services or SERVICES
    target_cities = ALL_CITIES
    if city_slug:
        city = get_city(city_slug)
        if not city:
            print(f"City not found: {city_slug}")
            return
        target_cities = [city]

    # Build list of remaining tasks only
    all_tasks = []
    skipped = 0
    for service in target_services:
        for city in target_cities:
            key = make_key(service, city["slug"])
            if resume and checkpoint.is_done(key):
                skipped += 1
            else:
                all_tasks.append((city, service))

    total = len(all_tasks) + skipped
    counter = {
        "success": 0,
        "failed": 0,
        "skipped": skipped,
        "total": total,
    }

    print(f"SEO600 Builder — {total} total pages", flush=True)
    print(f"Services: {', '.join(target_services)}", flush=True)
    print(f"Cities: {len(target_cities)}", flush=True)
    print(f"Already done: {skipped}, Remaining: {len(all_tasks)}", flush=True)
    print(f"Batch size: {BATCH_SIZE}, Concurrency: {CONCURRENCY}", flush=True)
    print(flush=True)

    if not all_tasks:
        print("Nothing to do — all pages already generated!", flush=True)
        return

    semaphore = asyncio.Semaphore(CONCURRENCY)
    start = time.time()

    # Process in batches to avoid memory issues
    for i in range(0, len(all_tasks), BATCH_SIZE):
        batch = all_tasks[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(all_tasks) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"--- Batch {batch_num}/{total_batches} ({len(batch)} pages) ---", flush=True)

        coros = [
            generate_one(city, service, checkpoint, semaphore, counter)
            for city, service in batch
        ]
        await asyncio.gather(*coros)

        # Brief pause between batches
        if i + BATCH_SIZE < len(all_tasks):
            await asyncio.sleep(1)

    elapsed = time.time() - start
    print(f"\n{'='*50}", flush=True)
    print(f"SEO600 Build Complete in {elapsed:.1f}s", flush=True)
    print(f"  Succeeded: {counter['success']}", flush=True)
    print(f"  Failed:    {counter['failed']}", flush=True)
    print(f"  Skipped:   {counter['skipped']}", flush=True)
    print(f"  Total:     {counter['total']}", flush=True)

    # Auto-retry failed pages (up to 2 retry rounds)
    for retry_round in range(1, 3):
        if not checkpoint.failed:
            break
        failed_keys = list(checkpoint.failed.keys())
        print(f"\n--- Retry round {retry_round}: {len(failed_keys)} failed pages ---", flush=True)
        checkpoint.failed = {}
        checkpoint.save()

        retry_tasks = []
        for key in failed_keys:
            svc_slug, city_slug = key.split("/", 1)
            city = get_city(city_slug)
            if city:
                retry_tasks.append((city, svc_slug))

        for i in range(0, len(retry_tasks), BATCH_SIZE):
            batch = retry_tasks[i:i + BATCH_SIZE]
            coros = [
                generate_one(city, service, checkpoint, semaphore, counter)
                for city, service in batch
            ]
            await asyncio.gather(*coros)
            if i + BATCH_SIZE < len(retry_tasks):
                await asyncio.sleep(2)

    # Final report
    if checkpoint.failed:
        print(f"\nStill failed after retries ({len(checkpoint.failed)}):", flush=True)
        for key, err in checkpoint.failed.items():
            print(f"  {key}: {err}", flush=True)
    else:
        print(f"\nAll pages generated successfully!", flush=True)


def show_status():
    checkpoint = CheckpointManager()
    s = checkpoint.status()
    total = len(ALL_CITIES) * len(SERVICES)
    print(f"SEO600 Status")
    print(f"  Generated: {s['generated']}/{total}")
    print(f"  Failed:    {s['failed']}")
    print(f"  Remaining: {total - s['generated']}")
    print(f"  Last run:  {s['last_run'] or 'Never'}")
    if s["failed_keys"]:
        print(f"\n  Failed pages:")
        for k in s["failed_keys"]:
            print(f"    {k}")


def toggle_enabled(enable: bool):
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("SEO600_ENABLED"):
                    f.write(f"SEO600_ENABLED={'true' if enable else 'false'}\n")
                else:
                    f.write(line)
    print(f"SEO600 {'enabled' if enable else 'disabled'}")


def main():
    parser = argparse.ArgumentParser(description="SEO600 Location Page Builder")
    parser.add_argument("--run", action="store_true", help="Run content generation")
    parser.add_argument("--service", type=str, help="Generate for specific service only")
    parser.add_argument("--city", type=str, help="Generate for specific city slug only")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--status", action="store_true", help="Show generation status")
    parser.add_argument("--regenerate", action="store_true", help="Clear checkpoints and regenerate all")
    parser.add_argument("--disable", action="store_true", help="Disable SEO600 pages")
    parser.add_argument("--enable", action="store_true", help="Enable SEO600 pages")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.disable:
        toggle_enabled(False)
    elif args.enable:
        toggle_enabled(True)
    elif args.run:
        services = [args.service] if args.service else None
        asyncio.run(
            run_all(
                services=services,
                city_slug=args.city,
                resume=args.resume,
                regenerate=args.regenerate,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
