import typer
from typing import Annotated
from dp import dispatcher
from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
import redis.asyncio as redis


async def main(bot: Bot, redis_url: str) -> None:
    async with redis.from_url(redis_url) as redis_client:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(
            bot,
            redis_client=redis_client,
        )


def cli_main(
    api_token: Annotated[str, typer.Option(help="Telegram bot API token")],
    redis_url: Annotated[str, typer.Option(help="Redis DSN")],
) -> None:
    bot = Bot(token=api_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    asyncio.run(main(bot, redis_url))


if __name__ == "__main__":
    typer.run(cli_main)
