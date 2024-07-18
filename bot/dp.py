from aiogram.filters.command import Command, CommandStart
from aiogram.types import Message
from aiogram import Dispatcher, F
from redis.asyncio import Redis
import asyncio
import re

dispatcher = Dispatcher()


@dispatcher.message(Command("rates"))
async def command_rates(message: Message, redis_client: Redis) -> None:
    stored_currencies: list[str] = [
        bytes.decode(key) for key in await redis_client.keys()
    ]
    get_rates_tasks = map(redis_client.get, stored_currencies)
    rates = map(float, await asyncio.gather(*get_rates_tasks))
    await message.answer(
        "\n".join(
            [
                f"{currency}: {rate:.4f} RUB"
                for currency, rate in zip(stored_currencies, rates)
            ]
        )
    )


@dispatcher.message(
    F.text.regexp(
        r"^/exchange[\ ]+([A-Z]+)[\ ]+([A-Z]+)[\ ]+((?:\d+\.)?\d+)[\ ]*$"
    ).as_("matched")
)
async def command_exchange(
    message: Message,
    matched: re.Match[str],
    redis_client: Redis,
) -> None:
    start_currency: str = matched.group(1)
    end_currency: str = matched.group(2)
    amount: float = float(matched.group(3))

    if amount < 0:
        await message.reply(f"❌ Количество должно быть неотрицательным: {amount}")
        return

    ruble_per_start_rate = await redis_client.get(start_currency)
    if ruble_per_start_rate is None:
        await message.reply(
            f"❌ Не найден актуальный курс для валюты: {start_currency}"
        )
        return
    ruble_per_start_rate = float(ruble_per_start_rate)

    ruble_per_end_rate = await redis_client.get(end_currency)
    if ruble_per_end_rate is None:
        await message.reply(f"❌ Не найден актуальный курс для валюты: {end_currency}")
        return
    ruble_per_end_rate = float(ruble_per_end_rate)

    intermediate_in_rubles: float = amount * ruble_per_start_rate
    converted_in_end_currency: float = intermediate_in_rubles / ruble_per_end_rate
    await message.answer(f"{converted_in_end_currency:.4f}")


@dispatcher.message(Command("exchange"))
async def command_exchange_fallback(message: Message) -> None:
    await message.reply(
        text="❌ Команда <code>/exchange</code> принимает аргументы:\n"
        "<code>/exchange (currency_from:str) (currency_to:str) (amount:int)</code>\n"
        "где:\n"
        "<code>currency_from</code>: валюта (пример: <code>USD</code>, <code>usd</code>, <code>uSd</code>)\n"
        "<code>currency_to</code>: валюта (пример: <code>USD</code>, <code>usd</code>, <code>uSd</code>)\n"
        "<code>amount</code>: неотрицательное количество (пример: <code>10</code>)\n",
    )


@dispatcher.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(
        text="start",
    )
