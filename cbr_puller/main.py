import xml.etree
import xml.etree.ElementTree
import typer
import typing
import schedule
import redis.asyncio as redis
import asyncio
import aiohttp
import xml
import logging
import functools


def to_sync[
    **TParams
](
    func: typing.Callable[TParams, typing.Coroutine[typing.Any, typing.Any, typing.Any]]
) -> typing.Callable[TParams, None]:
    @functools.wraps(func)
    def wrapping(*args: TParams.args, **kwargs: TParams.kwargs) -> None:
        try:
            asyncio.create_task(func(*args, **kwargs))
        except Exception as exc:
            logging.error(exc)

    return wrapping


@to_sync
async def pull_rates_from_cbr(redis_client: redis.Redis, rates_url: str) -> None:
    # so the whole system won't need any dirty hacks in code in cases of RUB<->ANY exchange
    # as well as in RUB<->RUB request
    await redis_client.set("RUB", 1.0)
    async with aiohttp.ClientSession() as session:
        async with session.get(rates_url, allow_redirects=False) as request:
            body_text = await request.text("windows-1251")
            etree = xml.etree.ElementTree.fromstring(body_text)
            valutes = etree.findall("Valute")

            def extract_currency_code_and_rate(
                valute: xml.etree.ElementTree.Element,
            ) -> tuple[str, float] | str:
                char_code = valute.find("CharCode")
                if char_code is None:
                    return f"<CharCode> element was not found in one of <Valute>"
                currency_code = char_code.text
                if currency_code is None or len(currency_code) == 0:
                    return f"<CharCode> is empty"

                vunit_rate = valute.find("VunitRate")
                if vunit_rate is None:
                    return f"<VunitRate> element was not found in one of <Valute>"
                unit_per_ruble_rate = vunit_rate.text
                if unit_per_ruble_rate is None:
                    return f"<VunitRate> is empty"
                # russian decimal format uses comma instead of dot
                unit_per_ruble_rate = unit_per_ruble_rate.replace(",", ".")
                unit_per_ruble_rate = float(unit_per_ruble_rate)
                return (currency_code, unit_per_ruble_rate)

            for valute in valutes:
                match extract_currency_code_and_rate(valute):
                    case (currency_code, unit_per_ruble_rate):
                        await redis_client.set(
                            currency_code, unit_per_ruble_rate, ex=24 * 60 * 60
                        )
                    case err:
                        logging.error(err)


async def main(*, redis_url: str, rates_url: str, pull_once: bool) -> None:
    async with redis.from_url(redis_url) as client:
        if pull_once:
            pull_rates_from_cbr(redis_client=client, rates_url=rates_url)

        schedule.every().day.at("00:00:00", "Europe/Moscow").do(
            pull_rates_from_cbr,
            redis_client=client,
            rates_url=rates_url,
        )
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)


def cli_main(
    redis_url: typing.Annotated[str, typer.Option(help="Redis DSN")],
    rates_url: typing.Annotated[str, typer.Option(help="URL to CBR's XML with rates")],
    pull_once: typing.Annotated[bool, typer.Option(help="Pull once")],
) -> None:
    asyncio.run(
        main(
            redis_url=redis_url,
            rates_url=rates_url,
            pull_once=pull_once,
        )
    )


if __name__ == "__main__":
    typer.run(cli_main)
