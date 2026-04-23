import os
import sys

# Garante a importação do core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.storage_sqlite.sqlite_adapter import SQLiteQueryAdapter
from core.application.use_cases import GetPriceHistoryUseCase

def draw_sparkline(prices):
    """Gera um mini-gráfico ASCII para inflação baseado no array de preços."""
    if not prices: return ""
    if len(prices) == 1: return "●"
    
    # Normaliza os precos entre 0 e 7 (para os 8 blocos iterativos)
    min_p, max_p = min(prices), max(prices)
    if min_p == max_p:
        return "─" * len(prices)
        
    chars = " ▂▃▄▅▆▇█"
    sparkline = ""
    for p in prices:
        idx = int((p - min_p) / (max_p - min_p) * 7)
        sparkline += chars[idx]
    return sparkline

def run_dashboard():
    query_adapter = SQLiteQueryAdapter()
    use_case = GetPriceHistoryUseCase(query_port=query_adapter)
    
    print("\n=======================================================")
    print(" 📈 DASHBOARD DE ANALYTICS: HISTÓRICO DE INFLAÇÃO ")
    print("=======================================================\n")
    
    # Extrai todas as variantes e varre a matemática temporal
    variants = query_adapter.get_all_variants()
    
    for variant in variants:
        stats = use_case.execute(variant)
        
        if "error" in stats:
            continue
            
        prices = [float(item['price']) for item in stats['timeline']]
        curr_price = stats['current_price']
        lowest = stats['lowest_historical_price']
        highest = stats['highest_historical_price']
        records = stats['total_records']
        
        # Define Qual a Tendência Primária
        if len(prices) >= 2:
            trend_val = prices[-1] - prices[-2]
            if trend_val < 0: trend = f"🔽 Queda de R$ {abs(trend_val):.2f}"
            elif trend_val > 0: trend = f"🔼 Alta de R$ {trend_val:.2f}"
            else: trend = "➖ Preço Estabilizado"
        else:
            trend = "🆕 Começando a Rastrear"
            
        spark = draw_sparkline(prices)
        
        # UI Terminal Format
        print(f"🕹️  {variant.upper()}")
        print(f"📉 Sparkline Temporal : [{spark}] ({records} capturas salva no banco)")
        print(f"💰 Preço Atual        : R$ {curr_price:.2f}")
        print(f"🥇 Menor Preço Histórico: R$ {lowest:.2f}")
        print(f"📈 Maior Preço Histórico: R$ {highest:.2f}")
        print(f"🔥 Tendência Imediata : {trend}")
        print("-" * 55)

if __name__ == "__main__":
    run_dashboard()
