# Bot Deriv Pro - Plataforma de Trading Algorítmico

Plataforma profesional de trading algorítmico con análisis técnico avanzado, backtesting, machine learning asistencial y gestión de riesgo adaptativa.

## ⚠️ Advertencia Legal y de Riesgo

**NO SE GARANTIZAN GANANCIAS** - Este sistema es una herramienta educativa y de investigación. El rendimiento pasado no predice resultados futuros. El trading conlleva riesgos significativos de pérdida de capital.

**Solo opere con capital que pueda permitirse perder.** Cualquier afirmación no verificada está marcada como `[No verificado]` o `[Inferencia]`.

## 🚀 Características Principales

### Análisis Técnico Avanzado

- ✅ **MTF Real (1m/5m/15m)**: Construcción de timeframe múltiples desde datos 1m
- ✅ **Divergencias RSI/MACD**: Detección robusta de divergencias bullish/bearish
- ✅ **Volumen Sintético**: Proxy de volumen usando ATR y características de velas
- ✅ **S/R Dinámicos**: Clustering de precios para niveles de soporte/resistencia
- ✅ **Scoring Ponderado**: Modelo de scoring con pesos configurables

### Machine Learning Asistencial

- ✅ **Decision Tree Light**: Modelo de árbol de decisiones para asistencia
- ✅ **Ensembling**: Combinación de scoring tradicional + probabilidad ML
- ✅ **Persistencia**: Guardado/carga de modelos entrenados

### Gestión de Riesgo Inteligente

- ✅ **Stake Dinámico**: 0.3% del balance por trade (configurable)
- ✅ **Drawdown Adaptativo**: Reducción de stake tras rachas negativas
- ✅ **Límites Diarios**: TP 10% / DD 12% diarios automáticos
- ✅ **Control Correlación**: Prevención de trades altamente correlacionados

### Backtesting Profesional

- ✅ **Slippage & Comisiones**: Simulación realista de costos de trading
- ✅ **Walk-Forward**: Validación walk-forward con retraining periódico
- ✅ **Métricas Completas**: Sharpe, drawdown, win rate, profit factor
- ✅ **Export CSV/JSON**: Resultados detallados para análisis

### Robustez Operacional

- ✅ **WebSocket Reintentos**: Reconexión automática con backoff exponencial
- ✅ **Manejo Excepciones**: Todas las operaciones I/O con try/catch
- ✅ **Logging Estructurado**: Registro de órdenes y eventos
- ✅ **Variables Entorno**: Credenciales seguras via `.env`

## 📦 Instalación

1. **Clonar el repositorio**:

```bash
git clone <repository-url>
cd trading_bot
```

2. **Instalar dependencias**:

```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:

```bash
cp .env.example .env
# Editar .env con tus credenciales Deriv
APP_ID=tu_app_id
TOKEN=tu_token
```

## ⚙️ Configuración

### Modos de Operación

- **SIMULATION_MODE**: Modo simulación (sin órdenes reales)
- **ML_DISABLED**: Deshabilitar ML (solo scoring tradicional)
- **BACKTEST_MODE**: Ejecutar backtesting histórico

### Parámetros Configurables

- `RISK_PER_TRADE`: Porcentaje de riesgo por trade (default: 0.003)
- `DAILY_TP_PCT`: Take profit diario (default: 0.10)
- `DAILY_DD_PCT`: Drawdown diario (default: 0.12)
- `CORRELATION_THRESHOLD`: Umbral de correlación (default: 0.8)

## 🎯 Uso

### Ejecutar en Modo Live

```bash
python main.py
```

### Ejecutar Backtest

```bash
# Próximamente: script de backtesting
python backtest_runner.py --symbols R_10 R_25 --period 30d
```

### Entrenar Modelo ML

```bash
# Próximamente: script de entrenamiento
python train_ml.py --data historical_data.csv --output model.joblib
```

### Ejecutar Tests

```bash
python -m pytest tests/ -v
```

## 📊 Métricas de Performance

El sistema calcula y monitoriza:

- **Net PnL**: Profit & Loss neto
- **Sharpe Ratio**: Retorno ajustado por riesgo
- **Max Drawdown**: Máxima pérdida desde peak
- **Win Rate**: Porcentaje de trades ganadores
- **Profit Factor**: Ratio ganancias/pérdidas
- **Precision/Recall**: Métricas de clasificación

## 🏗️ Arquitectura

```
trading_bot/
├── core/
│   ├── websocket_client.py   # Conexión Deriv WS
│   ├── ohlc_buffers.py       # MTF OHLC buffers
│   ├── features.py           # Cálculo de indicadores
│   ├── strategy.py           # Scoring y reglas
│   ├── ml_adapter.py         # Integración ML
│   ├── risk.py              # Gestión de riesgo
│   ├── correlation.py        # Control correlación
│   ├── backtester.py         # Backtesting
│   └── orders.py            # Gestión órdenes
├── utils/
│   ├── indicators.py         # Indicadores técnicos
│   └── logger.py            # Logging estructurado
├── main.py                  # Entrypoint principal
└── requirements.txt         # Dependencias
```

## 🧪 Testing

### Tests Unitarios

```bash
python -m pytest tests/test_indicators.py
python -m pytest tests/test_backtester.py
python -m pytest tests/test_strategy.py
```

### CI/CD

Workflow GitHub Actions incluido para:

- ✅ Linting (flake8, black)
- ✅ Tests unitarios
- ✅ Backtest sample
- ✅ Security scanning

## 📈 Resultados y Reportes

### Logs de Órdenes

- `logs/orders.csv`: Historial completo de trades
- `logs/session_report.txt`: Resumen de sesión
- `backtest_results/`: Resultados de backtesting

### Formatos de Exportación

- CSV: Trades detallados y equity curve
- JSON: Métricas de performance
- PNG: Gráficos de equity curve (opcional)

## 🔧 Troubleshooting

### Errores Comunes

1. **WebSocket desconectado**: Reintento automático cada 30s
2. **ML no disponible**: Sistema funciona en modo scoring tradicional
3. **Balance insuficiente**: Pausa automática hasta próximo día

### Monitorización

- Console Rich con estado en tiempo real
- Logs estructurados para debugging
- Alertas de correlación y riesgo

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Distribuido bajo licencia MIT. Ver `LICENSE` para más información.

## 🆘 Soporte

Para issues y preguntas:

- Abrir issue en GitHub
- Revisar documentación en `docs/`
- Consultar métricas de backtest

---

**Disclaimer**: Este software se proporciona "tal cual", sin garantías de ningún tipo. El usuario asume todo el riesgo asociado con su uso. Nunca opere con capital que no pueda permitirse perder.
