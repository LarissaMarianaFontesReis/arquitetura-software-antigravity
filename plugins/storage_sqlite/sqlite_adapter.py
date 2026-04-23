import sqlite3
import datetime
import os
from typing import List
from core.domain.ports import OfferStoragePort, OfferQueryPort

class SQLiteQueryAdapter(OfferQueryPort):
    def __init__(self, db_name: str = "amazon_offers_history.db"):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(root_dir, db_name)
        
    def get_price_history(self, variant_name: str) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price, title, url, image_url
            FROM cheapest_offers_history 
            WHERE variant_name = ? 
            ORDER BY timestamp ASC
        ''', (variant_name,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
        
    def get_all_variants(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT variant_name 
            FROM cheapest_offers_history 
            ORDER BY variant_name ASC
        ''')
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

class SQLiteStorageAdapter(OfferStoragePort):
    def __init__(self, db_name: str = "amazon_offers_history.db"):
        # Garante que o sqlite db caia na raiz do projeto
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(root_dir, db_name)
        self._init_db()
        
    def _init_db(self):
        """Garante que a tabela de histórico de preços exista e possui as colunas necessárias."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cheapest_offers_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                variant_name TEXT NOT NULL,
                price REAL NOT NULL,
                title TEXT,
                url TEXT
            )
        ''')
        
        # Migration: Adiciona image_url se não existir nas extrações antigas
        try:
            cursor.execute('ALTER TABLE cheapest_offers_history ADD COLUMN image_url TEXT')
        except sqlite3.OperationalError:
            pass # A Coluna já existe
            
        conn.commit()
        conn.close()

    def save_cheapest_offers(self, offers: dict) -> None:
        """
        Recebe o dict de model_name -> PriceVariant e salva o snapshot do cenário 
        no banco de dados, compondo o histórico.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        for variant_name, dto in offers.items():
            cursor.execute('''
                INSERT INTO cheapest_offers_history (timestamp, variant_name, price, title, url, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (now, variant_name, dto.price_value, dto.original_title, dto.url, getattr(dto, 'image_url', '')))
            
        conn.commit()
        conn.close()
