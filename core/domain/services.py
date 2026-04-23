import re

# Nomes exatos de variante vindos do watchlist.csv via CsvJsonProductAdapter.
# Quando o título já é um csv_name, o normalize retorna diretamente sem regex.
_CSV_VARIANT_NAMES: set[str] = {
    "PS5 Slim Digital",
    "PS5 Slim Standard (Disco)",
    "PS5 Pro",
    "Xbox Series X 1TB",
    "Xbox Series S 512GB",
    "Controle DualSense PS5 Branco",
    "Controle DualSense Edge PS5",
    "Controle Xbox Sem Fio Carbon Black",
    "Controle Xbox Sem Fio Robot White",
    "Volante Logitech G29 PS5 PC",
    "Volante Logitech G923 PS5 PC",
    "Headset Logitech G435 Sem Fio",
    "Headset Logitech G PRO X 2",
    "PlayStation Portal Remote Player",
    "PlayStation VR2",
}

class ProductDomainService:
    @staticmethod
    def normalize_product_variant(title: str, category: str) -> str:
        """
        Deduze qual é o modelo base (Variação) do produto baseado no título e categoria.

        Prioridade 1: Se o título for um csv_name exato do watchlist.csv, retorna
        diretamente (passthrough) — sem risco de reclassificação errada.

        Prioridade 2: Lógica de regex para produtos do fluxo legado (amazon_classified.json).
        """
        # Passthrough para nomes de variante exatos do CSV
        if title in _CSV_VARIANT_NAMES:
            return title

        t = title.lower()
        
        if category == "Consoles":
            if "xbox" in t:
                if " x " in t or "series x" in t or t.endswith(" x"):
                    return "Console Xbox One X"
                elif " s " in t or "series s" in t or t.endswith(" s"):
                    return "Console Xbox One S"
                else:
                    return "Console Xbox One Base"
            elif "pro" in t:
                return "Console PlayStation 5 PRO"
            elif "slim" in t:
                if "digital" in t or "edição digital" in t or "disk" not in t and "disco" not in t:
                    if "digital" in t or "edição digital" in t:
                        return "Console PlayStation 5 Slim Digital"
                return "Console PlayStation 5 Slim Standard (Disco)"
            elif "digital" in t or "edição digital" in t:
                return "Console PlayStation 5 Base Digital"
            else:
                return "Console PlayStation 5 Standard (Base/Fat)"
                
        elif category == "Controles":
            if "xbox" in t:
                return "Controle Xbox One"
            elif "edge" in t or "pro " in t:
                return "Controle DualSense Edge (Pro)"
            elif "hori" in t or "luta" in t:
                return "Controle Fightpad Hori ALPHA"
            elif "dualsense" in t or "controle" in t:
                return "Controle DualSense Padrão"
            else:
                return "Controle Genérico"

        elif category == "Volantes":
            if "g29" in t:
                return "Volante Logitech G29"
            elif "g923" in t:
                return "Volante Logitech G923"
            elif "direct drive" in t or "g pro" in t or "pro wheel" in t:
                return "Volante Logitech G PRO Direct Drive"
            else:
                return "Volante Genérico"

        elif category == "Headsets & Áudio":
            if "g pro x 2" in t:
                return "Headset Logitech G PRO X 2"
            elif "g435" in t:
                return "Headset Logitech G435"
            else:
                return "Headset/Fones Diversos"

        elif category == "Acessórios & Hardware":
            if "portal" in t:
                return "PlayStation Portal"
            elif "vr2" in t:
                return "PlayStation VR2"
            elif "unidade de disco" in t or "drive" in t.replace("direct drive", ""):
                return "Leitor de Disco Avulso PS5"
            elif "base de carregamento" in t or "carregador" in t:
                return "Base de Carregamento DualSense"
            elif "cabo" in t or "cable" in t:
                return "Cabo HDMI / USB"
            elif "ssd" in t or "firecuda" in t:
                return "SSD Interno M.2"
            elif "suporte" in t:
                return "Suporte Vertical Console"
            else:
                return "Acessório Genérico"
                
        elif category == "Jogos":
            # Jogos não têm variação de hardware, mas podemos agrupar jogos iguais
            if "spider-man" in t:
                return "Jogo: Marvel's Spider-Man 2"
            elif "gran turismo" in t:
                return "Jogo: Gran Turismo 7"
            elif "ghost of" in t:
                return "Jogo: Ghost of Tsushima/Yōtei"
            elif "resident evil" in t:
                return "Jogo: Resident Evil"
            elif "pragmata" in t:
                return "Jogo: Pragmata"
            elif "mega man" in t:
                return "Jogo: Mega Man Collection"
            elif "ea sports" in t or "fc" in t:
                return "Jogo: EA Sports FC"
            else:
                return "Jogo Genérico"
                
        return f"Outros: {title[:30]}"

    @staticmethod
    def parse_price(price_text: str) -> float:
        """
        Trata e converte a string BRL (ex: 'R$ 4.199,90') para float '4199.90'.
        """
        if not price_text or "sem" in price_text.lower() or "erro" in price_text.lower():
            return 0.0
        
        clean = re.sub(r'[^\d.,]', '', price_text)
        if not clean:
            return 0.0
            
        clean = clean.replace('.', '')
        clean = clean.replace(',', '.')
        
        try:
            return float(clean)
        except ValueError:
            return 0.0
