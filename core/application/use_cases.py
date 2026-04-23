from typing import List, Dict
from core.domain.ports import ProductRepositoryPort, OfferQueryPort
from core.domain.models import PriceVariant
from core.domain.services import ProductDomainService

class FindCheapestVariantsUseCase:
    def __init__(self, repository: ProductRepositoryPort):
        self.repository = repository

    def execute(self) -> Dict[str, PriceVariant]:
        """
        Orquestra:
        1. Puxa todos produtos pelo Adapter
        2. Isola e Normaliza as Variações de todos os componentes de Hardware / Jogos
        3. Exclui imediatamente itens SEM preço (Sem estoque)
        4. Agrupa e encontra o menor valor financeiro de cada Variante e retorna o Vencedor.
        """
        all_products = self.repository.get_all_products()

        groups: Dict[str, List[PriceVariant]] = {}

        for p in all_products:
            # Pula coisas não categorizadas base para manter o output limpo
            if p.category == "Outros":
                continue
                
            price = ProductDomainService.parse_price(p.price_text)
            
            # ATENDIMENTO DE REGRA: Ignorar todos os anúncios que chegaram 'Sem preço'.
            if price <= 0.0:
                continue

            # Busca a qual Modelo Base de Mercado ele pertence (Mapeamento de Acessórios, Consoles, Controles)
            variant_name = ProductDomainService.normalize_product_variant(p.title, p.category)
            
            variant_dto = PriceVariant(
                base_model=variant_name,
                price_value=price,
                original_title=p.title,
                url=p.url,
                image_url=p.image_url
            )
            
            if variant_name not in groups:
                groups[variant_name] = []
            groups[variant_name].append(variant_dto)

        # Regra de Apuração Final: O Menor Preço Ganha
        cheapest_results = {}
        for variant_name, items in groups.items():
            sorted_items = sorted(items, key=lambda x: x.price_value)
            cheapest_results[variant_name] = sorted_items[0]

        return cheapest_results

class GetPriceHistoryUseCase:
    def __init__(self, query_port: OfferQueryPort):
        self.query_port = query_port
        
    def execute(self, variant_name: str) -> dict:
        """
        Recebe o nome da variante, extrai as time-series temporais da porta e 
        modela a matemática de variação (Máximo, Atual, Queda).
        """
        history = self.query_port.get_price_history(variant_name)
        if not history:
            return {"variant": variant_name, "error": "Nenhum histórico rastreado para este item."}
            
        prices = [float(h['price']) for h in history]
        
        return {
            "variant": variant_name,
            "current_price": prices[-1],
            "lowest_historical_price": min(prices),
            "highest_historical_price": max(prices),
            "latest_url": history[-1]['url'], # Link extraído da coleta mais recente
            "latest_image_url": history[-1].get('image_url', ''), # Imagem da extração
            "total_records": len(prices),
            "timeline": history
        }
