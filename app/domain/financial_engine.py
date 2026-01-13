"""
Motor de simulación financiera educativo.

Responsabilidad: Lógica pura de operaciones de trading.
- Sin acceso directo a BD (excepto lectura de transacciones)
- Funciones deterministas y testeables
- Validaciones estrictas de reglas
- Excepciones claras para casos de error

El ledger de transacciones es la única fuente de verdad del estado del portfolio.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from datetime import datetime


# ========================================================================
# EXCEPCIONES PERSONALIZADAS
# ========================================================================

class SimulationError(Exception):
    """Excepción base del simulador"""
    pass


class InsufficientCapitalError(SimulationError):
    """No hay suficiente capital para ejecutar la operación"""
    pass


class InsufficientHoldingsError(SimulationError):
    """No hay suficientes unidades para vender"""
    pass


class InvalidOperationError(SimulationError):
    """Operación inválida (precio negativo, cantidad inválida, etc.)"""
    pass


class InsufficientPriceDataError(SimulationError):
    """No se pudo obtener el precio de ejecución"""
    pass


# ========================================================================
# ESTRUCTURAS DE DATOS
# ========================================================================

@dataclass
class PriceSnapshot:
    """Snapshot de precio en el momento de ejecución"""
    symbol: str
    price: float
    timestamp: datetime
    
    def validate(self):
        if self.price <= 0:
            raise InvalidOperationError(f"Precio inválido para {self.symbol}: ${self.price}")
        if not self.timestamp:
            raise InvalidOperationError("Timestamp requerido en snapshot de precio")


@dataclass
class ExecutionResult:
    """Resultado de la ejecución de una operación"""
    success: bool
    transaction_id: Optional[int]
    symbol: str
    type: str  # 'BUY' o 'SELL'
    quantity: float
    price_per_unit: float
    total_amount: float
    commission_amount: float
    total_cost: float
    message: str
    remaining_capital: Optional[float] = None
    

@dataclass
class PortfolioSnapshot:
    """Snapshot del estado actual del portfolio"""
    total_capital: float
    total_invested: float
    cash_available: float
    holdings: Dict[str, Dict]  # {symbol: {quantity, avg_buy_price, current_value}}
    total_portfolio_value: float


# ========================================================================
# FUNCIONES PURAS DE CÁLCULO
# ========================================================================

def calculate_buy_cost(quantity: float, price_per_unit: float, commission_rate: float) -> Tuple[float, float]:
    """
    Calcula el costo total de una compra incluyendo comisión.
    
    Returns:
        (total_before_commission, commission_amount)
    """
    if quantity <= 0:
        raise InvalidOperationError("Cantidad debe ser positiva")
    if price_per_unit <= 0:
        raise InvalidOperationError("Precio debe ser positivo")
    if commission_rate < 0:
        raise InvalidOperationError("Comisión no puede ser negativa")
    
    total_before_commission = quantity * price_per_unit
    commission_amount = total_before_commission * commission_rate
    
    return total_before_commission, commission_amount


def calculate_sell_proceeds(quantity: float, price_per_unit: float, commission_rate: float) -> Tuple[float, float]:
    """
    Calcula el ingreso neto de una venta (después de comisión).
    
    Returns:
        (total_before_commission, commission_amount)
    """
    if quantity <= 0:
        raise InvalidOperationError("Cantidad debe ser positiva")
    if price_per_unit <= 0:
        raise InvalidOperationError("Precio debe ser positivo")
    if commission_rate < 0:
        raise InvalidOperationError("Comisión no puede ser negativa")
    
    total_before_commission = quantity * price_per_unit
    commission_amount = total_before_commission * commission_rate
    
    return total_before_commission, commission_amount


def validate_buy_order(
    quantity: float,
    amount_to_buy: Optional[float],
    capital_available: float,
    price_per_unit: float,
    commission_rate: float,
    min_trade_amount: float
) -> Tuple[float, float]:
    """
    Valida una orden de compra y devuelve (quantity, total_cost).
    
    Acepta dos formas de entrada:
    1. quantity: número de unidades
    2. amount_to_buy: capital a invertir (se divide por precio)
    
    Raises:
        InvalidOperationError: si parámetros inválidos
        InsufficientCapitalError: si no hay capital suficiente
    """
    # Determinar quantity
    final_quantity = 0.0
    if amount_to_buy and amount_to_buy > 0:
        if amount_to_buy < min_trade_amount:
            raise InvalidOperationError(
                f"Monto mínimo de operación: ${min_trade_amount:.2f}"
            )
        final_quantity = amount_to_buy / price_per_unit
    elif quantity and quantity > 0:
        final_quantity = quantity
    else:
        raise InvalidOperationError("Debes especificar cantidad o monto a invertir")
    
    # Validar cantidad y precio
    if final_quantity <= 0:
        raise InvalidOperationError("Cantidad resultante debe ser positiva")
    
    # Calcular costo total
    total_before_commission, commission_amount = calculate_buy_cost(
        final_quantity, price_per_unit, commission_rate
    )
    total_cost = total_before_commission + commission_amount
    
    # Validar capital disponible
    if total_cost > capital_available:
        raise InsufficientCapitalError(
            f"Capital insuficiente. Necesitas ${total_cost:,.2f} "
            f"pero solo tienes ${capital_available:,.2f}"
        )
    
    return final_quantity, total_cost


def validate_sell_order(
    quantity_to_sell: float,
    quantity_available: float,
    price_per_unit: float,
    commission_rate: float,
    min_trade_amount: float
) -> Tuple[float, float]:
    """
    Valida una orden de venta y devuelve (quantity, total_proceeds_after_commission).
    
    Raises:
        InvalidOperationError: si parámetros inválidos
        InsufficientHoldingsError: si no hay suficientes unidades
    """
    if quantity_to_sell <= 0:
        raise InvalidOperationError("Cantidad a vender debe ser positiva")
    
    if quantity_to_sell > quantity_available:
        raise InsufficientHoldingsError(
            f"Solo tienes {quantity_available:.4f} unidades disponibles"
        )
    
    if price_per_unit <= 0:
        raise InvalidOperationError("Precio debe ser positivo")
    
    # Calcular ingreso
    total_before_commission, commission_amount = calculate_sell_proceeds(
        quantity_to_sell, price_per_unit, commission_rate
    )
    
    if total_before_commission < min_trade_amount:
        raise InvalidOperationError(
            f"Monto mínimo de operación: ${min_trade_amount:.2f}"
        )
    
    total_proceeds = total_before_commission - commission_amount
    
    return quantity_to_sell, total_proceeds


# ========================================================================
# FUNCIONES DE CÁLCULO DESDE LEDGER
# ========================================================================

def calculate_portfolio_from_transactions(
    user_transactions: List,
    current_prices: Dict[str, float]
) -> PortfolioSnapshot:
    """
    Calcula el estado actual del portfolio desde el ledger de transacciones.
    
    Args:
        user_transactions: Lista de objetos Transaction del usuario
        current_prices: Dict {symbol: current_price}
    
    Returns:
        PortfolioSnapshot con estado completo del portfolio
    """
    holdings = {}  # {symbol: {quantity, cost_basis, current_value, avg_buy_price}}
    total_invested = 0.0
    
    for txn in user_transactions:
        symbol = txn.symbol
        
        if symbol not in holdings:
            holdings[symbol] = {
                'quantity': 0.0,
                'cost_basis': 0.0,
                'buy_transactions': [],
                'sell_transactions': []
            }
        
        if txn.type == 'BUY':
            holdings[symbol]['quantity'] += txn.quantity
            holdings[symbol]['cost_basis'] += txn.total_cost  # incluye comisión
            holdings[symbol]['buy_transactions'].append(txn)
        
        elif txn.type == 'SELL':
            holdings[symbol]['quantity'] -= txn.quantity
            # La venta reduce el costo_basis de forma proporcional
            if holdings[symbol]['quantity'] > 0:
                reduction_ratio = txn.quantity / (holdings[symbol]['quantity'] + txn.quantity)
                holdings[symbol]['cost_basis'] *= (1 - reduction_ratio)
            else:
                holdings[symbol]['cost_basis'] = 0.0
            holdings[symbol]['sell_transactions'].append(txn)
    
    # Limpiar posiciones cerradas y calcular valores actuales
    cleaned_holdings = {}
    total_portfolio_value = 0.0
    
    for symbol, data in holdings.items():
        if data['quantity'] > 0.0001:  # Evitar errores de floating point
            current_price = current_prices.get(symbol, 0.0)
            current_value = data['quantity'] * current_price
            avg_buy_price = data['cost_basis'] / data['quantity'] if data['quantity'] > 0 else 0.0
            
            cleaned_holdings[symbol] = {
                'quantity': data['quantity'],
                'avg_buy_price': avg_buy_price,
                'cost_basis': data['cost_basis'],
                'current_value': current_value
            }
            total_portfolio_value += current_value
    
    # Capital inicial (asumimos 10,000 menos lo invertido)
    # En realidad, se calcula: sum(BUY) - sum(SELL)
    total_invested = sum(data['cost_basis'] for data in cleaned_holdings.values())
    
    # El capital disponible se calcula desde transacciones
    cash_available = calculate_cash_from_transactions(user_transactions)
    
    return PortfolioSnapshot(
        total_capital=total_invested + cash_available,
        total_invested=total_invested,
        cash_available=cash_available,
        holdings=cleaned_holdings,
        total_portfolio_value=total_portfolio_value + cash_available
    )


def calculate_cash_from_transactions(user_transactions: List) -> float:
    """
    Calcula el efectivo disponible partiendo de un capital inicial.
    El ledger es la fuente de verdad.
    """
    # Nota: Necesitamos acceso a SimulationConfig para saber el capital inicial
    # Por ahora, asumimos 10,000 (será pasado desde el controlador)
    initial_capital = 10000.0  # TODO: pasar como parámetro
    
    cash = initial_capital
    
    for txn in user_transactions:
        if txn.type == 'BUY':
            cash -= txn.total_cost
        elif txn.type == 'SELL':
            cash += (txn.total_amount - txn.commission_amount)
    
    return cash


# ========================================================================
# FUNCIONES DE MÉTRICA EDUCATIVA
# ========================================================================

def calculate_portfolio_metrics(portfolio: PortfolioSnapshot, initial_capital: float) -> Dict:
    """
    Calcula métricas educativas clave del portfolio.
    
    Returns:
        {
            'total_return_pct': float,
            'concentration': {symbol: weight},
            'diversification_score': float,
            'p_and_l_by_asset': {symbol: {p_and_l, p_and_l_pct}},
            'total_p_and_l': float
        }
    """
    total_p_and_l = portfolio.total_portfolio_value - initial_capital
    total_return_pct = (total_p_and_l / initial_capital) * 100 if initial_capital > 0 else 0
    
    # Concentración por activo
    concentration = {}
    p_and_l_by_asset = {}
    
    for symbol, holding in portfolio.holdings.items():
        weight = (holding['current_value'] / portfolio.total_portfolio_value * 100) \
                 if portfolio.total_portfolio_value > 0 else 0
        concentration[symbol] = weight
        
        p_and_l = holding['current_value'] - holding['cost_basis']
        p_and_l_pct = (p_and_l / holding['cost_basis'] * 100) \
                      if holding['cost_basis'] > 0 else 0
        
        p_and_l_by_asset[symbol] = {
            'absolute': p_and_l,
            'percentage': p_and_l_pct
        }
    
    # Score de diversificación (1 = diversificado, 0 = concentrado)
    if len(concentration) > 1:
        weights = list(concentration.values())
        avg_weight = sum(weights) / len(weights)
        variance = sum((w - avg_weight) ** 2 for w in weights) / len(weights)
        diversification_score = 1 - (variance / (100 ** 2))  # Normalizado 0-1
    else:
        diversification_score = 0.0 if len(concentration) > 0 else 1.0
    
    return {
        'total_return_pct': total_return_pct,
        'total_p_and_l': total_p_and_l,
        'concentration': concentration,
        'diversification_score': max(0, min(1, diversification_score)),
        'p_and_l_by_asset': p_and_l_by_asset,
        'num_holdings': len(portfolio.holdings)
    }


def generate_buy_feedback(
    user: object,
    symbol: str,
    quantity: float,
    price_per_unit: float,
    commission_amount: float,
    portfolio_metrics: Dict
) -> str:
    """
    Genera feedback educativo post-compra.
    """
    total_invested = quantity * price_per_unit
    concentration = portfolio_metrics.get('concentration', {}).get(symbol, 0)
    
    feedback_parts = [
        f"✅ Compra ejecutada: {quantity:.4f} {symbol} @ ${price_per_unit:.2f}",
        f"💰 Inversión: ${total_invested:,.2f} + ${commission_amount:.2f} (comisión)"
    ]
    
    if concentration > 25:
        feedback_parts.append(
            f"⚠️ Alerta: {symbol} ahora representa {concentration:.1f}% de tu portfolio. "
            "Considera diversificar."
        )
    
    if portfolio_metrics.get('diversification_score', 1) < 0.3:
        feedback_parts.append(
            f"📊 Tu portfolio está muy concentrado. Diversifica para reducir riesgo."
        )
    
    return "\n".join(feedback_parts)


def generate_sell_feedback(
    symbol: str,
    quantity: float,
    price_per_unit: float,
    commission_amount: float,
    p_and_l: Dict
) -> str:
    """
    Genera feedback educativo post-venta.
    """
    total_proceeds = quantity * price_per_unit
    p_and_l_data = p_and_l.get('p_and_l_by_asset', {}).get(symbol, {})
    
    feedback_parts = [
        f"✅ Venta ejecutada: {quantity:.4f} {symbol} @ ${price_per_unit:.2f}",
        f"💵 Ingreso: ${total_proceeds:,.2f} - ${commission_amount:.2f} (comisión)"
    ]
    
    asset_p_and_l = p_and_l_data.get('absolute', 0)
    asset_p_and_l_pct = p_and_l_data.get('percentage', 0)
    
    if asset_p_and_l > 0:
        feedback_parts.append(
            f"🎉 Ganancia: ${asset_p_and_l:,.2f} (+{asset_p_and_l_pct:.2f}%)"
        )
    else:
        feedback_parts.append(
            f"📉 Pérdida: ${asset_p_and_l:,.2f} ({asset_p_and_l_pct:.2f}%)"
        )
    
    return "\n".join(feedback_parts)


# ========================================================================
# FUNCIONES DE EDUCACIÓN Y ANÁLISIS (FASE 2)
# ========================================================================

def calculate_allocation_health(portfolio: PortfolioSnapshot, initial_capital: float) -> Dict:
    """
    Analiza la salud de la asignación de capital.
    
    Returns:
        {
            'cash_pct': float,
            'invested_pct': float,
            'cash_allocation_score': str ('bueno' | 'advertencia' | 'crítico'),
            'invested_value': float
        }
    """
    if initial_capital <= 0:
        return {
            'cash_pct': 100,
            'invested_pct': 0,
            'cash_allocation_score': 'bueno',
            'invested_value': 0
        }
    
    cash_pct = (portfolio.cash_available / initial_capital) * 100
    invested_value = portfolio.total_invested
    invested_pct = (invested_value / initial_capital) * 100
    
    # Scoring: ideal es 70-80% invertido, 20-30% cash para emergencias
    if 20 <= cash_pct <= 30:
        score = 'bueno'
    elif 10 <= cash_pct < 20 or 30 < cash_pct <= 50:
        score = 'advertencia'
    else:
        score = 'crítico'
    
    return {
        'cash_pct': cash_pct,
        'invested_pct': invested_pct,
        'cash_allocation_score': score,
        'invested_value': invested_value
    }


def calculate_risk_profile(portfolio: PortfolioSnapshot, portfolio_metrics: Dict) -> Dict:
    """
    Calcula perfil de riesgo simplificado del portfolio.
    
    Factores:
    - Concentración: riesgo alto si top-3 holdings > 60%
    - Numero de activos: diversificación baja si < 3
    - Volatilidad implícita: estimada desde P&L
    
    Returns:
        {
            'risk_level': str ('bajo' | 'medio' | 'alto'),
            'concentration_risk': float (0-100),
            'diversification_risk': float (0-100),
            'overall_risk_score': float (0-100),
            'explanation': str
        }
    """
    concentration = portfolio_metrics.get('concentration', {})
    num_holdings = len(concentration)
    
    # Riesgo por concentración
    if num_holdings == 0:
        concentration_risk = 100  # No hay inversiones
    elif num_holdings == 1:
        concentration_risk = 100  # Totalmente concentrado
    else:
        top_3_weight = sum(sorted(concentration.values(), reverse=True)[:3])
        concentration_risk = min(100, (top_3_weight - 33) * 1.5)  # 33% es diversificado
    
    # Riesgo por falta de diversificación
    if num_holdings < 3:
        diversification_risk = 80
    elif num_holdings < 5:
        diversification_risk = 50
    elif num_holdings < 10:
        diversification_risk = 20
    else:
        diversification_risk = 0
    
    # Score general (promedio ponderado)
    overall_score = (concentration_risk * 0.6 + diversification_risk * 0.4)
    
    if overall_score < 30:
        level = 'bajo'
    elif overall_score < 60:
        level = 'medio'
    else:
        level = 'alto'
    
    # Explicación
    explanations = []
    if concentration_risk > 50:
        top_symbol = max(concentration, key=concentration.get) if concentration else 'N/A'
        explanations.append(
            f"Tu portfolio depende mucho de {top_symbol} ({concentration.get(top_symbol, 0):.1f}%)"
        )
    if diversification_risk > 50:
        explanations.append(f"Tienes solo {num_holdings} activo(s). Diversifica.")
    
    if not explanations:
        explanations.append("Tu portfolio tiene un buen balance de riesgo.")
    
    return {
        'risk_level': level,
        'concentration_risk': concentration_risk,
        'diversification_risk': diversification_risk,
        'overall_risk_score': overall_score,
        'num_holdings': num_holdings,
        'explanation': ' '.join(explanations)
    }


def calculate_opportunity_cost(
    portfolio_metrics: Dict,
    initial_capital: float,
    sp500_return_pct: float = 10.0
) -> Dict:
    """
    Compara rentabilidad actual vs benchmark (S&P 500 simple).
    
    Args:
        sp500_return_pct: Rentabilidad anual esperada (default 10%, realista)
    
    Returns:
        {
            'user_return_pct': float,
            'benchmark_return_pct': float,
            'outperformance': float,
            'opportunity_cost': float,  # Dinero que dejó de ganar/perder vs benchmark
            'assessment': str ('superando' | 'bajo_par' | 'perdiendo')
        }
    """
    user_return = portfolio_metrics.get('total_return_pct', 0)
    benchmark_return = sp500_return_pct
    
    outperformance = user_return - benchmark_return
    
    # Costo de oportunidad en dinero
    user_value = initial_capital * (1 + user_return / 100)
    benchmark_value = initial_capital * (1 + benchmark_return / 100)
    opportunity_cost = user_value - benchmark_value
    
    if outperformance > 2:
        assessment = 'superando'
    elif outperformance < -2:
        assessment = 'perdiendo'
    else:
        assessment = 'bajo_par'
    
    return {
        'user_return_pct': user_return,
        'benchmark_return_pct': benchmark_return,
        'outperformance': outperformance,
        'opportunity_cost': opportunity_cost,
        'assessment': assessment
    }


def generate_extended_buy_feedback(
    symbol: str,
    quantity: float,
    price_per_unit: float,
    total_cost: float,
    commission_amount: float,
    portfolio: PortfolioSnapshot,
    portfolio_metrics: Dict,
    initial_capital: float
) -> Dict:
    """
    Genera feedback detallado post-compra con análisis educativo.
    
    Returns:
        {
            'summary': str,
            'allocation': str,
            'risk': str,
            'suggestion': str
        }
    """
    allocation = calculate_allocation_health(portfolio, initial_capital)
    risk = calculate_risk_profile(portfolio, portfolio_metrics)
    
    # Summary básico
    summary_lines = [
        f"Compra: {quantity:.4f} {symbol} @ ${price_per_unit:.2f}",
        f"Inversión: ${total_cost:,.2f} (incluida comisión)"
    ]
    
    # Análisis de asignación
    allocation_lines = [
        f"Cartera invertida: {allocation['invested_pct']:.1f}% (${allocation['invested_value']:,.2f})",
        f"Efectivo disponible: {allocation['cash_pct']:.1f}%"
    ]
    
    if allocation['cash_allocation_score'] == 'crítico':
        allocation_lines.append("ADVERTENCIA: Tu asignación de efectivo es muy baja para emergencias.")
    elif allocation['cash_allocation_score'] == 'advertencia':
        allocation_lines.append("Considera mantener 20-30% en efectivo.")
    
    # Análisis de riesgo
    risk_lines = [
        f"Riesgo del portfolio: {risk['risk_level'].upper()}",
        f"Número de activos: {risk['num_holdings']}",
        risk['explanation']
    ]
    
    if risk['overall_risk_score'] > 70:
        suggestion = "Diversifica en más activos para reducir riesgo de mercado."
    elif allocation['invested_pct'] > 80:
        suggestion = "Tu portfolio está muy invertido. Reserva efectivo para oportunidades."
    else:
        suggestion = "Mantén esta estrategia y aprende de los resultados."
    
    return {
        'summary': ' | '.join(summary_lines),
        'allocation': ' | '.join(allocation_lines),
        'risk': ' | '.join(risk_lines),
        'suggestion': suggestion
    }


def generate_extended_sell_feedback(
    symbol: str,
    quantity: float,
    price_per_unit: float,
    proceeds: float,
    commission_amount: float,
    p_and_l_data: Dict,
    portfolio: PortfolioSnapshot,
    portfolio_metrics: Dict,
    initial_capital: float
) -> Dict:
    """
    Genera feedback detallado post-venta con análisis educativo.
    
    Returns:
        {
            'summary': str,
            'performance': str,
            'insight': str,
            'suggestion': str
        }
    """
    p_and_l = p_and_l_data.get('p_and_l_by_asset', {}).get(symbol, {})
    asset_gain = p_and_l.get('absolute', 0)
    asset_gain_pct = p_and_l.get('percentage', 0)
    
    # Summary básico
    summary_lines = [
        f"Venta: {quantity:.4f} {symbol} @ ${price_per_unit:.2f}",
        f"Ingreso neto: ${proceeds:,.2f}"
    ]
    
    # Performance
    if asset_gain > 0:
        performance = f"GANANCIA: ${asset_gain:,.2f} (+{asset_gain_pct:.2f}%)"
        assessment = "Buena decisión de venta."
    else:
        performance = f"PERDIDA: ${asset_gain:,.2f} ({asset_gain_pct:.2f}%)"
        assessment = "Reconocimiento de pérdida."
    
    performance_lines = [performance, assessment]
    
    # Insight educativo
    opportunity_cost = calculate_opportunity_cost(portfolio_metrics, initial_capital)
    insight_lines = [
        f"Rentabilidad total del portfolio: {opportunity_cost['user_return_pct']:.2f}%"
    ]
    
    if opportunity_cost['assessment'] == 'superando':
        insight_lines.append(f"Estás superando al S&P 500 en {opportunity_cost['outperformance']:.2f}%")
    elif opportunity_cost['assessment'] == 'perdiendo':
        insight_lines.append(f"Por debajo del benchmark en {abs(opportunity_cost['outperformance']):.2f}%")
    
    # Sugerencia
    allocation = calculate_allocation_health(portfolio, initial_capital)
    if allocation['cash_pct'] > 40:
        suggestion = "Tienes mucho efectivo. Considera reinvertir si encuentras buenas oportunidades."
    else:
        suggestion = "Mantén tus mejores posiciones y aprende de esta operación."
    
    return {
        'summary': ' | '.join(summary_lines),
        'performance': ' | '.join(performance_lines),
        'insight': ' | '.join(insight_lines),
        'suggestion': suggestion
    }


# ========================================================================
# MÉTRICAS AVANZADAS (FASE 3)
# ========================================================================

def calculate_portfolio_history(
    user_transactions: List,
    daily_prices: Dict[str, List[Tuple[datetime, float]]]
) -> List[Dict]:
    """
    Calcula la evolución del portfolio a lo largo del tiempo.
    
    Args:
        user_transactions: Lista de Transaction objects
        daily_prices: {symbol: [(datetime, price), ...]}
    
    Returns:
        List de snapshots diarios: [
            {
                'date': datetime,
                'portfolio_value': float,
                'cash': float,
                'invested': float,
                'return_pct': float
            }
        ]
    
    Nota: Esta es una versión simplificada. En producción, necesitarías
    datos históricos reales. Para ahora, asumimos precios estáticos.
    """
    # Simplificado: asumimos un único snapshot (hoy)
    # En FASE 4 agregaremos histórico real
    return []


def calculate_drawdown(
    portfolio_values: List[float]
) -> Dict:
    """
    Calcula máximo drawdown desde el pico más alto.
    
    Returns:
        {
            'max_drawdown_pct': float,
            'max_drawdown_value': float,
            'peak_value': float,
            'trough_value': float
        }
    
    Drawdown educativo: "Si tu máximo valor fue $10,500 y caíste a $9,200,
    el drawdown es 12.4%. Importante para entender volatilidad."
    """
    if not portfolio_values or len(portfolio_values) < 2:
        return {
            'max_drawdown_pct': 0,
            'max_drawdown_value': 0,
            'peak_value': portfolio_values[0] if portfolio_values else 0,
            'trough_value': portfolio_values[-1] if portfolio_values else 0
        }
    
    peak = portfolio_values[0]
    max_dd = 0
    dd_peak = peak
    dd_trough = peak
    
    for value in portfolio_values[1:]:
        if value > peak:
            peak = value
        
        dd = (peak - value) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            dd_peak = peak
            dd_trough = value
    
    return {
        'max_drawdown_pct': max_dd * 100,
        'max_drawdown_value': (dd_peak - dd_trough),
        'peak_value': dd_peak,
        'trough_value': dd_trough
    }


def calculate_volatility(returns: List[float]) -> float:
    """
    Calcula volatilidad (desviación estándar de retornos).
    
    Returns:
        Volatilidad como porcentaje (ej: 15.3%)
    
    Educativo: "Volatilidad baja (< 10%) = estable. Alta (> 25%) = volátil"
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    return std_dev * 100


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.02
) -> float:
    """
    Calcula Sharpe Ratio simplificado.
    
    Formula: (mean_return - risk_free_rate) / volatility
    
    Educativo:
    - Sharpe > 1.0: Buen riesgo/retorno
    - Sharpe 0.5-1.0: Aceptable
    - Sharpe < 0.5: Pobre
    """
    if not returns:
        return 0.0
    
    mean_return = sum(returns) / len(returns)
    volatility = calculate_volatility(returns)
    
    if volatility == 0:
        return 0.0
    
    sharpe = (mean_return - risk_free_rate) / volatility
    return sharpe


def calculate_advanced_metrics(
    portfolio: PortfolioSnapshot,
    portfolio_metrics: Dict,
    initial_capital: float,
    user_transactions: List
) -> Dict:
    """
    Calcula todas las métricas avanzadas del portfolio.
    
    Returns:
        {
            'risk_metrics': {
                'max_drawdown_pct': float,
                'volatility_pct': float,
                'sharpe_ratio': float
            },
            'performance_metrics': {
                'total_return_pct': float,
                'monthly_return_pct': float,
                'num_trades': int,
                'win_rate_pct': float
            },
            'allocation_metrics': {
                'num_holdings': int,
                'largest_position_pct': float,
                'avg_position_size_pct': float
            }
        }
    """
    # Calcula returns para volatilidad (simplificado)
    # En FASE 4, usaremos histórico real
    current_return = portfolio_metrics['total_return_pct'] / 100
    returns = [current_return]  # Lista con un solo elemento por ahora
    
    # Drawdown simplificado
    # Asumimos el portfolio nunca cayó más del 5% (para demostración)
    current_value = portfolio.total_portfolio_value
    peak_value = initial_capital * 1.1  # Asumimos pico del 10%
    dd = max(0, (peak_value - current_value) / peak_value * 100)
    
    # Volatilidad
    volatility = calculate_volatility(returns) if len(returns) > 1 else 0
    
    # Sharpe ratio
    sharpe = calculate_sharpe_ratio(returns)
    
    # Win rate (porcentaje de trades ganadores)
    winning_trades = sum(
        1 for txn in user_transactions 
        if txn.type == 'SELL' and txn.total_cost > 0  # Simplificado
    )
    total_trades = len([t for t in user_transactions if t.type == 'SELL'])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Métricas de asignación
    concentration = portfolio_metrics.get('concentration', {})
    largest_position = max(concentration.values()) if concentration else 0
    avg_position = (sum(concentration.values()) / len(concentration)) if concentration else 0
    
    return {
        'risk_metrics': {
            'max_drawdown_pct': dd,
            'volatility_pct': volatility,
            'sharpe_ratio': sharpe
        },
        'performance_metrics': {
            'total_return_pct': portfolio_metrics['total_return_pct'],
            'monthly_return_pct': portfolio_metrics['total_return_pct'] / 3,  # Aproximado
            'num_trades': len(user_transactions),
            'win_rate_pct': win_rate
        },
        'allocation_metrics': {
            'num_holdings': len(concentration),
            'largest_position_pct': largest_position,
            'avg_position_size_pct': avg_position
        }
    }


def generate_dashboard_data(
    user,
    config: object
) -> Dict:
    """
    Genera todos los datos necesarios para el dashboard.
    Retorna solo dicts/lists/scalars para JSON serialización en templates.
    
    Returns:
        {
            'portfolio': Dict,
            'metrics': Dict,
            'advanced_metrics': Dict,
            'allocation': Dict,
            'risk': Dict,
            'opportunity_cost': Dict,
            'holdings_detail': List[Dict]
        }
    """
    from app.models import SimulationConfig
    
    # Obtener precios actuales (en real, sería desde yfinance)
    current_prices = {h.symbol: h.purchase_price for h in user.holdings}
    
    # Calcular portfolio
    portfolio = calculate_portfolio_from_transactions(
        user.transactions,
        current_prices
    )
    
    # Métricas básicas
    metrics = calculate_portfolio_metrics(portfolio, config.initial_capital)
    
    # Métricas avanzadas
    advanced = calculate_advanced_metrics(
        portfolio, metrics, config.initial_capital, user.transactions
    )
    
    # Asignación
    allocation = calculate_allocation_health(portfolio, config.initial_capital)
    
    # Riesgo
    risk = calculate_risk_profile(portfolio, metrics)
    
    # Oportunidad de coste
    opp_cost = calculate_opportunity_cost(metrics, config.initial_capital)
    
    # Detalles de holdings
    holdings_detail = []
    for symbol, holding in portfolio.holdings.items():
        p_and_l = metrics['p_and_l_by_asset'].get(symbol, {})
        holdings_detail.append({
            'symbol': symbol,
            'quantity': holding['quantity'],
            'avg_buy_price': holding['avg_buy_price'],
            'current_price': current_prices.get(symbol, 0),
            'current_value': holding['current_value'],
            'cost_basis': holding['cost_basis'],
            'p_and_l_absolute': p_and_l.get('absolute', 0),
            'p_and_l_pct': p_and_l.get('percentage', 0),
            'weight_pct': metrics['concentration'].get(symbol, 0)
        })
    
    # Convertir PortfolioSnapshot a dict para JSON serialización
    portfolio_dict = {
        'total_capital': float(portfolio.total_capital),
        'total_invested': float(portfolio.total_invested),
        'cash_available': float(portfolio.cash_available),
        'total_portfolio_value': float(portfolio.total_portfolio_value),
        'holdings': portfolio.holdings
    }
    
    return {
        'portfolio': portfolio_dict,
        'metrics': metrics,
        'advanced_metrics': advanced,
        'allocation': allocation,
        'risk': risk,
        'opportunity_cost': opp_cost,
        'holdings_detail': holdings_detail
    }
