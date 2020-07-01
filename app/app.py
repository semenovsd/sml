import ssl

from aiogram.utils.executor import start_webhook

from config import (TG_ADMINS_ID, WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_HOST,
                    WEBHOOK_PORT, WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV,
                    WEBHOOK_PATH)
from database import create_db
from load_all import bot

WEBHOOK_URL = f'{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}'


async def on_startup(self):
    await create_db()

    # Check webhook
    webhook = await bot.get_webhook_info()

    # If URL is bad
    if webhook.url != WEBHOOK_URL:
        # If URL doesnt match current - remove webhook
        if not webhook.url:
            await bot.delete_webhook()

    # Set new URL for webhook
    await bot.set_webhook(WEBHOOK_URL, certificate=open(WEBHOOK_SSL_CERT, 'rb').read())

    # Send message to admin
    await bot.send_message(TG_ADMINS_ID[0], "Я запущен!")


async def on_shutdown(self):
    # insert code here to run it before shutdown

    # Send message to admin
    await bot.send_message(TG_ADMINS_ID[0], "Я выключен!")


if __name__ == '__main__':
    # forwarding dp from handlers
    from handlers_main import dp

    # Generate SSL context.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        ssl_context=context
    )
