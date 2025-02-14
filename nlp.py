import spacy
import re
import logging
from datetime import datetime
from utils import add_expense, set_renda, get_summary, get_renda, get_summary_by_category, reset_all

# Configuração do logging para depuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega o modelo spaCy para português
nlp_model = spacy.load("pt_core_news_sm")

def process_message(message, sender):
    """
    Processa a mensagem recebida e determina a ação a ser tomada:
    - Se o usuário enviar um comando de ajuda ("ajuda", "comandos", "help"), retorna as funcionalidades.
    - Se a mensagem contém palavras relacionadas a reset, invoca handle_reset.
    - Se a mensagem contém palavras relacionadas a despesas, invoca handle_expense.
    - Se contém termos relacionados à renda, invoca handle_renda.
    - Se solicita um resumo (ex.: "saldo", "resumo"), invoca handle_summary.
    - Caso contrário, retorna uma mensagem padrão.
    """
    msg = message.strip().lower()
    logger.info("Mensagem recebida de %s: %s", sender, msg)

    # Dicionário de comandos
    help_keywords = ["ajuda", "comandos", "help"]
    reset_keywords = ["reset", "zerar", "apagar tudo", "limpar dados", "reiniciar", "apagar", "reiniciar"]
    expense_keywords = ["gastei", "comprei", "paguei", "custou"]
    income_keywords  = ["renda", "salário", "salario", "ganho", "recebo"]
    summary_keywords = ["resumo", "gastos"]
    handle_financial_keywords = ["saldo", "total"]

    if any(word in msg for word in expense_keywords):
        return handle_expense(message, sender)
    elif any(word in msg for word in income_keywords):
        return handle_renda(message, sender)
    elif any(word in msg for word in summary_keywords):
        return handle_summary(sender)
    elif any(word in msg for word in handle_financial_keywords):
        return handle_financial_summary(sender)
    elif any(word in msg for word in reset_keywords):
        return handle_reset(message, sender)
    elif any(word in msg for word in help_keywords):
        return handle_help(sender)
    else:
        return ("Desculpe, não entendi sua mensagem. Por favor, tente registrar uma despesa, "
                "definir sua renda ou solicitar um resumo.")

def handle_help(sender):
    """
    Retorna uma mensagem com todas as funcionalidades disponíveis.
    """
    response = (
        "Funcionalidades disponíveis:\n\n"
        "1. Registrar despesas:\n"
        "   - Exemplo: 'gastei 50 no supermercado'\n\n"
        "2. Registrar renda:\n"
        "   - Exemplo: 'minha renda é 3000'\n\n"
        "3. Obter resumo simples dos gastos por categoria:\n"
        "   - Exemplo: 'resumo alimentação' ou 'gastos transporte'\n\n"
        "4. Obter resumo financeiro completo:\n"
        "   - Exemplo: 'saldo' ou 'total'\n\n"
        "5. Resetar dados (gastos e renda):\n"
        "   - Exemplo: 'reset' ou 'zerar'\n"
        "     * Após isso, confirme com 'reset ok' para confirmar.\n\n"
        "6. Ajuda:\n"
        "   - Exemplo: 'ajuda', 'comandos' ou 'help'\n\n"
        "Utilize os comandos acima para interagir com o sistema."
    )
    return response

def handle_expense(message, sender):
    """
    Processa uma mensagem de despesa.
    Extrai o valor (usando spaCy e regex) e a categoria (por palavras-chave),
    registra a despesa e retorna uma resposta.
    """
    valor = extract_value(message)
    categoria = extract_category(message)
    data = datetime.now().strftime("%Y-%m-%d")
    
    if valor is not None:
        try:
            add_expense(sender, valor, categoria, data)
            response = f"Despesa de R${valor:.2f} registrada na categoria {categoria}."
            logger.info("Despesa registrada: %s", response)
            return response
        except Exception as e:
            logger.exception("Erro ao registrar despesa: %s", e)
            return "Ocorreu um erro ao registrar sua despesa. Por favor, tente novamente."
    else:
        return "Não consegui identificar o valor da despesa. Por favor, informe o valor corretamente."

def handle_renda(message, sender):
    """
    Processa uma mensagem de definição de renda.
    Extrai o valor e atualiza a renda do usuário.
    """
    valor = extract_value(message)
    if valor is None:
        # Fallback: tenta extrair o último número da mensagem
        numeros = re.findall(r'\d+[.,]?\d*', message)
        if numeros:
            try:
                valor = float(numeros[-1].replace(',', '.'))
            except ValueError:
                return "Não consegui identificar o valor da renda. Tente novamente."
        else:
            return "Não consegui identificar o valor da renda. Tente novamente."
    try:
        set_renda(sender, valor)
        response = f"Sua renda foi definida para R${valor:.2f}."
        logger.info("Renda definida: %s", response)
        return response
    except Exception as e:
        logger.exception("Erro ao definir renda: %s", e)
        return "Ocorreu um erro ao definir sua renda. Por favor, tente novamente."

def handle_summary(sender):
    """
    Gera um resumo dos gastos do usuário.
    """
    try:
        total = get_summary(sender)
        response = f"Você gastou um total de R${total:.2f} até o momento."
        logger.info("Resumo gerado: %s", response)
        return response
    except Exception as e:
        logger.exception("Erro ao gerar resumo: %s", e)
        return "Ocorreu um erro ao gerar o resumo. Por favor, tente novamente."

def handle_financial_summary(sender):
    """
    Gera um resumo financeiro completo que mostra:
      - Renda definida;
      - Gastos Totais;
      - Gastos por Categoria;
      - Saldo (renda - gastos).
    """
    try:
        total_gastos = get_summary(sender)
        renda = get_renda(sender)
        saldo = renda - total_gastos
        
        # Obtém o resumo dos gastos por categoria
        gastos_categoria = get_summary_by_category(sender)
        # Formata os detalhes por categoria
        if gastos_categoria:
            detalhes_categoria = "\n".join(
                [f"  • {categoria}: R${valor:.2f}" for categoria, valor in gastos_categoria.items()]
            )
        else:
            detalhes_categoria = "Nenhum gasto registrado por categoria."
        
        response = (
            f"Resumo Financeiro Completo:\n"
            f"Renda: R${renda:.2f}\n"
            f"Gastos Totais: R${total_gastos:.2f}\n"
            f"Gastos por Categoria:\n{detalhes_categoria}\n"
            f"Saldo: R${saldo:.2f}"
        )
        logger.info("Resumo financeiro completo: %s", response)
        return response
    except Exception as e:
        logger.exception("Erro ao gerar resumo financeiro completo: %s", e)
        return "Ocorreu um erro ao gerar o resumo financeiro. Por favor, tente novamente."
     
def handle_reset(message, sender):
    """
    Processa um comando de reset.
    Se a mensagem contiver termos de confirmação ("sim", "confirmar", "ok") junto com reset,
    realiza o reset dos dados chamando a função reset_all() e retorna uma mensagem de confirmação.
    Caso contrário, retorna uma mensagem perguntando se deseja confirmar o reset.
    """
    # Verifica se a mensagem contém termos de confirmação
    confirm_keywords = ["sim", "confirmar", "ok"]
    if any(word in message for word in confirm_keywords):
        try:
            reset_all()  # Função importada de utils para resetar todos os dados
            logger.info("Dados resetados para %s", sender)
            return "Todos os seus dados (gastos e renda) foram resetados."
        except Exception as e:
            logger.exception("Erro ao resetar dados: %s", e)
            return "Ocorreu um erro ao resetar seus dados. Por favor, tente novamente."
    else:
        return ("Você deseja resetar todos os seus dados (gastos e renda)? "
                "Responda com 'reset ok' para confirmar.")

def extract_value(message):
    """
    Tenta extrair um valor monetário da mensagem.
    Primeiro utiliza spaCy para identificar entidades MONEY; se não conseguir,
    utiliza expressão regular como fallback.
    """
    doc = nlp_model(message)
    # Tenta extrair valores usando entidades do spaCy
    for ent in doc.ents:
        if ent.label_ == "MONEY":
            value_str = re.sub(r'[^\d,\.]', '', ent.text)
            try:
                valor = float(value_str.replace(',', '.'))
                logger.info("Valor extraído com spaCy: %s", valor)
                return valor
            except ValueError:
                continue
    # Fallback com regex
    match = re.search(r'(\d+[.,]?\d*)', message)
    if match:
        try:
            valor = float(match.group(1).replace(',', '.'))
            logger.info("Valor extraído com regex: %s", valor)
            return valor
        except ValueError:
            return None
    return None

def extract_category(message):
    """
    Tenta determinar a categoria da transação a partir da mensagem.
    Usa um conjunto ampliado de palavras-chave para mapear a mensagem para uma categoria.
    Se nenhuma palavra-chave for encontrada, retorna "Outros".
    """
    msg_lower = message.lower()
    categories = {
        # Alimentação
        "almoço": "Alimentação",
        "almoco": "Alimentação",
        "jantar": "Alimentação",
        "café": "Alimentação",
        "lanche": "Alimentação",
        "refeição": "Alimentação",
        "comida": "Alimentação",
        "restaurante": "Alimentação",
        "mercado": "Alimentação",
        "supermercado": "Alimentação",
        "padaria": "Alimentação",
        "fastfood": "Alimentação",
        "pizza": "Alimentação",
        "sushi": "Alimentação",
        "sorvete": "Alimentação",
        "churrasco": "Alimentação",
        "cozinha": "Alimentação",
        # Transporte
        "uber": "Transporte",
        "ônibus": "Transporte",
        "táxi": "Transporte",
        "taxi": "Transporte",
        "trem": "Transporte",
        "metrô": "Transporte",
        "combustível": "Transporte",
        "gasolina": "Transporte",
        "diesel": "Transporte",
        "estacionamento": "Transporte",
        "fretado": "Transporte",
        "transporte": "Transporte",
        "viagem": "Transporte",
        # Lazer
        "cinema": "Lazer",
        "bar": "Lazer",
        "show": "Lazer",
        "festa": "Lazer",
        "teatro": "Lazer",
        "concerto": "Lazer",
        "parque": "Lazer",
        "esporte": "Lazer",
        "jogo": "Lazer",
        "museu": "Lazer",
        "exposição": "Lazer",
        "festivais": "Lazer",
        # Saúde
        "saúde": "Saúde",
        "farmácia": "Saúde",
        "medicamento": "Saúde",
        "consulta": "Saúde",
        "exame": "Saúde",
        "hospital": "Saúde",
        "dentista": "Saúde",
        "clínica": "Saúde",
        "psicólogo": "Saúde",
        "terapia": "Saúde",
        # Educação
        "educação": "Educação",
        "curso": "Educação",
        "livro": "Educação",
        "material escolar": "Educação",
        "universidade": "Educação",
        "ensino": "Educação",
        "escola": "Educação",
        "aula": "Educação",
        # Contas e Serviços
        "conta": "Contas",
        "energia": "Contas",
        "água": "Contas",
        "internet": "Contas",
        "telefone": "Contas",
        "gás": "Contas",
        "cabo": "Contas",
        # Moradia
        "aluguel": "Moradia",
        "imóvel": "Moradia",
        "casa": "Moradia",
        "residência": "Moradia",
        "condomínio": "Moradia",
        "manutenção": "Moradia",
        "reforma": "Moradia",
        # Compras e Vestuário
        "roupa": "Compras",
        "sapato": "Compras",
        "loja": "Compras",
        "shopping": "Compras",
        "presentes": "Compras",
        "eletrônicos": "Compras",
        "gadgets": "Compras",
        "cosméticos": "Compras",
        "acessórios": "Compras",
        # Beleza
        "maquiagem": "Beleza",
        "cabelo": "Beleza",
        "barbearia": "Beleza",
        "spa": "Beleza",
        "estética": "Beleza",
        # Viagens
        "viagem": "Viagens",
        "passagem": "Viagens",
        "hotel": "Viagens",
        "resort": "Viagens",
        "pacote": "Viagens",
        # Serviços
        "serviço": "Serviços",
        "manicure": "Serviços",
        "pedicure": "Serviços",
        "limpeza": "Serviços",
        "assistência": "Serviços",
        "conserto": "Serviços",
        "reparo": "Serviços"
    }

    for keyword, cat in categories.items():
        if keyword in msg_lower:
            logger.info("Categoria identificada: %s", cat)
            return cat
    return "Outros"
