# 🎮 PlayStation Price Comparator API

**Antigravity Price Tracker** é um sistema projetado com **Arquitetura Hexagonal (Ports & Adapters)** sob os princípios do **CQRS**. Ele capta, normaliza e orquestra histórico de preços para Consoles e Hardware Gamers listados no *amazon_classified.json*, rastreando ativamente a inflação de ofertas.

---

## 🛠 Topologia de Diretórios (Plugin Architecture)

Esta engine possui um desacoplamento estrito entre "Negócios" e "Infraestrutura":

* `core/`: Motor central impermeável. Possui os *Use Cases* e Serviços e dita as regras da operação de preços sem entender de Banco de Dados.
* `plugins/`: Engrenagens conectáveis físicas (Arquitetura de Plugins).
    * `scrapper_amazon/`: Módulo de ponte para captura do JSON/Crawler.
    * `storage_sqlite/`: Módulo do BD purista com tabela Histórica isolada temporalmente.
* `presentation/`: FrontEnd de linha de comando para consumir Visualmente o histórico CQRS.

---

## 🚀 Como Executar Localmente

Você precisará apenas de **Python 3** configurado em sua máquina. O sistema não necessita de nenhuma biblioteca externa ou configurações pesadas virtuais (`pip install`). 

Na raiz do repositório, estão disponíveis 2 comandos absolutos para você simular as rotinas diárias do Robô:

### Passo 1: Executar o Scraper de Atualização Diária (A Central)

Para buscar os lotes base atualizados, parsear os dados contra a lógica forte de Domain Services e depositar o instantâneo (*snapshot*) atual dessas mercadorias no banco de dados SQLite, rodamos a Interface Primária:

```bash
python3 main.py
```
> 💡 *Dica:* Rode este comando ao menos 1x ao dia. Quando for disparado, o sistema mapeará tudo garantindo que **não sobrepõe** a captura de ontem, montando automaticamente a sua Tabela Temporal (Histórico).

---

### Passo 2: Executar o Terminal de Analytics

Para visualizar o painel do consumidor e avaliar se é uma boa hora para comprar as mercadorias com o preço em queda, utilizamos o Módulo Gráfico (*CQRS / Presentation Layer*):

```bash
python3 presentation/cli_dashboard.py
```
> 💡 *Dica:* A tela do ambiente preencherá gráficos **`Sparkline` ASCII**, Tendências (Alta/Queda), indicando visualmente qual foi os limites máximos/mínimos para peças exatas de consles, baseando-se por tudo aquilo que foi rodado internamente pelo Motor `main.py`!
# sofware-architecture-antigravity-price-comparator
