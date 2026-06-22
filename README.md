# Mythic Index MCP Server

<!-- mcp-name: io.github.wizkid17/mythic-index-mcp -->

Magic: The Gathering card prices, deck analysis, and investment intelligence — powered by live data from 5 vendors covering 99K+ cards.

Connect this MCP server to Claude Desktop, Claude Code, or any MCP-compatible AI assistant to get real-time MTG card pricing, deck cost analysis, sealed product EV calculations, and investment insights.

## What You Can Do

**Ask about prices:**
> "What's the current price of Sheoldred, the Apocalypse?"

**Build decks on a budget:**
> "Find me black creatures with deathtouch under $5 legal in Modern"

**Price a full decklist:**
> "Price this deck: 4 Lightning Bolt, 4 Goblin Guide, 20 Mountain — check Modern legality"

**Evaluate sealed products:**
> "Is the Modern Horizons 3 Collector Booster Box worth buying at $280?"

**Track investments:**
> "What cards spiked this week? Show me Reserved List cards under $50"

**Understand strategy:**
> "What role does Counterspell play? Find me blue counter spells for Commander under $3"

## Quick Start

### Prerequisites

- Python 3.10+ (the MCP SDK requires 3.10 or newer)
- Claude Desktop, Claude Code, or any MCP-compatible client

### Install

The published package runs with no manual install via [`uv`](https://docs.astral.sh/uv/):

```bash
uvx mythic-index-mcp
```

Or install from source:

```bash
git clone https://github.com/wizkid17/mythic-index-mcp.git
cd mythic-index-mcp
pip install -r requirements.txt
```

### Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mythic-index": {
      "command": "uvx",
      "args": ["mythic-index-mcp"]
    }
  }
}
```

Restart Claude Desktop. The Mythic Index tools will appear in the tools menu (hammer icon).

### Configure Claude Code

```bash
claude mcp add mythic-index uvx mythic-index-mcp
```

### Use Your Own API Key (optional)

The server includes a public read-only key with rate limiting. For higher rate limits, get your own key and set it as an environment variable:

```json
{
  "mcpServers": {
    "mythic-index": {
      "command": "uvx",
      "args": ["mythic-index-mcp"],
      "env": {
        "MYTHIC_INDEX_API_KEY": "mi_your_key_here"
      }
    }
  }
}
```

## Available Tools (19)

### Search & Discovery
| Tool | Description |
|------|-------------|
| `search_cards` | Fuzzy name search — handles typos and partial names |
| `find_cards` | Advanced filters: oracle text, color, type, CMC, price, format, Reserved List |
| `browse_cards` | Browse by price, name, or newest sets |
| `list_sets` | List and search all 971 MTG sets |

### Pricing
| Tool | Description |
|------|-------------|
| `get_card_price` | Current prices across TCGPlayer, Card Kingdom, CardMarket, CardSphere, CardHoarder |
| `get_price_history` | Price trends over 7/30/90/365 days |

### Sets & Sealed Products
| Tool | Description |
|------|-------------|
| `get_set_stats` | Rarity distribution, avg price, total value, chase card, top 10 |
| `search_sealed` | Find booster boxes, packs, bundles, commander decks |
| `get_sealed_ev` | Full EV breakdown with tier analysis (bulk → jackpot) |

### Investment
| Tool | Description |
|------|-------------|
| `top_movers` | Biggest price gains and drops over any period |
| `find_arbitrage` | Cross-vendor profit opportunities (buy retail, sell buylist) |
| `reserved_list_tracker` | Browse Reserved List cards — never reprinted |

### Deck Analysis
| Tool | Description |
|------|-------------|
| `price_deck` | Full decklist pricing: total cost, vendor comparison, mana curve, legality, budget swaps |
| `suggest_budget_alternatives` | Find cheaper cards with similar type and CMC |
| `analyze_mana_curve` | Curve visualization, land count evaluation, color source requirements |

### Strategy
| Tool | Description |
|------|-------------|
| `check_legality` | Format legality: Standard, Modern, Pioneer, Commander, Legacy, Vintage, Pauper |
| `evaluate_card` | Strategic roles, keyword abilities, archetype fit |
| `find_cards_by_role` | Search by role: removal, ramp, card draw, burn, counter, tutor, and 7 more |

### System
| Tool | Description |
|------|-------------|
| `get_api_status` | Platform health and sync status |

## Data Coverage

| Metric | Value |
|--------|-------|
| Cards | 99,000+ |
| Sets | 971 |
| Price sources | TCGPlayer, Card Kingdom, CardMarket, CardSphere, CardHoarder |
| Price listings | 534,000+ |
| Sealed products | 3,900+ with EV calculations |
| Cards with format legality | 99,287 |
| Reserved List cards | 1,096 |
| Update frequency | Daily at 3 AM Lima (UTC-5) |

## Using as a Claude Project

For the best experience, create a Claude Project and add the contents of `skill/system_prompt.md` as the Project Instructions. This gives Claude deep MTG domain knowledge on top of the live data tools.

## Self-Hosting

If you run your own Mythic Index API instance:

```bash
export MYTHIC_INDEX_API_URL=http://localhost:8000
export MYTHIC_INDEX_API_KEY=your-key
python3 mcp_server.py
```

For remote SSE hosting:

```bash
python3 mcp_server.py --sse --port 8080
```

## API

This MCP server connects to the [Mythic Index API](https://api.mythic-index.com). Documentation: [api.mythic-index.com/mtg-api/docs](https://api.mythic-index.com/mtg-api/docs)

## License

MIT — see [LICENSE](LICENSE)

## Links

- **API Docs:** https://api.mythic-index.com/mtg-api/docs
- **Admin Console:** https://api.mythic-index.com/admin
- **MCP Protocol:** https://modelcontextprotocol.io
- **Anthropic:** https://anthropic.com