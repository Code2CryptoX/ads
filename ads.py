import asyncio
import aiohttp
import json
import urllib.parse
from rich.table import Table
from rich.console import Console
from rich.live import Live

# ========== CONSOLE / THEME ==========
console = Console()

# ========== BANNER ==========
def print_banner():
    console.print("=" * 60, style="green")
    console.print("📢 Channel   : Code2Crypto", style="green")
    console.print("🚀 Tool Name : AdsEvm Bot", style="green")
    console.print("👨‍💻 Dev      : @Anaik_Dev", style="green")
    console.print("=" * 60, style="green")

# ========== API CONFIG ==========
URL = "https://adsevm.saifpowersoft.top/api/watched.php"
NETWORKS = ["gigapub", "monetag"]

HEADERS = {
    "authority": "adsevm.saifpowersoft.top",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://adsevm.saifpowersoft.top",
    "referer": "https://adsevm.saifpowersoft.top/?tgWebAppStartParam=5472249596",
    "save-data": "on",
    "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
}

# ========== SINGLE ACCOUNT FROM QUERY ID (NO SAVE) ==========
def get_account_from_query():
    query_id = input("🔑 Enter query_id: ").strip()
    try:
        parsed = urllib.parse.parse_qs(query_id)
        user_json_str = parsed.get("user", [None])[0]
        if not user_json_str:
            raise ValueError("Missing 'user' field inside query_id.")
        user_json = json.loads(user_json_str)
        user_id = user_json["id"]
        console.print(f"✅ Loaded account: {user_id}", style="green")
        return {"user_id": user_id, "init_data": query_id}
    except Exception as e:
        console.print(f"❌ Invalid query_id: {e}", style="green")
        return None

# ========== WORKER: WATCH ADS FOR ONE NETWORK ==========
async def watch_ads(session, account, net, status_dict):
    data = {
        "user_id": account["user_id"],
        "init_data": account["init_data"],
        "network": net
    }
    user_id = account["user_id"]

    while True:
        try:
            async with session.post(URL, headers=HEADERS, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    balance = result.get("new_balance", "-")
                    ads_today = result.get("ads_watched_today", 0)
                    daily_limit = result.get("daily_limit", 0)

                    status = f"{ads_today}/{daily_limit} | Balance: {balance}"
                    if isinstance(ads_today, int) and isinstance(daily_limit, int) and ads_today >= daily_limit:
                        status += " 🚫 LIMIT"
                        status_dict[user_id][net] = status
                        # Cooldown if limit reached
                        await asyncio.sleep(60)
                    else:
                        status_dict[user_id][net] = status
                else:
                    status_dict[user_id][net] = f"Error {resp.status}"
        except Exception as e:
            status_dict[user_id][net] = f"Exception: {type(e).__name__}"
        # Short delay between requests
        await asyncio.sleep(2)

# ========== LIVE TABLE ==========
async def display_table(status_dict, account):
    with Live(refresh_per_second=1) as live:
        while True:
            table = Table(title="💰 AdsEvm Bot | Code2Crypto", style="green")
            table.add_column("User ID", justify="center", style="green")
            for net in NETWORKS:
                table.add_column(net, justify="center", style="green")

            user_id = account["user_id"]
            row = [str(user_id)]
            for net in NETWORKS:
                row.append(status_dict[user_id].get(net, "-"))
            table.add_row(*row)

            live.update(table)
            await asyncio.sleep(1)

# ========== MAIN ==========
async def main():
    print_banner()

    account = get_account_from_query()
    if not account:
        return

    status_dict = {account["user_id"]: {}}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for net in NETWORKS:
            tasks.append(asyncio.create_task(watch_ads(session, account, net, status_dict)))
        tasks.append(asyncio.create_task(display_table(status_dict, account)))
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n🛑 Stopped by user.", style="green")