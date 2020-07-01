import os

# Telegram token
TGBOT_TOKEN = os.getenv('TGBOT_TOKEN')

# Telegram admins ID
TG_ADMINS_ID = [int(ID) for ID in os.getenv('TG_ADMINS_ID').split()]

# Telegram webhook
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PORT = os.getenv('WEBHOOK_PORT')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
WEBHOOK_SSL_CERT = os.getenv('WEBHOOK_SSL_CERT')
WEBHOOK_SSL_PRIV = os.getenv('WEBHOOK_SSL_PRIV')

# Webhost
WEBAPP_HOST = os.getenv('WEBAPP_HOST')
WEBAPP_PORT = os.getenv('WEBAPP_PORT')

# Postgressql
PG_HOST = os.getenv('PG_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
