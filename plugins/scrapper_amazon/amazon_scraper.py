import json
import requests
from parsel import Selector
import time
import random
import os
import re

OUTPUT_JSON = "amazon_products_local.json"

def scrape_amazon_search(search_urls):
    """
    Função 1: Raspa a página de busca para obter a listagem de produtos.
    """
    product_data = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    for search_url in search_urls:
        print(f"Buscando produtos na página: {search_url}")
        try:
            time.sleep(random.uniform(1.0, 2.5))
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 503:
                print(f"⚠️  Bloqueado pela Amazon (Erro 503 / CAPTCHA)")
                continue
                
            response.raise_for_status()

            selector = Selector(text=response.text)
            search_results = selector.css('[data-component-type="s-search-result"]')
            print(f"Encontrados {len(search_results)} resultados na página. Processando...")
            
            for item in search_results:
                title = item.css('[data-cy="title-recipe"] h2 span::text').get()
                if not title:
                    title = item.css('h2 span::text').get()
                    
                price = item.css('[data-cy="price-recipe"] span.a-price span.a-offscreen::text').get()
                if not price:
                    price = item.css('span.a-price span.a-offscreen::text').get()
                    
                link = item.css('[data-cy="title-recipe"] a::attr(href)').get()
                if not link:
                    link = item.css('h2 a::attr(href)').get()
                    if not link:
                        a_tag = item.css('h2').xpath('..')
                        if a_tag and a_tag[0].root.tag == 'a':
                            link = a_tag[0].attrib.get('href')

                rating = item.css('span.a-icon-alt::text').get()
                sku = item.attrib.get('data-asin')
                
                # Novos campos da vitrine
                image_url = item.css('img.s-image::attr(src)').get()
                review_count = item.css('span.a-size-base.s-underline-text::text').get()
                original_price = item.css('span.a-price.a-text-price span.a-offscreen::text').get()
                sponsored = "Sim" if item.css('.puis-sponsored-label-text, .puis-sponsored-label-info-icon').get() else "Não"
                is_prime = "Sim" if item.css('i.a-icon-prime').get() else "Não"
                sales_info = item.xpath('.//span[contains(text(), "comprados")]/text()').get()
                
                # Tenta compor dados de entrega de vários spans disponíveis
                delivery = item.css('[data-cy="delivery-recipe"] span.a-text-bold::text').getall()
                delivery_msg = " | ".join([d.strip() for d in delivery if d.strip()])
                
                if not link or "javascript" in link or len(link) < 5:
                    link = f"/dp/{sku}"
                    
                if link and not link.startswith('http'):
                    link = "https://www.amazon.com.br" + link
                    
                if title:
                    produto = {
                        "sku_amazon": sku,
                        "title": title.strip(),
                        "price_current": price.strip() if price else "Sem preço",
                        "price_original": original_price.strip() if original_price else "Sem desconto",
                        "rating": rating.strip() if rating else "Sem avaliação",
                        "reviews_count": review_count.strip() if review_count else "0",
                        "sales_info": sales_info.strip() if sales_info else "-",
                        "sponsored": sponsored,
                        "is_prime": is_prime,
                        "delivery": delivery_msg if delivery_msg else "-",
                        "image": image_url,
                        "url": link
                    }
                    product_data.append(produto)
                    
        except Exception as e:
            print(f"Erro ao extrair a página de busca: {e}")

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(product_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nFinalizado! Dados salvos em '{OUTPUT_JSON}'.")


def enrich_with_manufacturer_sku(limit=3):
    """
    Função 2: Entra na página individual dos produtos para obter o SKU do fabricante
    salvando incrementalmente para nunca repetir produtos já visitados.
    """
    if not os.path.exists(OUTPUT_JSON):
        print(f"Arquivo {OUTPUT_JSON} não encontrado. Execute a busca primeiro.")
        return

    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        product_data = json.load(f)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    processed_count = 0
    updated = False

    for item in product_data:
        if processed_count >= limit:
            break
            
        # Pula se o script já processou esse produto anteriormente validando a chave "manufacturer_sku"
        if "manufacturer_sku" in item and item["manufacturer_sku"] not in [None, "Erro", "Não encontrado"]:
            continue

        # Constrói a URL Padrão/Canônica usando o SKU (ASIN), à prova de banners com javascript:void(0)
        url = item.get("url")
        sku = item.get("sku_amazon") or item.get("sku", "")
        if "javascript" in url or not url.startswith("http") or len(url) < 15:
            url = f"https://www.amazon.com.br/dp/{sku}"
            item["url"] = url

        title = item.get("title", "")
        print(f"\n[{processed_count+1}/{limit}] Acessando aba do produto: {title[:50]}...")
        
        try:
            # Pausa humana crucial entre cada produto
            time.sleep(random.uniform(2.5, 5.0))
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 503:
                print("⚠️ Bloqueado por CAPTCHA da Amazon. Parando execução para proteger seu IP.")
                break
                
            response.raise_for_status()
            sel = Selector(text=response.text)
            
            found_model = "Não encontrado na página"
            
            # Vamos iterar por todos os elementos comuns da Amazon que guardam as especificações
            rows = sel.css('tr, li, div')
            for r in rows:
                # Pega todo texto do elemento e une em uma string para encontrar a combinação de campos
                text = " ".join(r.css('*::text').getall()).replace('\n', ' ').strip()
                text_lower = text.lower()
                
                # Procura explicitamente por Modelo ou Referência de Fabricante
                if 'número do modelo' in text_lower or 'referência do fabricante' in text_lower:
                    parts = re.split(r'(?i)número do modelo|referência do fabricante', text)
                    if len(parts) > 1:
                        # Limpa espaços em brancos invisíveis, dois pontos, etc.
                        clean_val = parts[-1].replace(':', '').strip().replace('\u200e', '')
                        if clean_val and len(clean_val) < 40 and " {" not in clean_val:
                            found_model = clean_val
                            break

            print(f" -> Modelo do Fabricante extraído: {found_model}")
            item["manufacturer_sku"] = found_model
            updated = True
            processed_count += 1
            
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            item["manufacturer_sku"] = f"Erro: {str(e)}"
            updated = True
            processed_count += 1

    # Ao final da rodada de no máximo 3 itens, salvamos o JSON com as chaves atualizadas
    if updated:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=4)
        print(f"\nConcluído! {processed_count} produtos enriquecidos incrementalmente.")
    else:
        print("\nTodos os produtos do JSON já estão enriquecidos ou limite foi atingido.")

if __name__ == "__main__":
    termos_de_busca = [
        "https://www.amazon.com.br/s?k=playstation+5",
        "https://www.amazon.com.br/s?k=xbox+one"
    ]
    print("Iniciando varredura da vitrine com todas as propriedades estendidas...")
    scrape_amazon_search(termos_de_busca)
    
    # Executa apenas nos próximos 3 produtos da lista que NÃO tem o 'manufacturer_sku'
    # enrich_with_manufacturer_sku(limit=3)
