"""
CsvJsonProductAdapter
Adapter que lê o amazon_scraped.json (gerado pelo playwright_scraper.py)
e o injeta no ecossistema de Arquitetura Hexagonal como uma lista de Product.

Cada produto vem com um csv_hash que referencia unicamente a entrada do watchlist.csv,
eliminando ambiguidade na comparação histórica de variantes.
"""
import json
from pathlib import Path
from typing import List

from core.domain.ports import ProductRepositoryPort
from core.domain.models import Product

ROOT_DIR     = Path(__file__).resolve().parents[2]
SCRAPED_JSON = ROOT_DIR / "amazon_scraped.json"


class CsvJsonProductAdapter(ProductRepositoryPort):
    """
    Porta primária que lê o JSON gerado pelo Playwright scraper.
    O campo 'category' já vem do CSV, portanto não há inferência de categoria.
    O campo 'csv_hash' é preservado no título para que o domain service
    possa usar o csv_name como chave de variante (mais preciso que regex).
    """

    def __init__(self, filepath: str | None = None):
        self.filepath = Path(filepath) if filepath else SCRAPED_JSON

    def get_all_products(self) -> List[Product]:
        if not self.filepath.exists():
            print(f"[CsvJsonProductAdapter] Arquivo não encontrado: {self.filepath}")
            print("  Rode primeiro: python main.py --scrape")
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data: list[dict] = json.load(f)
        except Exception as e:
            print(f"[CsvJsonProductAdapter] Erro ao ler JSON: {e}")
            return []

        products = []
        for item in data:
            # Usa csv_name como título principal para o domain service mapear
            # a variante de forma determinística (sem regex frágil)
            title = item.get("csv_name") or item.get("title", "")

            p = Product(
                title=title,
                url=item.get("url", ""),
                price_text=item.get("price", "Sem preço"),
                category=item.get("category", "Outros"),
                image_url=item.get("image", ""),
            )
            products.append(p)

        print(f"[CsvJsonProductAdapter] {len(products)} produtos carregados de {self.filepath.name}")
        return products
