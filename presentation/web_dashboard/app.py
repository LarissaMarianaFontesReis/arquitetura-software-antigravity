import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Import ports and use cases do seu ecossistema limpo
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from plugins.storage_sqlite.sqlite_adapter import SQLiteQueryAdapter
from core.application.use_cases import GetPriceHistoryUseCase

# Setup Nativo via Hexagonal Injections
query_adapter = SQLiteQueryAdapter()
use_case = GetPriceHistoryUseCase(query_port=query_adapter)

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/api/variants':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            variants = query_adapter.get_all_variants()
            self.wfile.write(json.dumps(variants).encode())
            return
            
        elif parsed_url.path == '/api/history':
            query_params = parse_qs(parsed_url.query)
            variant = query_params.get('variant', [''])[0]
            stats = use_case.execute(variant)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            return
        
        elif parsed_url.path == '/':
            # Rota root aponta para o estatico HTML
            self.path = '/static/index.html'
            return super().do_GET()
            
        else:
            # Qualquer requisicao de arquivo comum (css, js, imagem) vai ser puxada da pasta static
            if not self.path.startswith('/static/'):
                self.path = '/static' + self.path
            return super().do_GET()

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    # Alterando diretório para poder servir os JS/CSS estaticos relativos
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    port = 8080
    httpd = None
    
    for p in range(8080, 8090):
        try:
            server_address = ('', p)
            httpd = ReusableHTTPServer(server_address, DashboardHandler)
            port = p
            break
        except OSError as e:
            if e.errno == 48: # Address in Use
                continue
            else:
                raise
                
    if httpd:
        print("🚀 Servidor Analytics Web CQRS inicializado e blindado!")
        print(f"👉 ACESSE NO SEU NAVEGADOR: http://localhost:{port}")
        httpd.serve_forever()
    else:
        print("⚠️ Erro: As portas 8080 a 8089 já estão sendo usadas por outros aplicativos no seu Mac.")
