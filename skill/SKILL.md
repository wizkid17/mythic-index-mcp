# MTG Expert — Mythic Index Skill

## Description
Expert Magic: The Gathering advisor for deck building, competitive strategy, and card investment. Powered by live pricing data from 5 vendors (TCGPlayer, Card Kingdom, CardMarket, CardSphere, CardHoarder) covering 99K+ cards, 971 sets, and 3,900+ sealed products with EV calculations.

## Trigger Patterns
Use this skill when the user asks about:
- MTG card prices, values, or price history ("What's Sheoldred worth?", "How has Force of Negation trended?")
- Deck building or deck help ("Build me a Modern deck", "Help with my Commander deck", "Here's my decklist")
- Card recommendations by ability, color, type, or budget ("Find me black removal under $5")
- Format legality ("Is this legal in Standard?", "What's banned in Modern?")
- Sealed product evaluation ("Is the MH3 box worth buying?", "What's the EV of a collector booster?")
- Card investment or finance ("What cards spiked?", "Reserved List picks", "Arbitrage opportunities")
- Card strategy or evaluation ("What role does this card play?", "Why is this card good?")
- Budget alternatives ("What's a cheaper replacement for X?")
- Mana curve or deck analysis ("Is my curve too high?", "How many lands do I need?")

## MCP Connection
This skill requires the Mythic Index MCP server. See setup instructions in README.md.

### Available Tools (20)
**Search & Discovery:**
- search_cards — fuzzy name search
- find_cards — advanced filters (oracle text, color, type, CMC, price range, format)
- browse_cards — browse by price/name with filters
- list_sets — list/search sets

**Pricing:**
- get_card_price — current prices across 5 vendors
- get_price_history — price trends over time

**Sets & Sealed:**
- get_set_stats — set statistics, rarity distribution, top cards
- search_sealed — find sealed products
- get_sealed_ev — full EV tier breakdown

**Investment:**
- top_movers — biggest price gains/losses
- find_arbitrage — cross-vendor profit opportunities
- reserved_list_tracker — RL investment tracking

**Deck Analysis:**
- price_deck — full decklist pricing + analysis
- suggest_budget_alternatives — cheaper card swaps
- analyze_mana_curve — curve evaluation + land recommendations

**Strategy:**
- check_legality — format legality per card
- evaluate_card — strategic role analysis
- find_cards_by_role — search by strategic role (removal, ramp, burn, etc.)

**System:**
- get_api_status — platform health check