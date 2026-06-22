"""
Mythic Index MCP Server — Marketplace Edition
===============================================
MTG card search, pricing, deck analysis, and investment intelligence.
19 tools + 1 resource. Connects to api.mythic-index.com.

Setup: pip install mcp httpx
Usage: python3 mcp_server.py (stdio) or python3 mcp_server.py --sse --port 8080
"""
import os, re, json, httpx
from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("MYTHIC_INDEX_API_URL", "https://api.mythic-index.com")
API_KEY = os.environ.get("MYTHIC_INDEX_API_KEY", "mi_ze5qEbb5NRrJqbFfe3pojSp-0kcpJo5zvL9T8KTQs3IS2gYUMQdZtfGtKos7s7T3")

mcp = FastMCP("Mythic Index", instructions="MTG card prices, deck analysis, and investment intelligence. 19 tools, 99K cards, 5 vendors.")

def _client(): return httpx.Client(base_url=API_URL, headers={"X-API-Key": API_KEY}, timeout=30.0)
def _get(path, params=None):
    with _client() as c: r = c.get(path, params=params); r.raise_for_status(); return r.json()
def _post(path, body):
    with _client() as c: r = c.post(path, json=body); r.raise_for_status(); return r.json()

def _parse_decklist(text):
    cards = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//') or line.lower() in ('sideboard','mainboard','companion','commander','lands','creatures','spells'): continue
        m = re.match(r'^(\d+)\s*x?\s+(.+)$', line)
        if m: cards.append({"name": m.group(2).strip(), "quantity": int(m.group(1))}); continue
        m = re.match(r'^(.+?)\s*x(\d+)$', line)
        if m: cards.append({"name": m.group(1).strip(), "quantity": int(m.group(2))}); continue
        cards.append({"name": line, "quantity": 1})
    return cards

# ═══ SEARCH & DISCOVERY ═══

@mcp.tool()
def search_cards(query: str, limit: int = 10) -> str:
    """Search MTG cards by name with fuzzy matching. Handles typos and partial names.
    Args: query: Card name (min 2 chars). limit: Max results (1-50)."""
    data = _get("/api/cards/search", {"q": query, "limit": min(limit, 50)})
    cards = data.get("cards", [])
    if not cards: return f"No cards found for '{query}'"
    lines = [f"Found {data['count']} cards for '{query}':\n"]
    for c in cards: lines.append(f"- **{c['name']}** [{c['set_code'].upper()}] ({c['rarity']}) {c.get('mana_cost','')} — {c.get('type_line','')} [id:{c['card_id']}]")
    return "\n".join(lines)

@mcp.tool()
def find_cards(oracle_text:str="", type_line:str="", colors:str="", color_identity:str="", cmc_min:int=0, cmc_max:int=20, rarity:str="", keyword:str="", reserved_list:bool=False, price_min:float=0, price_max:float=0, format:str="", sort:str="price", limit:int=10) -> str:
    """Find MTG cards by ability text, type, color, CMC, price, format. For deck building queries like 'black creatures with deathtouch under $5'.
    Args: oracle_text: Rules text search. type_line: Card type filter. colors: Comma-separated W,U,B,R,G. color_identity: Exact identity for Commander. cmc_min/cmc_max: Mana value range. rarity: common/uncommon/rare/mythic. keyword: Ability keyword. reserved_list: Only RL cards. price_min/price_max: USD range. format: Legality filter. sort: price/name/recent. limit: 1-50."""
    p = {"sort": sort, "order": "desc", "limit": min(limit, 50)}
    if oracle_text: p["oracle_text"] = oracle_text
    if type_line: p["type_line"] = type_line
    if colors: p["colors"] = colors
    if color_identity: p["color_identity"] = color_identity
    if cmc_min > 0: p["cmc_min"] = cmc_min
    if cmc_max < 20: p["cmc_max"] = cmc_max
    if rarity: p["rarity"] = rarity
    if keyword: p["keyword"] = keyword
    if reserved_list: p["reserved_list"] = "true"
    if price_min > 0: p["price_min"] = price_min
    if price_max > 0: p["price_max"] = price_max
    if format: p["format"] = format
    data = _get("/api/cards/browse", p)
    cards = data.get("cards", [])
    if not cards: return "No cards found with those filters."
    lines = [f"Found {data.get('total',0):,} cards:\n"]
    for i, c in enumerate(cards, 1):
        price = f"${c['best_price']:.2f}" if c.get('best_price') else "—"
        lines.append(f"{i}. **{c['name']}** [{c['set_code'].upper()}] ({c['rarity']}) {c.get('mana_cost','')} — {price}")
    return "\n".join(lines)

@mcp.tool()
def browse_cards(sort:str="price", order:str="desc", rarity:str="", set_code:str="", limit:int=10) -> str:
    """Browse MTG cards by price, name, or newest. Args: sort: price/name/recent. order: desc/asc. rarity/set_code: filters. limit: 1-50."""
    p = {"sort": sort, "order": order, "limit": min(limit, 50)}
    if rarity: p["rarity"] = rarity
    if set_code: p["set_code"] = set_code
    data = _get("/api/cards/browse", p)
    cards = data.get("cards", [])
    if not cards: return "No cards found."
    lines = [f"{len(cards)} of {data.get('total',0):,} cards:\n"]
    for i, c in enumerate(cards, 1):
        price = f"${c['best_price']:.2f}" if c.get('best_price') else "—"
        lines.append(f"{i}. **{c['name']}** [{c['set_code'].upper()}] ({c['rarity']}) — {price} [id:{c['card_id']}]")
    return "\n".join(lines)

@mcp.tool()
def list_sets(search: str = "") -> str:
    """List MTG sets. Args: search: Optional name/code filter."""
    data = _get("/api/sets", {"search": search} if search else {})
    sets = data.get("sets", [])
    if not sets: return "No sets found."
    main = [s for s in sets if s.get("set_type") in {"expansion","core","masters","draft_innovation","commander"}][:25]
    display = main if main and not search else sets[:25]
    lines = [f"{data['count']} sets:\n"]
    for s in display: lines.append(f"- **{s['name']}** [{s['code'].upper()}] ({s.get('set_type','')}) — {s.get('card_count') or s.get('total_cards',0)} cards")
    return "\n".join(lines)

# ═══ PRICING ═══

@mcp.tool()
def get_card_price(card_id: int) -> str:
    """Current prices across all vendors. Args: card_id: From search results."""
    data = _get(f"/api/cards/{card_id}")
    card, pr = data["card"], data.get("printings", {})
    lines = [f"**{card['name']}** — {card.get('type_line','')}", f"Set: {card['set_name']} | Rarity: {card['rarity']}", ""]
    for finish, sources in pr.items():
        lines.append(f"**{finish.upper()}**")
        best = None
        for slug, info in sources.items():
            r = info.get("retail")
            if r:
                lines.append(f"  {info['source']}: ${r:.2f}" + (f" (buylist: ${info['buylist']:.2f})" if info.get('buylist') else ""))
                if best is None or r < best: best = r
        if best: lines.append(f"  → Best: **${best:.2f}**")
    return "\n".join(lines)

@mcp.tool()
def get_price_history(card_id:int, days:int=30, finish:str="nonfoil") -> str:
    """Price trends over time. Args: card_id: Card ID. days: 7/30/90/365. finish: nonfoil/foil."""
    data = _get(f"/api/cards/{card_id}/prices", {"days": days, "finish": finish, "condition": "retail"})
    fd = data.get("prices", {}).get(finish, {})
    if not fd and data.get("prices"): fd = list(data["prices"].values())[0]
    if not fd: return "No price history."
    lines = [f"**{data.get('card_name','')}** — {days}D {finish}:\n"]
    for slug, info in fd.items():
        pts = info.get("data", [])
        if not pts: continue
        lo, hi, last = min(p["price"] for p in pts), max(p["price"] for p in pts), pts[-1]["price"]
        d = ((last - pts[0]["price"]) / pts[0]["price"] * 100) if pts[0]["price"] else 0
        lines.append(f"**{info.get('source',slug)}**: ${last:.2f} | Low ${lo:.2f} | High ${hi:.2f} | {'+' if d>0 else ''}{d:.1f}%")
    return "\n".join(lines)

# ═══ SETS & SEALED ═══

@mcp.tool()
def get_set_stats(set_code: str) -> str:
    """Set statistics: cards, rarity, prices, top cards. Args: set_code: e.g. 'mh3'."""
    d = _get(f"/api/sets/{set_code}/stats")
    ps = d["price_stats"]
    lines = [f"**{d['set_name']}** ({d['set_code'].upper()}) — {d['set_type']}", f"Cards: {d['total_cards']} | Priced: {ps['priced_cards']} | Avg: ${ps['avg_price']:.2f} | Total: ${ps['total_value']:,.0f}"]
    chase = d.get("chase_card")
    if chase: lines.append(f"Chase: **{chase['name']}** ${chase['price']:.2f}")
    top = d.get("top_cards", [])[:5]
    if top:
        lines.append("\nTop cards:")
        for i, c in enumerate(top, 1): lines.append(f"  {i}. {c['name']} — ${c['best_price']:.2f}")
    return "\n".join(lines)

@mcp.tool()
def search_sealed(set_code:str="", category:str="") -> str:
    """Find sealed products. Args: set_code: Filter by set. category: booster_box/booster_pack/bundle."""
    if set_code:
        data = _get(f"/api/sealed/set/{set_code}")
        prods = data.get("products", [])
        if category: prods = [p for p in prods if p.get("category") == category]
        if not prods: return f"No sealed products for '{set_code}'"
        lines = [f"Sealed for {set_code.upper()} ({len(prods)}):\n"]
        for p in prods:
            price = f"${p['box_market_price']:.2f}" if p.get("box_market_price") else "—"
            lines.append(f"- **{p['name']}** ({p.get('category','')}) — {price} [id:{p['id']}]")
        return "\n".join(lines)
    data = _get("/api/sealed")
    lines = [f"{len(data.get('sets',[]))} sets with sealed products:\n"]
    for s in data.get("sets", [])[:15]: lines.append(f"**{s['set_name']}** — {len(s['products'])} products")
    return "\n".join(lines)

@mcp.tool()
def get_sealed_ev(product_id: int) -> str:
    """EV breakdown for sealed product. Args: product_id: From search_sealed."""
    d = _get(f"/api/sealed/{product_id}/ev")
    pr, ev = d["product"], d["ev"]
    if d.get("warnings"): return f"**{pr['name']}**\n⚠️ {'; '.join(d['warnings'])}"
    mkt, gross, roi = ev.get("box_market_price",0) or 0, ev.get("gross_ev",0) or 0, ev.get("roi_pct",0) or 0
    lines = [f"**{pr['name']}** ({pr['set_name']})", f"Market: ${mkt:.2f} | EV: ${gross:.2f} | ROI: {'+' if roi>0 else ''}{roi:.1f}%", f"{'Underpriced ✓' if roi > 0 else 'Overpriced ✗'}"]
    for finish, fd in ev.get("by_finish", {}).items():
        tiers = fd.get("tiers", {})
        if tiers:
            lines.append(f"\n**{finish}** (${fd.get('ev_per_pack',0):.2f}/pack):")
            for tn in ["jackpot","premium","meaningful","playable","bulk"]:
                t = tiers.get(tn)
                if t: lines.append(f"  {tn}: {t['cards']} cards, {t['pull_pct']:.1f}%, EV ${t.get('ev_contribution_per_pack',0):.2f}")
    return "\n".join(lines)

# ═══ INVESTMENT ═══

@mcp.tool()
def top_movers(days:int=7, direction:str="up", limit:int=10, min_price:float=1.0) -> str:
    """Biggest price gains/drops. Args: days: 1-90. direction: up/down. min_price: Filter noise."""
    data = _get("/api/cards/movers", {"days": days, "direction": direction, "limit": min(limit,50), "min_price": min_price})
    movers = data.get("movers", [])
    if not movers: return f"No movers ({direction}, {days}D)"
    lines = [f"{'📈' if direction=='up' else '📉'} {direction.title()} movers ({days}D):\n"]
    for i, m in enumerate(movers, 1): lines.append(f"{i}. **{m['name']}** [{m['set_code'].upper()}] ${m['previous_price']:.2f}→${m['current_price']:.2f} ({'+' if m['change_pct']>0 else ''}{m['change_pct']:.1f}%)")
    return "\n".join(lines)

@mcp.tool()
def find_arbitrage(min_spread:float=1.0, limit:int=10) -> str:
    """Cross-vendor profit opportunities. Args: min_spread: Min profit USD. limit: 1-50."""
    data = _get("/api/cards/arbitrage", {"min_spread": min_spread, "limit": min(limit,50)})
    opps = data.get("opportunities", [])
    if not opps: return f"No arbitrage > ${min_spread:.2f}"
    lines = ["💰 Arbitrage:\n"]
    for i, o in enumerate(opps, 1): lines.append(f"{i}. **{o['name']}** — Buy {o['buy_from']} ${o['buy_price']:.2f} → Sell {o['sell_to']} ${o['sell_price']:.2f} = **${o['spread']:.2f}** ({o['margin_pct']:.1f}%)")
    return "\n".join(lines)

@mcp.tool()
def reserved_list_tracker(max_price:float=0, sort:str="price", limit:int=20) -> str:
    """Reserved List cards — never reprinted. Args: max_price: Budget cap. sort: price/name. limit: 1-50."""
    p = {"reserved_list": "true", "sort": sort, "order": "desc" if sort=="price" else "asc", "limit": min(limit,50)}
    if max_price > 0: p["price_max"] = max_price
    data = _get("/api/cards/browse", p)
    cards = data.get("cards", [])
    if not cards: return "No RL cards found."
    lines = [f"📜 Reserved List ({data.get('total',0):,} total):\n"]
    for i, c in enumerate(cards, 1): lines.append(f"{i}. **{c['name']}** [{c['set_code'].upper()}] — {'$'+str(round(c['best_price'],2)) if c.get('best_price') else '—'}")
    return "\n".join(lines)

# ═══ DECK ANALYSIS ═══

@mcp.tool()
def price_deck(decklist:str, format:str="") -> str:
    """Price a decklist with curve, colors, legality, budget swaps. Args: decklist: '4 Lightning Bolt' per line. format: standard/modern/commander."""
    cards = _parse_decklist(decklist)
    if not cards: return "Could not parse. Use: '4 Lightning Bolt'"
    body = {"cards": cards}
    if format: body["format"] = format
    d = _post("/api/decks/analyze", body)
    t = d['total_cost']['cheapest_per_card']
    lines = [f"**Deck** — {d['total_cards']} cards\n💰 **${t:.2f}**"]
    v = d['total_cost'].get('by_vendor', {})
    if v:
        lines.append("\nBy vendor:")
        for vn, p in v.items(): lines.append(f"  {vn}: ${p:.2f}{' ←' if p==min(v.values()) else ''}")
    if d.get('missing'): lines.append(f"\n⚠️ Not found: {', '.join(d['missing'])}")
    leg = d.get('legality')
    if leg:
        if leg['legal']: lines.append(f"\n✅ {leg['format'].title()} legal")
        else:
            lines.append(f"\n❌ Not {leg['format'].title()} legal:")
            for issue in leg['issues'][:5]: lines.append(f"  • {issue['name']}: {issue['status']}")
    curve = d.get('mana_curve', {})
    bm = max(curve.values()) if curve.values() else 1
    lines.append("\n📊 Curve:")
    for cmc in ['0','1','2','3','4','5','6+']: lines.append(f"  {cmc}: {'█'*max(1,round(curve.get(cmc,0)/bm*12)) if curve.get(cmc,0)>0 else ''} {curve.get(cmc,0)}")
    exp = d.get('most_expensive', [])[:3]
    if exp:
        lines.append("\n💎 Expensive:")
        for c in exp: lines.append(f"  {c['quantity']}x {c['name']} ${c['unit_price']:.2f} ({c['pct_of_deck']:.0f}%)")
    alts = d.get('budget_alternatives', [])[:3]
    if alts:
        lines.append("\n💡 Swaps:")
        for a in alts: lines.append(f"  {a['original']} → **{a['alternative']}** (saves ${a['savings_per_copy']:.2f})")
    return "\n".join(lines)

@mcp.tool()
def suggest_budget_alternatives(card_name:str, max_price:float=0, format:str="") -> str:
    """Cheaper alternatives with similar type/CMC. Args: card_name: Card to replace. max_price: Cap. format: Legality filter."""
    s = _get("/api/cards/search", {"q": card_name, "limit": 1})
    if not s.get("cards"): return f"Not found: {card_name}"
    card = s["cards"][0]; det = _get(f"/api/cards/{card['card_id']}"); cd = det["card"]
    best = None
    for f, src in det.get("printings",{}).items():
        for sl, info in src.items():
            if info.get("retail") and (best is None or info["retail"] < best): best = info["retail"]
    if not best: return f"No price for {cd['name']}"
    cap = max_price if max_price > 0 else best * 0.5
    tk = next((t for t in ["creature","instant","sorcery","enchantment","artifact","planeswalker"] if t in (cd.get("type_line","")).lower()), "")
    if not tk: return f"Can't find alternatives for {cd.get('type_line','')}"
    cmc = cd.get("cmc",0) or 0
    p = {"type_line":tk,"cmc_min":max(0,cmc-1),"cmc_max":cmc+1,"price_max":cap,"price_min":0.10,"sort":"price","order":"desc","limit":8}
    if format: p["format"] = format
    alts = [c for c in _get("/api/cards/browse", p).get("cards",[]) if c["name"] != cd["name"]]
    lines = [f"**{cd['name']}** ${best:.2f} → alternatives under ${cap:.2f}:\n"]
    for i, c in enumerate(alts, 1): lines.append(f"{i}. **{c['name']}** {c.get('mana_cost','')} — ${'%.2f'%c['best_price'] if c.get('best_price') else '—'} (saves ${best-(c.get('best_price') or 0):.2f})")
    return "\n".join(lines) if alts else lines[0] + "\nNo alternatives found."

@mcp.tool()
def analyze_mana_curve(decklist: str) -> str:
    """Analyze mana curve, lands, color sources. Args: decklist: Same format as price_deck."""
    cards = _parse_decklist(decklist)
    if not cards: return "Could not parse."
    d = _post("/api/decks/analyze", {"cards": cards})
    curve, types, colors = d.get('mana_curve',{}), d.get('type_distribution',{}), d.get('color_distribution',{})
    total, lands = d['total_cards'], types.get('land',0)
    nonland = total - lands
    tm = sum((6 if k=='6+' else int(k))*v for k,v in curve.items())
    avg = tm/nonland if nonland>0 else 0
    bm = max(curve.values()) if curve.values() else 1
    lines = [f"**Curve** — {total} cards, avg CMC {avg:.2f}\n"]
    for cmc in ['0','1','2','3','4','5','6+']: lines.append(f"  {cmc}: {'█'*max(1,round(curve.get(cmc,0)/bm*15)) if curve.get(cmc,0)>0 else ''} {curve.get(cmc,0)}")
    if total == 60:
        ideal = 20 if avg < 2.5 else (22 if avg < 3.0 else 24)
        lines.append(f"\n{'✅' if abs(lands-ideal)<=2 else '⚠️'} Lands: {lands} (rec ~{ideal})")
    elif total == 100:
        ideal = 36 if avg < 3.0 else 38
        lines.append(f"\n{'✅' if abs(lands-ideal)<=2 else '⚠️'} Lands: {lands} (rec ~{ideal})")
    cn = {'W':'White','U':'Blue','B':'Black','R':'Red','G':'Green'}
    active = [(c,n) for c,n in colors.items() if c!='colorless' and n>0]
    if active:
        lines.append("\n🎨 Sources:")
        for c,n in sorted(active, key=lambda x:x[1], reverse=True): lines.append(f"  {cn.get(c,c)}: {n} cards → ~{max(1,round(lands*n/nonland))} sources")
    return "\n".join(lines)

# ═══ STRATEGY ═══

@mcp.tool()
def check_legality(card_id: int) -> str:
    """Format legality check. Args: card_id: From search results."""
    d = _get(f"/api/cards/{card_id}/legality")
    leg = d.get("legalities", {})
    lines = [f"**{d['card_name']}**:\n"]
    legal = [f for f,s in leg.items() if s=="legal"]
    banned = [f for f,s in leg.items() if s=="banned"]
    restricted = [f for f,s in leg.items() if s=="restricted"]
    if legal: lines.append(f"✅ Legal: {', '.join(legal)}")
    if restricted: lines.append(f"⚠️ Restricted: {', '.join(restricted)}")
    if banned: lines.append(f"❌ Banned: {', '.join(banned)}")
    return "\n".join(lines)

@mcp.tool()
def evaluate_card(card_id: int) -> str:
    """Strategic analysis: roles, keywords, archetypes. Args: card_id: From search."""
    d = _get(f"/api/cards/{card_id}/strategy")
    lines = [f"**{d['name']}** — {d.get('type_line','')}", f"{d.get('mana_cost','')} (CMC {d.get('cmc',0)}) | {d.get('rarity','')}"]
    if d.get('oracle_text'): lines.append(f"\n*{d['oracle_text']}*")
    for r in d.get('roles',[]): lines.append(f"  • {r['role'].replace('_',' ').title()} — {r['description']}")
    if d.get('keywords'): lines.append(f"Keywords: {', '.join(d['keywords'])}")
    if d.get('archetypes'): lines.append(f"Archetypes: {', '.join(d['archetypes'])}")
    if d.get('legal_formats'): lines.append(f"Legal: {', '.join(d['legal_formats'])}")
    return "\n".join(lines)

@mcp.tool()
def find_cards_by_role(role:str, colors:str="", format:str="", max_price:float=0, limit:int=10) -> str:
    """Find cards by role: removal, card_draw, ramp, counter, protection, evasion, token_generation, lifegain, discard, tutor, graveyard, board_wipe, burn.
    Args: role: Strategic role. colors: W,U,B,R,G. format: modern/commander. max_price: Budget. limit: 1-30."""
    patterns = {"removal":"destroy target","card_draw":"draw a card","ramp":"add {","counter":"counter target","protection":"hexproof","evasion":"flying","token_generation":"create a","lifegain":"gain life","discard":"discard a card","tutor":"search your library","graveyard":"from your graveyard","board_wipe":"destroy all","burn":"damage to any target"}
    pattern = patterns.get(role.lower())
    if not pattern: return f"Unknown role. Available: {', '.join(patterns.keys())}"
    p = {"oracle_text": pattern, "sort": "price", "order": "desc", "limit": min(limit,30)}
    if colors: p["colors"] = colors
    if format: p["format"] = format
    if max_price > 0: p["price_max"] = max_price
    data = _get("/api/cards/browse", p)
    cards = data.get("cards", [])
    if not cards: return f"No {role} cards found."
    lines = [f"**{role.replace('_',' ').title()}** ({data.get('total',0):,}):\n"]
    for i, c in enumerate(cards, 1): lines.append(f"{i}. **{c['name']}** [{c['set_code'].upper()}] {c.get('mana_cost','')} — {'$'+str(round(c['best_price'],2)) if c.get('best_price') else '—'}")
    return "\n".join(lines)

# ═══ SYSTEM ═══

@mcp.tool()
def get_api_status() -> str:
    """Platform health and sync status."""
    d = _get("/api/status")
    data = d["data"]
    lines = [f"Cards: {data.get('total_cards',0):,} | Listings: {data.get('total_listings',0):,} | Latest: {data.get('latest_price_date','—')}"]
    for n, s in d.get("syncs",{}).items(): lines.append(f"  {'✅' if s['status']=='success' else '❌'} {n}")
    return "\n".join(lines)

@mcp.resource("mythic://api-guide")
def api_guide() -> str:
    """API reference."""
    return "Mythic Index API: 21 endpoints, 5 vendors, 99K cards. https://api.mythic-index.com"

def main():
    import sys
    if not API_KEY or API_KEY == "PUBLIC_READ_KEY_PLACEHOLDER":
        print("Set MYTHIC_INDEX_API_KEY or replace placeholder in mcp_server.py", file=sys.stderr); sys.exit(1)
    if "--sse" in sys.argv:
        port = 8080
        for i, a in enumerate(sys.argv):
            if a == "--port" and i+1 < len(sys.argv): port = int(sys.argv[i+1])
        mcp.run(transport="sse", port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()