"""The investor verdict, in one place: README, THESIS, the dashboard and the 60-second page all print this.

Written from out/results.json, so the numbers in it move with the data. The stance is ours; the thresholds
for changing it are stated with it.
"""


def items(results):
    """[(label, sentence)], plain text with **bold** marks; [] when buyback data is missing."""
    s, sc = results["summary"], results.get("scenarios")
    if s.get("payback") is None or not sc:
        return []
    c, cap = sc["cases"], sc["levers"]["capture"]
    full = cap[-1]
    base = c["base"]["year"]
    return [
        ("Today", f"**Not yet a supply story.** NEAR still mints about {s['multiple']:.0f}× what it wins back, and at the median growth rate in the data "
                  f"break-even is {'in ' + str(base) if base else 'more than a century away'}. Don't own NEAR expecting buybacks to offset dilution soon."),
        ("The bet", f"**Governance, not growth.** Sending every Intents fee to the buyback (today about {100 * s['capture_share']:.0f}%) and HSP-029's lower "
                    f"issuance would bring even the base case to {'about ' + format(full['years_base_hsp029'], '.0f') + ' years' if full.get('years_base_hsp029') is not None else 'not even within a century'}. Both are votes, not market conditions."),
        ("Turn more bullish if", "HSP-029 is ratified (its veto window runs to 16 Nov 2026, 16:48 UTC) and validators adopt it after the 90-day grace period, or the buyback's share of Intents fees "
                                 "rises toward 50%."),
        ("Turn bearish if", f"the buyback balance keeps falling, payback over 100 epochs drops below {50 * s['payback']:.0f}%, or transfers "
                            "stop coming from intents.near."),
    ]


def markdown(results):
    return "\n".join(f"- **{k}:** {v}" for k, v in items(results))


def html(results, esc):
    import re
    b = lambda t: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(t))
    return "".join(f"<li><span class='k'>{esc(k)}</span><span class='v'>{b(v)}</span></li>" for k, v in items(results))
