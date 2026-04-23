import json
from typing import List
from core.domain.ports import ProductRepositoryPort
from core.domain.models import Product

class LocalJsonProductAdapter(ProductRepositoryPort):
    def __init__(self, filepath: str):
        self.filepath = filepath

    def get_all_products(self) -> List[Product]:
        """
        Lê o nosso JSON estruturado gerado pelo processo anterior e injeta no ecossistema
        de Arquitetura Hexagonal. Se amanhã quisermos puxar de um banco PostgreSQL,
        basta criar um 'PostgresProductAdapter' e conectar na Main!
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Erro ao ler adapter local: {e}")
            return []

        products = []
        
        # Nosso amazon_classified formatou o JSON por "Categoria" -> [Itens]
        for category_name, items in data.items():
            for desc in items:
                p = Product(
                    title=desc.get('title', ''),
                    url=desc.get('url', ''),
                    price_text=desc.get('price', ''),
                    category=category_name,
                    image_url=desc.get('image', '')
                )
                products.append(p)
                
        return products
