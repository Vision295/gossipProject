import docker
import asyncio
import time
import os
import re
import json
from docker.models.containers import Container


def new_experience(experience_type: str) -> dict:
    with open("exp_count.json", "r") as f:
        data = json.load(f)
        data[experience_type] += 1
    with open("exp_count.json", "w") as f:
        json.dump(data, f)
    return data


experiences = new_experience("full_mesh")

home = "/run/media/theophile/Windows/Users/theop/Documents/_Perso/_Etudes/_INSA/_4TC1/networksProject/code/results"
DEST_DIR = os.path.expanduser(home + f"/{experiences['full_mesh']}")
os.makedirs(DEST_DIR, exist_ok=True)


# ---------------------------------------------------------
# ✅ WRAPPER: run docker.exec_run (which is blocking) ASYNC
# ---------------------------------------------------------
async def async_exec(container: Container, command: str, user="root", detach=True):
    return await asyncio.to_thread(
        container.exec_run,
        command,
        user=user,
        detach=detach
    )


async def exec_gossip(container: Container):
    try:
        # IMPORTANT: Async call to avoid CPU bursts
        await async_exec(
            container,
            "bash -c 'cd /app && ./entrypoint.sh &'",
            user="root",
            detach=True
        )
        print(f"  ✅ Started gossip in {container.name}")
    except Exception as e:
        print(f"  ⚠️ Failed in {container.name}: {e}")


async def async_sleep(ms: int):
    await asyncio.sleep(ms / 1000.0)


def find_node_idx(container: Container) -> str:
    config_result = container.exec_run("cat /app/push_config.toml", user="root")
    config_content = config_result.output.decode(errors="ignore")

    match = re.search(r"NODE_IDX\s*=\s*(\S+)", config_content)
    node_idx = match.group(1).strip() if match else container.name
    return str(node_idx)


async def start_gossip(container_list: list[Container]):
    sender = None

    # Launch EVERY container asynchronously but spaced out
    for container in container_list:
        print(f"→ Starting gossip in {container.name}")

        # ✅ CRUCIAL: stagger execution to avoid CPU starvation
        await async_sleep(120)   # 120 ms — tweak if needed

        node_idx = find_node_idx(container)

        if node_idx == "1":
            sender = container
        else:
            asyncio.create_task(exec_gossip(container))

    # sender last
    if sender:
        await async_sleep(150)
        asyncio.create_task(exec_gossip(sender))


def fetch_rename_logs(container: Container) -> None:
    print(f"→ Fetching logs from {container.name}")

    node_idx = find_node_idx(container)

    log_result = container.exec_run("cat /app/log.txt", user="root")
    log_content = log_result.output.decode(errors="ignore")

    dest_path = os.path.join(DEST_DIR, f"{node_idx}.txt")
    with open(dest_path, "w") as f:
        f.write(log_content)
    print(f"  ✅ Saved {dest_path}")


async def run_gossip_sequence(wait_seconds: int = 60):
    client = docker.from_env()
    containers: list[Container] = client.containers.list(filters={"status": "running"})

    print(f"Found {len(containers)} running containers")

    await start_gossip(containers)

    print(f"⏳ Waiting {wait_seconds} seconds...")
    await asyncio.sleep(wait_seconds)

    # Fetch logs (sync)
    for container in containers:
        try:
            fetch_rename_logs(container)
        except Exception as e:
            print(f"  ⚠️ Failed fetching from {container.name}: {e}")

    print("🎯 All logs collected into", DEST_DIR)


if __name__ == "__main__":
    asyncio.run(run_gossip_sequence(wait_seconds=60))
