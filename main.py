import os
import sys
import json

# Garante que o projeto consegue importar o pacote explicitamente na raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.scrapper_amazon.csv_json_adapter import CsvJsonProductAdapter
from plugins.scrapper_amazon.local_json_adapter import LocalJsonProductAdapter
from core.application.use_cases import FindCheapestVariantsUseCase
from plugins.storage_sqlite.sqlite_adapter import SQLiteStorageAdapter


def run_scraper():
    """Executa o Playwright scraper para coletar novos dados do watchlist.csv."""
    from plugins.scrapper_amazon.playwright_scraper import main as scraper_main
    print("\n>>> Iniciando coleta com Playwright...\n")
    # --show pode ser passado para visualizar o browser durante o scrape
    headless_mode = "--show" not in sys.argv
    scraper_main(headless=headless_mode)


def run_pipeline():
    """
    Carrega os dados coletados e executa o pipeline de comparação de preços.
    Tenta primeiro o amazon_scraped.json (Playwright), depois o legado.
    """
    scraped_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amazon_scraped.json")
    legacy_json  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amazon_classified.json")

    if os.path.exists(scraped_json):
        print(f"[Pipeline] Usando dados do Playwright: {scraped_json}")
        repo_adapter = CsvJsonProductAdapter(filepath=scraped_json)
    elif os.path.exists(legacy_json):
        print(f"[Pipeline] amazon_scraped.json não encontrado. Usando legado: {legacy_json}")
        repo_adapter = LocalJsonProductAdapter(filepath=legacy_json)
    else:
        print("[Erro] Nenhum arquivo de dados encontrado. Rode: python main.py --scrape")
        return

    storage_adapter  = SQLiteStorageAdapter()
    compare_use_case = FindCheapestVariantsUseCase(repository=repo_adapter)

    cheapest_variants = compare_use_case.execute()

    try:
        storage_adapter.save_cheapest_offers(cheapest_variants)
        print(f"\n[OK] Snapshot de precos salvo com sucesso na base de dados!")
    except Exception as e:
        print(f"[Aviso] Erro no banco ao salvar historico: {e}")

    print("\n=======================================================")
    print("   COMPARADOR - OFERTAS MAIS BARATAS ATIVAS")
    print("=======================================================\n")

    for variant, dto in sorted(cheapest_variants.items()):
        formatted_price = f"{dto.price_value:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        print(f"  {variant.upper()}")
        print(f"  Melhor Preco: R$ {formatted_price}")
        print(f"  Anuncio: {dto.original_title[:70]}...")
        print(f"  Link: {dto.url}")
        print("-" * 55)


def main():
    """
    Entry point principal.

    Flags disponíveis:
      --scrape       Executa o Playwright scraper antes do pipeline
      --show         Abre o browser visível durante o scrape (requer --scrape)
      --scrape-only  Apenas scrapa, sem rodar o pipeline de comparação
    """
    args = sys.argv[1:]

    if "--scrape" in args or "--scrape-only" in args:
        run_scraper()

    if "--scrape-only" not in args:
        run_pipeline()


if __name__ == "__main__":
    main()
