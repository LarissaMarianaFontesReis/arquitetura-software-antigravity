"""
Playwright Amazon Scraper
Plugin de scraping que percorre o watchlist.csv e, para cada produto,
realiza uma busca inteligente na Amazon Brasil retornando o item de menor preço.

Cada resultado recebe um hash SHA-256 derivado do id e search_query do CSV,
garantindo rastreabilidade e prevenção de confusão na comparação histórica.
"""
import asyncio
import csv
import hashlib
import json
import os
import re
import sys
import time
import random
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR   = Path(__file__).resolve().parents[2]
WATCHLIST  = ROOT_DIR / "watchlist.csv"
OUTPUT_JSON = ROOT_DIR / "amazon_scraped.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_hash(csv_id: str, search_query: str) -> str:
    """SHA-256 estável a partir de id + search_query do CSV."""
    raw = f"{csv_id}::{search_query.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_price_value(price_text: str) -> float:
    """Converte 'R$ 4.199,90' → 4199.90"""
    if not price_text:
        return 0.0
    clean = re.sub(r"[^\d,]", "", price_text)
    clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def load_watchlist() -> list[dict]:
    """Lê o watchlist.csv e retorna lista de dicts."""
    if not WATCHLIST.exists():
        print(f"[ERRO] watchlist.csv não encontrado em {WATCHLIST}")
        sys.exit(1)

    products = []
    with open(WATCHLIST, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["max_price"] = float(row.get("max_price", 99999))
            products.append(row)

    print(f"[INFO] {len(products)} produtos carregados do watchlist.csv")
    return products


# ---------------------------------------------------------------------------
# Core Playwright logic
# ---------------------------------------------------------------------------

async def scrape_product(page, product: dict) -> dict | None:
    """
    Busca um produto específico na Amazon, filtra resultados e retorna
    o item com menor preço (excluindo Sponsored e sem preço).
    """
    search_query = product["search_query"]
    max_price    = product["max_price"]
    csv_hash     = compute_hash(product["id"], search_query)

    url = f"https://www.amazon.com.br/s?k={search_query.replace(' ', '+')}&language=pt_BR"
    print(f"\n[SCRAPING] {product['name']}")
    print(f"  → Busca: {search_query}")
    print(f"  → Hash:  {csv_hash[:16]}...")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Aguarda resultados carregarem
        await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)
        # Pausa humana leve para JS terminar
        await asyncio.sleep(random.uniform(1.5, 3.0))

    except Exception as e:
        print(f"  [AVISO] Timeout ou erro ao carregar resultados: {e}")
        return None

    # Extrair todos os resultados via Playwright evaluate
    raw_items = await page.evaluate("""
        () => {
            const results = [];
            const cards = document.querySelectorAll('[data-component-type="s-search-result"]');
            cards.forEach(card => {
                // Pula patrocinados
                const isSponsored = !!card.querySelector(
                    '.puis-sponsored-label-text, .puis-sponsored-label-info-icon, [aria-label="Patrocinado"]'
                );

                const titleEl = card.querySelector('h2 span, [data-cy="title-recipe"] span');
                const title   = titleEl ? titleEl.innerText.trim() : '';

                const priceEl = card.querySelector('span.a-price span.a-offscreen');
                const price   = priceEl ? priceEl.innerText.trim() : '';

                const linkEl  = card.querySelector('h2 a, [data-cy="title-recipe"] a');
                let link      = linkEl ? linkEl.getAttribute('href') : '';
                if (link && !link.startsWith('http')) {
                    link = 'https://www.amazon.com.br' + link;
                }

                const imgEl = card.querySelector('img.s-image');
                const image = imgEl ? imgEl.getAttribute('src') : '';

                const asin  = card.getAttribute('data-asin') || '';

                if (title && price && link) {
                    results.push({ title, price, link, image, asin, isSponsored });
                }
            });
            return results;
        }
    """)

    if not raw_items:
        print(f"  [AVISO] Nenhum resultado extraído para '{product['name']}'.")
        return None

    # Filtragem por relevância usando keywords da search_query
    # Divide a query em tokens e exige que pelo menos 50% apareçam no título
    query_lower = search_query.lower()
    query_tokens = [w for w in query_lower.split() if len(w) > 2]

    def is_relevant(title: str) -> bool:
        t = title.lower()
        if not query_tokens:
            return True
        matches = sum(1 for kw in query_tokens if kw in t)
        return matches >= max(2, round(len(query_tokens) * 0.5))

    # Preço mínimo absoluto vindo do CSV (campo opcional `min_price`)
    # Se não definido, usa max_price / 8 como heurística
    min_price = float(product.get("min_price") or (max_price / 8))

    candidates = []
    for item in raw_items:
        if item.get("isSponsored"):
            continue
        val = parse_price_value(item.get("price", ""))
        if val < min_price:
            continue
        if val > max_price:
            continue
        if not is_relevant(item.get("title", "")):
            continue
        candidates.append({**item, "_price_value": val})

    if not candidates:
        # Relaxa relevância — mantém apenas filtros de preço
        candidates = [
            {**item, "_price_value": parse_price_value(item.get("price", ""))}
            for item in raw_items
            if not item.get("isSponsored")
            and parse_price_value(item.get("price", "")) >= min_price
            and parse_price_value(item.get("price", "")) <= max_price
        ]

    if not candidates:
        print(f"  [AVISO] Nenhum candidato válido. Ajuste min_price/max_price no watchlist.csv.")
        return None


    # Ordena pelo menor preço
    candidates.sort(key=lambda x: x["_price_value"])
    winner = candidates[0]

    print(f"  ✅ Melhor: {winner['title'][:60]}...")
    print(f"     Preço: {winner['price']}  |  ASIN: {winner['asin']}")

    return {
        "csv_hash":     csv_hash,
        "csv_id":       int(product["id"]),
        "csv_name":     product["name"],
        "category":     product["category"],
        "search_query": search_query,
        "title":        winner["title"],
        "price":        winner["price"],
        "url":          winner["link"],
        "image":        winner["image"],
        "asin":         winner["asin"],
        "scraped_at":   datetime.now().isoformat(timespec="seconds"),
    }


async def run_scraper(headless: bool = True) -> list[dict]:
    """Loop principal: percorre o watchlist e scrapa cada produto."""
    from playwright.async_api import async_playwright

    products = load_watchlist()
    results  = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        # Bloqueia rastreadores para performance
        await context.route(
            "**/{ads,analytics,tracking,doubleclick,adservice}**",
            lambda route: route.abort()
        )

        page = await context.new_page()

        # Mascara de automação
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        for product in products:
            result = await scrape_product(page, product)
            if result:
                results.append(result)
            # Pausa entre buscas para não ser banido
            await asyncio.sleep(random.uniform(2.0, 4.5))

        await browser.close()

    return results


def save_results(results: list[dict]) -> None:
    """Salva o JSON de saída com todos os resultados."""
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"\n[OK] {len(results)} produtos salvos em '{OUTPUT_JSON}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(headless: bool = True):
    print("=" * 60)
    print("  AMAZON PLAYWRIGHT SCRAPER - Price Comparator")
    print("=" * 60)

    results = asyncio.run(run_scraper(headless=headless))
    save_results(results)

    print("\nResumo da coleta:")
    for r in results:
        print(f"  [{r['csv_id']:02d}] {r['csv_name']:<35} {r['price']}")


if __name__ == "__main__":
    # Passa headless=False se quiser ver o browser abrir
    headless_mode = "--show" not in sys.argv
    main(headless=headless_mode)
