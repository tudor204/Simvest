from flask import Blueprint, render_template, url_for, flash, redirect
from flask_login import login_required, current_user
from app.market_service import fetch_live_market_data
from app.models import Holding, Transaction, db
from datetime import datetime, timedelta
from sqlalchemy import desc
import pandas as pd
import yfinance as yf 
from app import app

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    try:
        # 1. Obtener datos de la base de datos
        holdings = Holding.query.filter_by(user_id=current_user.id).all()
        
        transaction_history = Transaction.query.filter_by(user_id=current_user.id)\
                                         .order_by(desc(Transaction.timestamp))\
                                         .limit(20).all()

        # 2. Obtener datos del mercado en vivo
        try:
            _, products_dict = fetch_live_market_data() 
        except Exception as e:
            app.logger.error(f"Error fetching market data: {e}")
            products_dict = {}

        valor_portafolio = 0
        portafolio_data = []
        total_invested = 0  # Para cálculo más preciso de P&L

        # 3. Calcular valores actuales
        for h in holdings:
            symbol = h.symbol
            market_info = products_dict.get(symbol, {})
            
            current_price = market_info.get('price', h.purchase_price)
            try:
                current_price = float(current_price)
            except (TypeError, ValueError):
                current_price = h.purchase_price

            current_value = current_price * h.quantity
            invested_value = h.purchase_price * h.quantity
            gain_loss = current_value - invested_value
            
            # Protección contra división por cero
            if invested_value > 0:
                percent_change = (gain_loss / invested_value) * 100
            else:
                percent_change = 0.0

            valor_portafolio += current_value
            total_invested += invested_value

            portafolio_data.append({
                'id': h.id,
                'symbol': h.symbol,
                'name': market_info.get('name', h.name),
                'quantity': h.quantity,
                'purchase_price': h.purchase_price,
                'current_price': current_price,
                'gain_loss': gain_loss,
                'percent_change': percent_change,
                'total_value': current_value,
                'invested_value': invested_value
            })

        current_capital = float(current_user.capital)
        total_capital = current_capital + valor_portafolio
        
        # Cálculo de P&L global más preciso
        initial_capital_value = 10000.00  # Considerar hacer esto configurable
        overall_pnl = total_capital - initial_capital_value
        overall_pnl_pct = (overall_pnl / initial_capital_value * 100) if initial_capital_value > 0 else 0.0

        # 4. Datos históricos para el gráfico
        portfolio_history = get_portfolio_history(portafolio_data, current_capital)

        return render_template(
            'Dashboard/dashboard.html',
            current_capital=current_capital,
            valor_portafolio=valor_portafolio,
            total_capital=total_capital,
            portafolio=portafolio_data,
            portfolio_history=portfolio_history,
            transaction_history=transaction_history,
            overall_pnl=overall_pnl,
            overall_pnl_pct=overall_pnl_pct,
            total_invested=total_invested  # Nuevo: valor total invertido
        )
        
    except Exception as e:
        app.logger.error(f"Error in dashboard: {e}")
        flash('Error al cargar el dashboard. Por favor, intenta nuevamente.', 'error')
        return render_template('Dashboard/dashboard.html', error=True)

def get_portfolio_history(portafolio_data, current_capital, num_days=4):
    """Función auxiliar para obtener datos históricos del portafolio"""
    portfolio_history = {"labels": [], "values": []}
    
    # Generar etiquetas de fechas
    date_labels = []
    for i in range(num_days):
        day = datetime.now() - timedelta(days=num_days - 1 - i)
        date_labels.append(day.strftime("%Y-%m-%d"))
    portfolio_history["labels"] = date_labels

    if not portafolio_data:
        portfolio_history["values"] = [round(current_capital, 2)] * num_days
        return portfolio_history

    symbols_in_portfolio = [item['symbol'] for item in portafolio_data]
    quantity_map = {item['symbol']: item['quantity'] for item in portafolio_data}

    try:
        start_date = (datetime.now() - timedelta(days=num_days)).strftime('%Y-%m-%d')
        
        hist_data = yf.download(
            symbols_in_portfolio, 
            start=start_date, 
            interval="1d",
            progress=False
        )

        daily_portfolio_values = [0.0] * num_days
        
        if not hist_data.empty:
            prices_df = hist_data['Close'].tail(num_days)

            for symbol in symbols_in_portfolio:
                quantity = quantity_map[symbol]
                
                if len(symbols_in_portfolio) == 1:
                    price_series = prices_df
                elif symbol in prices_df.columns:
                    price_series = prices_df[symbol]
                else:
                    continue
                    
                asset_daily_values = (price_series * quantity).tolist()
                                    
                if len(asset_daily_values) < num_days:
                    missing_days = num_days - len(asset_daily_values)
                    asset_daily_values = ([asset_daily_values[0]] * missing_days) + asset_daily_values

                for i in range(num_days):
                    if i < len(asset_daily_values):
                        daily_portfolio_values[i] += asset_daily_values[i]

            portfolio_history["values"] = [
                round(current_capital + daily_value, 2) for daily_value in daily_portfolio_values
            ]
        else:
            current_total = sum(item['total_value'] for item in portafolio_data)
            portfolio_history["values"] = [round(current_capital + current_total, 2)] * num_days

    except Exception as e:
        app.logger.error(f"Error in get_portfolio_history: {e}")
        current_total = sum(item['total_value'] for item in portafolio_data)
        portfolio_history["values"] = [round(current_capital + current_total, 2)] * num_days
    
    return portfolio_history

@dashboard_bp.route('/history')
@login_required
def history():
    """Muestra el historial completo de transacciones"""
    all_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                     .order_by(desc(Transaction.timestamp))\
                                     .all()

    return render_template('Dashboard/history.html', transactions=all_transactions)