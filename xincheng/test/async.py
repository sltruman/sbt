import asyncio

loop = asyncio.get_event_loop()

async def finish():
    print('finish')
    loop.stop()

async def sort():
    print('sort')
    asyncio.ensure_future(finish())

async def place():
    print('place')
    asyncio.ensure_future(sort())


async def locate():
    print('locate')
    asyncio.ensure_future(place())

asyncio.ensure_future(locate())
loop.run_forever()

