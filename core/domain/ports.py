from abc import ABC, abstractmethod
from typing import List
from .models import Product

class ProductRepositoryPort(ABC):
    @abstractmethod
    def get_all_products(self) -> List[Product]:
        """Recupera a lista global de produtos raw do banco de dados (Adapter)"""
        pass

class OfferStoragePort(ABC):
    @abstractmethod
    def save_cheapest_offers(self, offers: dict) -> None:
        """Salva a lista comparativa final no sistema de armazenamento (SQLite, JSON, etc)"""
        pass

class OfferQueryPort(ABC):
    @abstractmethod
    def get_price_history(self, variant_name: str) -> List[dict]:
        """Extrai a linha do tempo temporal do preço de uma variante para Analytics."""
        pass
        
    @abstractmethod
    def get_all_variants(self) -> List[str]:
        """Extrai o nome de todas as variantes únicas mapeadas no histórico."""
        pass
