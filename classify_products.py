import json

def classify_products(input_file="amazon_products_local.json", output_file="amazon_classified.json"):
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
        
    classified = {
        "Consoles": [],
        "Controles": [],
        "Volantes": [],
        "Headsets & Áudio": [],
        "Jogos": [],
        "Acessórios & Hardware": [],
        "Outros": []
    }
    
    for p in products:
        title = p.get("title", "").lower()
        
        # A ordem das condições importa: um volante para PS5 nunca deve cair na categoria "Consoles" 
        # só porque tem a palavra "PS5" no título. Por isso isolamos as categorias específicas primeiro.
        if any(x in title for x in ["volante", "pedais", "driving force", "g923", "g29"]):
            category = "Volantes"
            
        elif any(x in title for x in ["headset", "fone", "áudio"]):
            category = "Headsets & Áudio"
            
        elif any(x in title for x in ["cabo", "cable", "usb", "suporte", "base", "carregamento", "ssd", "unidade de disco", "vr2", "portal remote", "lcd"]):
            category = "Acessórios & Hardware"
            
        # Puxamos atributos inconfundíveis de Console ANTES de Controle
        # Usamos lógicas fechadas (como evitar "para consoles") para barrar "Controle para consoles Sony"
        elif any(x in title for x in ["console ", "pacote ", "bundle", "edição digital", "digital edition", "disc edition", "disc console"]) and "para console" not in title:
            category = "Consoles"
            
        elif "playstation 5 slim" in title or "playstation®5" in title or "playstation 5 pro" in title or "ps5 digital" in title:
            category = "Consoles"
            
        elif any(x in title for x in ["controle", "dualsense", "controller", "mando", "joystick"]):
            category = "Controles"
            
        elif any(x in title for x in ["jogo", "spider-man", "gran turismo", "ghost of", "resident evil", "pragmata", "mega man", "collection", "game"]):
            category = "Jogos"
            
        elif any(x in title for x in ["playstation 5", "playstation®5", "ps5", "pro", "macbook", "notebook", "xbox one", "xbox"]):
            # Como a busca principal original do usuário inclui o console ou macbooks...
            category = "Consoles"
            
        else:
            category = "Outros"
            
        # O usuário pediu para limpar o JSON mantendo nome, link e fotografia no segmento
        classified[category].append({
            "title": p.get("title"),
            "url": p.get("url"),
            "price": p.get("price_current"),
            "rating": p.get("rating"),
            "image": p.get("image", "")
        })
        
    # Limpa as categorias que ficaram vazias para o JSON final ficar enxuto
    classified = {k: v for k, v in classified.items() if len(v) > 0}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(classified, f, ensure_ascii=False, indent=4)
        
    print(f"Classificação concluída com sucesso! Objeto salvo em {output_file}\n")
    print("Resumo do agrupamento:")
    for cat, items in classified.items():
        print(f" -> {cat}: {len(items)} produtos")

if __name__ == "__main__":
    classify_products()
