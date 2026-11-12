#!/usr/bin/env python3
"""Rebuild data/epochs.csv from NEAR mainnet block headers. No keys, stdlib only.

Usage: python3 fetch.py [--epochs 1300]   epochs, then buyback balances
       python3 fetch.py buybacks          buyback balances only
       python3 fetch.py wallets           all three revenue wallets at the last window's ends
       python3 fetch.py protocol          protocol parameters cited in the thesis
       python3 fetch.py inflows           who sent NEAR to the buyback account (NearBlocks, third party)
       python3 fetch.py offchain          price and DefiLlama series (third party)
Resumable: epochs and balances already cached are not refetched.

Per epoch (exact, integer yoctoNEAR):
  mint = supply(first block) - supply(last block of previous epoch) + burnt(first block)
  burn = burnt(first block) + supply(first block) - supply(last block)
Per epoch (sampled, K blocks seeded by the epoch's first height): gas used, gas limit.
"""
import csv, json, os, random, sys, time, urllib.error, urllib.request

RPC = os.environ.get("NEAR_RPC", "https://archival-rpc.mainnet.fastnear.com")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "epochs.csv")
K = 3  # sampled blocks per epoch; the free sources allow short bursts, then block for minutes
FIELDS = ["start_height", "end_height", "prev_end_height", "t0_ns", "t1_ns",
          "supply_prev_end", "supply_start", "supply_end", "mint", "burn",
          "gas_price", "shards", "sample_n", "sample_gas_used", "sample_gas_limit"]


NEARDATA = os.environ.get("NEARDATA", "https://mainnet.neardata.xyz")
UA = {"Content-Type": "application/json", "User-Agent": "coverage-fetch"}


def rpc_block(block_id):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "block", "params": {"block_id": block_id}}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, UA), timeout=30))
    if "result" in r:
        return r["result"]
    if (r["error"].get("cause") or {}).get("name") == "UNKNOWN_BLOCK":
        return None
    raise RuntimeError(r["error"])


def neardata_block(height):  # same header and chunk fields as the RPC; null for a skipped height
    return json.load(urllib.request.urlopen(urllib.request.Request(
        f"{NEARDATA}/v0/block/{height}/headers", headers=UA), timeout=30))


turn = 0


def block(block_id):
    """Block by height or hash. None if the height was skipped.

    The two free sources have separate rate limits, so heights alternate between them.
    """
    global turn
    sources = [rpc_block, neardata_block] if isinstance(block_id, int) else [rpc_block]
    err, tries = None, 0
    while tries < 7:
        limited = 0
        for k in range(len(sources)):
            src = sources[(turn + k) % len(sources)]
            try:
                b = src(block_id)
                turn += 1
                return b
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    limited += 1
                else:
                    err = e
            except Exception as e:
                err = e
        if limited == len(sources):  # every source is rate limited: wait for a window, never give up
            time.sleep(3)
            continue
        tries += 1
        time.sleep(2 ** tries)
    sys.exit(f"fetch failed for block {block_id}: {err}")


def chunks(b):
    h = b["header"]["height"]
    return [c for c in b["chunks"] if c["height_included"] == h]


def burnt(b):
    return sum(int(c["balance_burnt"]) for c in chunks(b))


def fetch_epoch(end):
    """end = last block of the epoch. Returns (row, last block of the previous epoch)."""
    # next_epoch_id is the hash of the previous epoch's last block. Epochs are usually exactly
    # 43,200 heights long, so try that height first: it can be served by either source.
    prev_end = block(end["header"]["height"] - 43200)
    if not prev_end or prev_end["header"]["hash"] != end["header"]["next_epoch_id"]:
        prev_end = block(end["header"]["next_epoch_id"])
    h = prev_end["header"]["height"] + 1
    while (start := block(h)) is None:
        h += 1
    assert start["header"]["prev_hash"] == prev_end["header"]["hash"], "epoch boundary not contiguous"
    assert start["header"]["epoch_id"] == end["header"]["epoch_id"] != prev_end["header"]["epoch_id"]
    s0, s1, s2 = (int(b["header"]["total_supply"]) for b in (prev_end, start, end))
    sh, eh = start["header"]["height"], end["header"]["height"]
    heights = sorted(random.Random(sh).sample(range(sh + 1, eh + 1), K))
    sample = [b for b in map(block, heights) if b]
    cs = [c for b in sample for c in chunks(b)]
    row = dict(start_height=sh, end_height=eh, prev_end_height=prev_end["header"]["height"],
               t0_ns=prev_end["header"]["timestamp"], t1_ns=end["header"]["timestamp"],
               supply_prev_end=s0, supply_start=s1, supply_end=s2,
               mint=s1 - s0 + burnt(start), burn=burnt(start) + s1 - s2,
               gas_price=start["header"]["gas_price"], shards=len(start["chunks"]),
               sample_n=len(sample), sample_gas_used=sum(c["gas_used"] for c in cs),
               sample_gas_limit=sum(c["gas_limit"] for c in cs))
    return row, prev_end


BUYBACK = "buybacks.multisignature.near"  # receives NEAR bought with NEAR Intents fee revenue
BOUT = os.path.join(os.path.dirname(OUT), "buybacks.csv")
LLAMA = {  # third-party daily USD series, keyless; context and cross-checks only
    "near_fees_usd": "https://api.llama.fi/summary/fees/near?dataType=dailyFees",
    "near_burn_usd": "https://api.llama.fi/summary/fees/near?dataType=dailyRevenue",
    "intents_volume_usd": "https://api.llama.fi/summary/dexs/near-intents",
    "intents_fees_usd": "https://api.llama.fi/summary/fees/near-intents?dataType=dailyFees",
    "intents_buyback_usd": "https://api.llama.fi/summary/fees/near-intents?dataType=dailyHoldersRevenue",
}


def balance(height):
    """NEAR held by the buyback account at a block height, in yoctoNEAR. None before the account existed."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "query", "params": {
        "request_type": "view_account", "block_id": height, "account_id": BUYBACK}}).encode()
    while True:
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, UA), timeout=30))
            if "result" in r:
                return int(r["result"]["amount"]) + int(r["result"]["locked"])
            if (r["error"].get("cause") or {}).get("name") == "UNKNOWN_ACCOUNT":
                return None
            sys.exit(f"balance query failed at {height}: {r['error']}")
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(5)
        except OSError:  # dropped connection: try again
            time.sleep(5)


REVENUE_WALLETS = [BUYBACK, "fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"]


def query(params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "query", "params": params}).encode()
    while True:
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, UA), timeout=30))
            if "result" in r:
                return r["result"]
            if (r["error"].get("cause") or {}).get("name") == "UNKNOWN_ACCOUNT":
                return None  # the account did not exist at that height
            sys.exit(f"query failed: {params} -> {r['error']}")
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(5)
        except OSError:  # dropped connection: try again
            time.sleep(5)


def wallets():
    """NEAR plus wNEAR held by all three NEAR Intents revenue wallets at both ends of the last
    100-epoch window, and at any extra heights given. A wider cross-check of the buyback figure."""
    import base64
    rows = sorted(csv.DictReader(open(OUT)), key=lambda r: int(r["start_height"]))
    out = []
    # extra heights on the command line, e.g. both ends of an epoch with a lump transfer
    extra = [int(a) for a in sys.argv[2:]]
    for h in sorted({int(rows[-100]["prev_end_height"]), int(rows[-1]["end_height"]), *extra}):
        for acct in REVENUE_WALLETS:
            a = query({"request_type": "view_account", "block_id": h, "account_id": acct})
            args = base64.b64encode(json.dumps({"account_id": acct}).encode()).decode()
            w = query({"request_type": "call_function", "block_id": h, "account_id": "wrap.near",
                       "method_name": "ft_balance_of", "args_base64": args})
            if "error" in w:  # a failed view call must not be recorded as a zero balance
                sys.exit(f"ft_balance_of failed for {acct} at {h}: {w['error']}")
            out.append([h, acct, int(a["amount"]) + int(a["locked"]) if a else 0, int(json.loads(bytes(w["result"])))])
    with open(os.path.join(os.path.dirname(OUT), "wallets.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["height", "account", "near", "wnear"])
        w.writerows(out)
    stamp("wallets.csv", [RPC + " query view_account / call_function wrap.near ft_balance_of"])
    print(f"wrote wallets.csv ({len(out)} rows)")


def stamp(name, urls):
    """Record when a file in data/ was fetched, from where, and its sha256, in data/sources.json."""
    import hashlib
    path = os.path.join(os.path.dirname(OUT), "sources.json")
    src = json.load(open(path)) if os.path.exists(path) else {}
    src[name] = {"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "urls": urls,
                 "sha256": hashlib.sha256(open(os.path.join(os.path.dirname(OUT), name), "rb").read()).hexdigest()}
    with open(path, "w") as f:
        json.dump(src, f, indent=1, sort_keys=True)
        f.write("\n")


def protocol():
    """Snapshot of the protocol parameters the thesis cites, from the live protocol config."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "EXPERIMENTAL_protocol_config",
                       "params": {"finality": "final"}}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, UA), timeout=30))["result"]
    keep = {k: r[k] for k in ("protocol_version", "epoch_length", "max_inflation_rate", "protocol_reward_rate",
                              "num_blocks_per_year", "min_gas_price", "gas_limit")}
    keep["burnt_gas_reward"] = r["runtime_config"]["transaction_costs"]["burnt_gas_reward"]
    with open(os.path.join(os.path.dirname(OUT), "protocol.json"), "w") as f:
        json.dump(keep, f, indent=1, sort_keys=True)
        f.write("\n")
    stamp("protocol.json", [RPC + " EXPERIMENTAL_protocol_config"])
    print("wrote protocol.json", keep)


def inflows(pages=12):
    """Recent receipts into the buyback account, from the NearBlocks indexer (third party, no key):
    who sent the NEAR. Each row carries a transaction hash that can be checked on any RPC."""
    out, cursor = {}, None
    for _ in range(pages):
        url = f"https://api.nearblocks.io/v1/account/{BUYBACK}/receipts?per_page=250&order=desc"
        if cursor:
            url += f"&cursor={cursor}"
        for attempt in range(20):
            try:
                page = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(20)
            except OSError:
                time.sleep(20)
        else:
            break
        for r in page["txns"]:
            dep = sum(int(a.get("deposit") or 0) for a in r.get("actions") or [] if a.get("action") == "TRANSFER")
            if r["receiver_account_id"] == BUYBACK and dep and r["receipt_outcome"]["status"]:
                out[r["receipt_id"]] = [r["receipt_block"]["block_height"], r["transaction_hash"],
                                        r["predecessor_account_id"], round(dep / 1e24, 6)]
        cursor = page.get("cursor")
        if not cursor or len(page["txns"]) < 250:
            break
    with open(os.path.join(os.path.dirname(OUT), "inflows.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["block_height", "transaction_hash", "predecessor", "near"])
        w.writerows(sorted(out.values()))
    stamp("inflows.csv", [f"https://api.nearblocks.io/v1/account/{BUYBACK}/receipts?per_page=250&order=desc&page=N"])
    print(f"wrote inflows.csv ({len(out)} transfers)")


def buybacks():
    """Balance of the buyback account at every cached epoch end. Newest first; resumable."""
    rows = list(csv.DictReader(open(OUT)))
    # every epoch end, plus the block before the oldest epoch so its gain can be computed too
    ends = sorted({int(r["end_height"]) for r in rows} | {min(int(r["prev_end_height"]) for r in rows)}, reverse=True)
    have = {}
    if os.path.exists(BOUT):
        have = {int(r["end_height"]): int(r["balance"]) for r in csv.DictReader(open(BOUT))}

    def write():
        with open(BOUT + ".tmp", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["end_height", "balance"])
            w.writerows(sorted(have.items()))
        os.replace(BOUT + ".tmp", BOUT)

    gone = False  # once the account does not exist, every older height is zero too
    for i, h in enumerate(ends):
        if h in have:
            continue
        b = None if gone else balance(h)
        gone = b is None
        have[h] = b or 0
        if i % 20 == 0:
            write()
            print(f"buybacks {i + 1}/{len(ends)}", flush=True)
    write()
    print(f"wrote {len(have)} balances to {BOUT}")


def offchain():
    """Daily NEAR price and DefiLlama series. Only complete UTC days are kept."""
    get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
    day = lambda ts: time.strftime("%Y-%m-%d", time.gmtime(ts))
    today = day(time.time())
    prices = get("https://api.coingecko.com/api/v3/coins/near/market_chart?vs_currency=usd&days=365&interval=daily")
    with open(os.path.join(os.path.dirname(OUT), "price.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "usd"])
        w.writerows((day(t / 1000), p) for t, p in prices["prices"] if day(t / 1000) < today)
    cols = {k: {day(t): v for t, v in get(u)["totalDataChart"]} for k, u in LLAMA.items()}
    dates = sorted(d for d in set().union(*cols.values()) if "2025-11-01" <= d < today)
    with open(os.path.join(os.path.dirname(OUT), "llama.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date"] + list(LLAMA))
        w.writerows([d] + [cols[k].get(d, "") for k in LLAMA] for d in dates)
    stamp("price.csv", ["https://api.coingecko.com/api/v3/coins/near/market_chart?vs_currency=usd&days=365&interval=daily"])
    stamp("llama.csv", list(LLAMA.values()))
    print(f"wrote price.csv and llama.csv ({len(dates)} days)")


def save(rows):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: int(r["start_height"])))
    os.replace(OUT + ".tmp", OUT)


def main():
    n = int(sys.argv[sys.argv.index("--epochs") + 1]) if "--epochs" in sys.argv else 1300
    rows = {}
    if os.path.exists(OUT):
        rows = {int(r["end_height"]): r for r in csv.DictReader(open(OUT))}
    final = json.load(urllib.request.urlopen(urllib.request.Request(
        RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": "block",
                         "params": {"finality": "final"}}).encode(), UA), timeout=30))["result"]
    end = block(final["header"]["next_epoch_id"])  # last block of the newest complete epoch
    end_h = end["header"]["height"]
    for i in range(n):
        if end_h in rows:  # cached: jump back without touching the chain
            end, end_h = None, int(rows[end_h]["prev_end_height"])
            continue
        row, end = fetch_epoch(end or block(end_h))
        rows[end_h] = row
        end_h = end["header"]["height"]
        if i % 10 == 0:
            save(rows)
            print(f"{i + 1}/{n} epochs, at height {end_h}", flush=True)
    save(rows)
    print(f"wrote {len(rows)} epochs to {OUT}")
    buybacks()


if __name__ == "__main__":
    {"buybacks": buybacks, "offchain": offchain, "wallets": wallets, "inflows": inflows, "protocol": protocol}.get(sys.argv[1] if len(sys.argv) > 1 else "", main)()
