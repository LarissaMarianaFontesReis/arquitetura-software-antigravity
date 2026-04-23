import json

with open("amazon_classified.json", "r", encoding="utf-8") as f:
    classified = json.load(f)

products_local = []
for category, items in classified.items():
    for item in items:
        products_local.append({
            "title": item["title"],
            "url": item["url"],
            "price_current": item["price"],
            "rating": item["rating"],
            "image": item["image"]
        })

# ADD XBOX MOCKS
products_local.extend([
    {
        "title": "Console Xbox One S 500GB Branco",
        "price_current": "R$ 1.500,00",
        "url": "https://amazon.com.br/xbox1",
        "rating": "4.5",
        "image": ""
    },
    {
        "title": "Console Xbox One X 1TB Preto",
        "price_current": "R$ 2.400,00",
        "url": "https://amazon.com.br/xbox2",
        "rating": "4.8",
        "image": ""
    },
    {
        "title": "Controle Xbox Sem Fio Carbon Black",
        "price_current": "R$ 420,00",
        "url": "https://amazon.com.br/xbox3",
        "rating": "4.9",
        "image": ""
    }
])

with open("amazon_products_local.json", "w", encoding="utf-8") as f:
    json.dump(products_local, f, ensure_ascii=False, indent=4)
