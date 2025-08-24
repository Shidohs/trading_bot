# Configuración del sistema de trading
DEBUG = True  # Cambiar a False para modo producción

# Configuración de trading
SYMBOLS = ["R_10", "R_25", "R_50", "R_75", "R_100"]
INITIAL_BALANCE = 10000.0

# Configuración de riesgo
RISK_PER_TRADE = 0.003  # 0.3% del balance
DAILY_TP_PCT = 0.10  # 10% take profit diario
DAILY_DD_PCT = 0.12  # 12% drawdown diario
MAX_OPEN_PER_SYMBOL = 2
MAX_OPEN_TOTAL = 8

# Configuración de estrategia
STRATEGY_THRESHOLD = 0.78  # 78% score mínimo para entrar
ML_ENABLED = True  # Habilitar machine learning
CORRELATION_THRESHOLD = 0.8  # Umbral de correlación

# Configuración de WebSocket
WS_RECONNECT_DELAY = 30  # Segundos entre reconexiones
WS_PING_INTERVAL = 20  # Segundos entre pings
WS_PING_TIMEOUT = 10  # Timeout de ping

# Configuración de backtesting
BACKTEST_COMMISSION = 0.001  # 0.1% comisión
BACKTEST_SLIPPAGE = 0.0005  # 0.05% slippage

# Configuración de logging
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOG_FILE = "logs/trading_bot.log"
ORDERS_CSV = "logs/orders.csv"

# Configuración ML
ML_MODEL_PATH = "models/trading_model.joblib"
ML_TRAINING_DATA = "data/historical_data.csv"
