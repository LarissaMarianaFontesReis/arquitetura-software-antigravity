from dataclasses import dataclass

@dataclass
class Product:
    title: str
    url: str
    price_text: str
    category: str  # Extraído grosseiramente, a lógica de categoria pode ser processada antes ou aqui
    image_url: str = ""

@dataclass
class PriceVariant:
    base_model: str
    price_value: float
    original_title: str
    url: str
    image_url: str = ""
