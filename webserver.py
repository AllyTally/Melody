import traceback
import time
import discord
import asyncio
from client import bot
import logs

from aiohttp import web


routes = web.RouteTableDef()

@routes.get('/api/list_servers/')
async def hello(request):
    return web.json_response({"guilds": dict([(str(x.id), [x.name,str(x.icon_url_as(format="png"))]) for x in bot.guilds])})

app = web.Application()
app.add_routes(routes)

async def start_server():
    logs.info("Starting web server...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 2064)
    await site.start()
