import json
with open('data/market_prices.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    commodities = sorted(list(set(item['commodity'] for item in data['data'])))
    print(json.dumps(commodities))
