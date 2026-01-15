
MARKET_UNIVERSE = [
    # ====================================================================
    # 1. ACCIONES (20 activos)
    # ====================================================================
    {'name': 'Apple Inc.', 'symbol': 'AAPL', 'category': 'acciones'},
    {'name': 'Microsoft Corp.', 'symbol': 'MSFT', 'category': 'acciones'},
    {'name': 'Alphabet Inc. (Google) - Class C', 'symbol': 'GOOG', 'category': 'acciones'},
    {'name': 'Amazon.com, Inc.', 'symbol': 'AMZN', 'category': 'acciones'},
    {'name': 'Tesla Inc.', 'symbol': 'TSLA', 'category': 'acciones'},
    {'name': 'NVIDIA Corp.', 'symbol': 'NVDA', 'category': 'acciones'},
    {'name': 'Meta Platforms Inc. (Facebook)', 'symbol': 'META', 'category': 'acciones'},
    {'name': 'Johnson & Johnson', 'symbol': 'JNJ', 'category': 'acciones'},
    {'name': 'JPMorgan Chase & Co.', 'symbol': 'JPM', 'category': 'acciones'},
    {'name': 'Visa Inc.', 'symbol': 'V', 'category': 'acciones'},
    {'name': 'Procter & Gamble Co.', 'symbol': 'PG', 'category': 'acciones'},
    {'name': 'Exxon Mobil Corporation', 'symbol': 'XOM', 'category': 'acciones'},
    {'name': 'UnitedHealth Group Inc.', 'symbol': 'UNH', 'category': 'acciones'},
    {'name': 'Home Depot, Inc.', 'symbol': 'HD', 'category': 'acciones'},
    {'name': 'Coca-Cola Company', 'symbol': 'KO', 'category': 'acciones'},
    {'name': 'Pfizer Inc.', 'symbol': 'PFE', 'category': 'acciones'},
    {'name': 'Salesforce, Inc.', 'symbol': 'CRM', 'category': 'acciones'},
    {'name': 'Netflix, Inc.', 'symbol': 'NFLX', 'category': 'acciones'},
    {'name': 'Advanced Micro Devices, Inc.', 'symbol': 'AMD', 'category': 'acciones'},
    {'name': 'Alibaba Group Holding Ltd.', 'symbol': 'BABA', 'category': 'acciones'},

    # ====================================================================
    # 2. ETFS (20 activos)
    # ====================================================================
    {'name': 'Vanguard S&P 500 ETF', 'symbol': 'VOO', 'category': 'etfs'},
    {'name': 'iShares Core S&P 500 ETF', 'symbol': 'IVV', 'category': 'etfs'},
    {'name': 'Invesco QQQ Trust (Nasdaq 100)', 'symbol': 'QQQ', 'category': 'etfs'},
    {'name': 'Vanguard Total Stock Market ETF', 'symbol': 'VTI', 'category': 'etfs'},
    {'name': 'iShares Russell 2000 ETF (Small Cap)', 'symbol': 'IWM', 'category': 'etfs'},
    {'name': 'Vanguard FTSE Developed Markets ETF', 'symbol': 'VEA', 'category': 'etfs'},
    {'name': 'Vanguard FTSE Emerging Markets ETF', 'symbol': 'VWO', 'category': 'etfs'},
    {'name': 'SPDR Gold Shares', 'symbol': 'GLD', 'category': 'etfs'},
    {'name': 'Energy Select Sector SPDR Fund', 'symbol': 'XLE', 'category': 'etfs'},
    {'name': 'Financial Select Sector SPDR Fund', 'symbol': 'XLF', 'category': 'etfs'},
    {'name': 'Health Care Select Sector SPDR Fund', 'symbol': 'XLV', 'category': 'etfs'},
    {'name': 'iShares Core U.S. Aggregate Bond ETF', 'symbol': 'AGG', 'category': 'etfs'},
    {'name': 'ARK Innovation ETF', 'symbol': 'ARKK', 'category': 'etfs'},
    {'name': 'Global X Uranium ETF', 'symbol': 'URA', 'category': 'etfs'},
    {'name': 'iShares Global Clean Energy ETF', 'symbol': 'ICLN', 'category': 'etfs'},
    {'name': 'The Real Estate Select Sector SPDR Fund', 'symbol': 'XLRE', 'category': 'etfs'},
    {'name': 'First Trust NYSE Arca Biotechnology ETF', 'symbol': 'FBT', 'category': 'etfs'},
    {'name': 'iShares MSCI EAFE ETF', 'symbol': 'EFA', 'category': 'etfs'},
    {'name': 'Vanguard Mid-Cap ETF', 'symbol': 'VO', 'category': 'etfs'},
    {'name': 'SPDR S&P Dividend ETF', 'symbol': 'SDY', 'category': 'etfs'},

    # ====================================================================
    # 3. FONDOS DE INVERSIÓN (20 activos)
    # ====================================================================
    {'name': 'Fidelity 500 Index Fund', 'symbol': 'FXAIX', 'category': 'fondos'},
    {'name': 'Vanguard Total Stock Market Index Fund Admiral Shares', 'symbol': 'VTSAX', 'category': 'fondos'},
    {'name': 'Fidelity NASDAQ Composite Index Fund', 'symbol': 'FNCMX', 'category': 'fondos'},
    {'name': 'Vanguard Total International Stock Index Fund Admiral Shares', 'symbol': 'VTIAX', 'category': 'fondos'},
    {'name': 'Fidelity International Index Fund', 'symbol': 'FSPSX', 'category': 'fondos'},
    {'name': 'Vanguard Total Bond Market Index Fund Admiral Shares', 'symbol': 'VBTLX', 'category': 'fondos'},
    {'name': 'Fidelity Mid Cap Index Fund', 'symbol': 'FSMDX', 'category': 'fondos'},
    {'name': 'Vanguard Real Estate Index Fund Admiral Shares', 'symbol': 'VGSIX', 'category': 'fondos'},
    {'name': 'Fidelity Contrafund', 'symbol': 'FCNTX', 'category': 'fondos'},
    {'name': 'Vanguard Growth Index Fund Admiral Shares', 'symbol': 'VIGAX', 'category': 'fondos'},
    {'name': 'Fidelity Small Cap Index Fund', 'symbol': 'FSSNX', 'category': 'fondos'},
    {'name': 'Vanguard High-Yield Corporate Fund Investor Shares', 'symbol': 'VWEAX', 'category': 'fondos'},
    {'name': 'Fidelity Technology Fund', 'symbol': 'FSELX', 'category': 'fondos'},
    {'name': 'Vanguard European Stock Index Fund Admiral Shares', 'symbol': 'VEUSX', 'category': 'fondos'},
    {'name': 'Fidelity Health Care Fund', 'symbol': 'FHLC', 'category': 'fondos'},
    {'name': 'Vanguard Dividend Growth Fund', 'symbol': 'VDIGX', 'category': 'fondos'},
    {'name': 'Fidelity U.S. Bond Index Fund', 'symbol': 'FXNAX', 'category': 'fondos'},
    {'name': 'Vanguard Developed Markets Index Fund Admiral Shares', 'symbol': 'VTMGX', 'category': 'fondos'},
    {'name': 'Fidelity Total International Bond Fund', 'symbol': 'FTIEX', 'category': 'fondos'},
    {'name': 'Vanguard Target Retirement 2050 Fund', 'symbol': 'VFIFX', 'category': 'fondos'},

    # ====================================================================
    # 4. RENTA FIJA / BONOS (20 activos)
    # ====================================================================
    {'name': 'iShares 20+ Year Treasury Bond ETF', 'symbol': 'TLT', 'category': 'renta-fija'},
    {'name': 'Vanguard Total Bond Market ETF', 'symbol': 'BND', 'category': 'renta-fija'},
    {'name': 'iShares iBoxx $ Inv Grade Corp Bd ETF', 'symbol': 'LQD', 'category': 'renta-fija'},
    {'name': 'SPDR Bloomberg High Yield Bond ETF', 'symbol': 'JNK', 'category': 'renta-fija'},
    {'name': 'iShares Short-Term Treasury Bond ETF', 'symbol': 'SHV', 'category': 'renta-fija'},
    {'name': 'Vanguard Short-Term Bond ETF', 'symbol': 'BSV', 'category': 'renta-fija'},
    {'name': 'iShares National Muni Bond ETF', 'symbol': 'MUB', 'category': 'renta-fija'},
    {'name': 'Vanguard Intermediate-Term Bond ETF', 'symbol': 'BIV', 'category': 'renta-fija'},
    {'name': 'SPDR Portfolio Intermediate Term Corp Bond ETF', 'symbol': 'SPIB', 'category': 'renta-fija'},
    {'name': 'PIMCO Enhanced Low Duration Active ETF', 'symbol': 'LDUR', 'category': 'renta-fija'},
    {'name': 'iShares 7-10 Year Treasury Bond ETF', 'symbol': 'IEF', 'category': 'renta-fija'},
    {'name': 'Vanguard Mortgage-Backed Securities ETF', 'symbol': 'VMBS', 'category': 'renta-fija'},
    {'name': 'iShares J.P. Morgan USD Emerging Markets Bond ETF', 'symbol': 'EMB', 'category': 'renta-fija'},
    {'name': 'iShares Global Corporate Bond ETF', 'symbol': 'BNDX', 'category': 'renta-fija'},
    {'name': 'SPDR TIPS ETF', 'symbol': 'TIPS', 'category': 'renta-fija'},
    {'name': 'iShares Inflation Protected Bond ETF', 'symbol': 'TIP', 'category': 'renta-fija'},
    {'name': 'Vanguard Total International Bond ETF', 'symbol': 'BNDX', 'category': 'renta-fija'},
    {'name': 'VanEck Vectors Fallen Angel High Yield Bond ETF', 'symbol': 'ANGL', 'category': 'renta-fija'},
    {'name': 'Invesco Preferred ETF', 'symbol': 'PGX', 'category': 'renta-fija'},
    {'name': 'iShares AAA - AA Rated Corporate Bond ETF', 'symbol': 'QLTA', 'category': 'renta-fija'},

    # ====================================================================
    # 5. CRIPTOMONEDAS (20 activos)
    # ====================================================================
    {'name': 'Bitcoin', 'symbol': 'BTC-USD', 'category': 'crypto'},
    {'name': 'Ethereum', 'symbol': 'ETH-USD', 'category': 'crypto'},
    {'name': 'Solana', 'symbol': 'SOL-USD', 'category': 'crypto'},
    {'name': 'Ripple', 'symbol': 'XRP-USD', 'category': 'crypto'},
    {'name': 'Dogecoin', 'symbol': 'DOGE-USD', 'category': 'crypto'},
    {'name': 'Cardano', 'symbol': 'ADA-USD', 'category': 'crypto'},
    {'name': 'Avalanche', 'symbol': 'AVAX-USD', 'category': 'crypto'},
    {'name': 'Polkadot', 'symbol': 'DOT-USD', 'category': 'crypto'},
    {'name': 'Polygon', 'symbol': 'MATIC-USD', 'category': 'crypto'},
    {'name': 'Shiba Inu', 'symbol': 'SHIB-USD', 'category': 'crypto'},
    {'name': 'Chainlink', 'symbol': 'LINK-USD', 'category': 'crypto'},
    {'name': 'Litecoin', 'symbol': 'LTC-USD', 'category': 'crypto'},
    {'name': 'Bitcoin Cash', 'symbol': 'BCH-USD', 'category': 'crypto'},
    {'name': 'Uniswap', 'symbol': 'UNI-USD', 'category': 'crypto'},
    {'name': 'Ethereum Classic', 'symbol': 'ETC-USD', 'category': 'crypto'},
    {'name': 'Stellar', 'symbol': 'XLM-USD', 'category': 'crypto'},
    {'name': 'Cosmos', 'symbol': 'ATOM-USD', 'category': 'crypto'},
    {'name': 'Monero', 'symbol': 'XMR-USD', 'category': 'crypto'},
    {'name': 'TRON', 'symbol': 'TRX-USD', 'category': 'crypto'},
    {'name': 'NEAR Protocol', 'symbol': 'NEAR-USD', 'category': 'crypto'},
]


# ====================================================================
# BASE DE CONOCIMIENTO PARA IA DE INVERSIÓN
# ====================================================================

INVESTMENT_KNOWLEDGE = {
    'acción': 'Una acción es una parte de propiedad en una empresa. Cuando compras acciones, te conviertes en accionista y tienes derechos sobre las ganancias y decisiones de la empresa. Las acciones pueden subir o bajar de valor según el desempeño de la empresa.',
    
    'dividendo': 'Los dividendos son pagos periódicos que algunas empresas hacen a sus accionistas como parte de sus ganancias. No todas las empresas pagan dividendos, y la cantidad varía según el desempeño financiero.',
    
    'riesgo': 'El riesgo en inversión se refiere a la posibilidad de perder dinero. Hay diferentes niveles: acciones pequeñas tienen riesgo alto, bonos tienen riesgo bajo, y fondos indexados ofrecen riesgo moderado. La clave es diversificar tu portafolio.',
    
    'volatilidad': 'La volatilidad mide cuánto cambia el precio de un activo. Alta volatilidad = cambios grandes y rápidos = mayor riesgo pero también mayor potencial de ganancia. Baja volatilidad = cambios pequeños = más estable.',
    
    'diversificación': 'Diversificar significa distribuir tu dinero entre diferentes activos, sectores y empresas. Esto reduce el riesgo porque si un sector tiene problemas, los otros pueden compensar. Es la regla de oro: no pongas todos los huevos en una canasta.',
    
    'portafolio': 'Un portafolio es la colección de todas tus inversiones. Incluye acciones, bonos, fondos, y otros activos. Un buen portafolio está balanceado y diversificado según tu perfil de riesgo.',
    
    'mercado': 'El mercado es el lugar (ahora generalmente digital) donde se compran y venden activos financieros como acciones, bonos y fondos. Los precios fluctúan basándose en oferta, demanda y noticias económicas.',
    
    'comprar': 'Para comprar una acción, necesitas acceso a un broker (plataforma de trading). Seleccionas el activo, cantidad, y tipo de orden (market o limit). Una orden market se ejecuta al precio actual, una limit espera un precio específico.',
    
    'vender': 'Para vender acciones que ya posees, usa la misma plataforma. Puedes vender al precio actual o establecer un límite de precio. Cuando vendes, se realiza tu ganancia o pérdida.',
    
    'orden limit': 'Una orden limit te permite comprar o vender solo a un precio específico o mejor. Es útil para garantizar que no pagas más de lo que deseas. Si el precio nunca alcanza tu límite, la orden no se ejecuta.',
    
    'long': 'Una posición long significa que compras una acción esperando que suba de precio. Es la forma tradicional de invertir: comprar bajo, vender alto. Beneficias si el precio sube.',
    
    'short': 'Una posición short es cuando vendes una acción que no posees, esperando que baje de precio. Es más arriesgado y requiere experiencia. Beneficias si el precio baja.',
    
    'etf': 'Un ETF (Fondo Cotizado) es una canasta de acciones que se comporta como una sola acción. Ofrece diversificación instantánea con bajo costo. Es ideal para principiantes que quieren diversidad automática.',
    
    'fondo': 'Un fondo mutuo es una colección de dinero de muchos inversionistas usado para comprar acciones, bonos u otros activos. Profesionales lo manejan, pero tiene comisiones más altas que los ETFs.',
    
    'comisión': 'Las comisiones son los costos que cobran los brokers por operar. Pueden ser por transacción o porcentaje. Es importante minimizarlas porque restan de tus ganancias. Usa plataformas con comisiones bajas o cero.',
    
    'análisis técnico': 'El análisis técnico estudia gráficos de precios históricos para predecir movimientos futuros. Usa patrones, soporte/resistencia, e indicadores. Muchos traders lo usan, pero no es infalible.',
    
    'análisis fundamental': 'El análisis fundamental estudia los estados financieros de una empresa (ganancias, deuda, flujo de caja) para determinar si está subvaluada o sobrevalorada. Es el enfoque de Warren Buffett.',
    
    'p/e': 'El ratio P/E (Precio/Ganancia) compara el precio de una acción con sus ganancias anuales. Un P/E bajo puede indicar que está barata, pero también puede significar problemas. Úsalo con otros indicadores.',
    
    'principal': 'El principal es la cantidad inicial de dinero que inviertes. Si inviertes $1000, ese es tu principal. Tu ganancia es cualquier aumento por encima de eso.',
    
    'retorno': 'El retorno es la ganancia que obtienes de tu inversión, expresada como porcentaje. Si inviertes $100 y ganas $10, tu retorno es 10%. Cuanto mayor el retorno, mejor, pero conlleva más riesgo.',
    
    'pnl': 'P&L significa Ganancia y Pérdida (Profit & Loss). Es tu ganancia o pérdida total en dinero o porcentaje. Es crucial monitorearlo para saber cómo va tu inversión.',
    
    'stop loss': 'Un stop loss es una orden que vende automáticamente cuando el precio baja a cierto nivel. Te protege de grandes pérdidas. Si compras a $50 y estableces stop loss a $45, se vende automáticamente si baja a $45.',
    
    'take profit': 'Un take profit es una orden que vende automáticamente cuando ganas cierta cantidad. Te asegura ganancias sin emoción. Si ganas 20%, puedes establecer take profit para vender automáticamente.',
    
    'buscador': 'Para comenzar a invertir, necesitas: conocimiento (estás en el lugar correcto), un broker (plataforma), dinero, y disciplina. Empieza pequeño, aprende, y escala gradualmente.',
    
    'empezar': 'Para empezar: 1) Abre una cuenta en un broker, 2) Haz tu depósito inicial, 3) Educa sobre mercados, 4) Compra activos diversificados, 5) Monitorea regularmente, 6) Aprende de tus errores.',
    
    'largo plazo': 'Invertir a largo plazo (años o décadas) es generalmente más seguro porque aprovechas el crecimiento compuesto. Experimenta menos volatilidad que el trading activo. Es ideal para jubilación.',
    
    'corto plazo': 'Invertir a corto plazo (días, semanas, meses) es más riesgado pero puede ser lucrativo. Requiere análisis constante y disciplina. No es recomendado para principiantes.',
    
    'interés compuesto': 'El interés compuesto es cuando ganas interés sobre tu interés anterior. Si inviertes $1000 a 10% anual: Año 1: $1100, Año 2: $1210, etc. Crece exponencialmente con tiempo.',
}

DEFAULT_RESPONSES = [
    '💡 Es una buena pregunta. Aunque no tengo información específica sobre eso, puedo decirte que en inversión es importante investigar, diversificar y tener una estrategia clara. ¿Hay algo más específico que quieras saber sobre acciones, bonos, o estrategias de inversión?',
    '🤔 Esa es una pregunta compleja. Lo más importante en inversión es entender tu perfil de riesgo, establecer objetivos claros y diversificar tu portafolio. ¿Quieres saber más sobre algún aspecto específico?',
    '📚 Recomiendo aprender sobre los fundamentos primero: qué son acciones, bonos, ETFs, y cómo diversificar. Luego, puedes explorar estrategias más avanzadas. ¿Hay algún concepto que quieras que explique?',
]

# Categorización de tópicos para mejor comprensión
TOPIC_CATEGORIES = {
    'basicos': ['acción', 'dividendo', 'mercado', 'portafolio', 'fondo', 'etf'],
    'riesgos': ['riesgo', 'volatilidad', 'stop loss', 'short'],
    'estrategia': ['largo plazo', 'corto plazo', 'diversificación', 'comprar', 'vender'],
    'analisis': ['análisis técnico', 'análisis fundamental', 'p/e', 'pnl'],
    'ordenes': ['orden limit', 'take profit', 'long'],
    'costos': ['comisión', 'principal', 'retorno', 'interés compuesto'],
}

SUGGESTED_QUESTIONS = [
    '¿Qué es una acción?',
    '¿Cómo empiezo a invertir?',
    '¿Qué es diversificación?',
    '¿Cuál es la diferencia entre largo plazo y corto plazo?',
    '¿Qué son los dividendos?',
    '¿Qué es un ETF?',
    '¿Cómo reduzco el riesgo?',
    '¿Qué es un stop loss?',
]


def calculate_similarity(text1, text2):
    """
    Calcula similitud fuzzy entre dos textos.
    """
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    if text1 == text2:
        return 1.0
    
    if text1 in text2 or text2 in text1:
        return 0.8
    
    common = sum(1 for c in text1 if c in text2)
    max_len = max(len(text1), len(text2))
    return common / max_len if max_len > 0 else 0


def find_best_keyword_match(message):
    """
    Encuentra la mejor coincidencia de palabra clave en el mensaje.
    Usa fuzzy matching para ser más inteligente.
    """
    message_lower = message.lower()
    best_match = None
    best_score = 0
    best_answer = None
    
    for keyword, answer in INVESTMENT_KNOWLEDGE.items():
        if keyword in message_lower:
            return (keyword, answer, 1.0)
        
        similarity = calculate_similarity(keyword, message_lower)
        if similarity > best_score:
            best_score = similarity
            best_match = keyword
            best_answer = answer
    
    return (best_match, best_answer, best_score) if best_score > 0.6 else (None, None, 0)


def get_topic_category(keyword):
    """
    Obtiene la categoría de un tópico.
    """
    for category, keywords in TOPIC_CATEGORIES.items():
        if keyword in keywords:
            return category
    return None


def generate_investment_response(user_message):
    """
    Genera una respuesta inteligente sobre inversión.
    Utiliza fuzzy matching, contexto y categorización.
    
    Args:
        user_message (str): El mensaje del usuario
    
    Returns:
        dict: {'success': bool, 'response': str, 'suggestions': list}
    """
    import random
    
    if not user_message or not user_message.strip():
        return {
            'success': False,
            'response': '❌ Por favor, escribe una pregunta válida.',
            'suggestions': SUGGESTED_QUESTIONS[:3]
        }
    
    keyword, answer, confidence = find_best_keyword_match(user_message)
    
    if confidence > 0.6:
        category = get_topic_category(keyword)
        response_text = answer
        relevant_suggestions = []
        
        if category:
            for cat_keyword in TOPIC_CATEGORIES.get(category, []):
                if cat_keyword != keyword:
                    relevant_suggestions.append(f'¿Qué es {cat_keyword.title()}?')
        
        if not relevant_suggestions:
            relevant_suggestions = random.sample(SUGGESTED_QUESTIONS, min(2, len(SUGGESTED_QUESTIONS)))
        else:
            relevant_suggestions = relevant_suggestions[:2]
        
        return {
            'success': True,
            'response': f'📚 {response_text}',
            'suggestions': relevant_suggestions,
            'topic': keyword
        }
    else:
        response = random.choice(DEFAULT_RESPONSES)
        return {
            'success': True,
            'response': response,
            'suggestions': random.sample(SUGGESTED_QUESTIONS, min(3, len(SUGGESTED_QUESTIONS)))
        }
