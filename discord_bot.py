import Main

import discord
from discord.ext import commands

import os

app = commands.Bot(command_prefix='/')


@app.event
async def on_ready():
    print(f'{app.user.name} 연결성공')
    await app.change_presence(status=discord.Status.online, activity=None)


@app.command(aliases=['설정', 'a'])
async def setting(ctx, arg):
    result = ctx.author


@app.command(aliases=['설정확인', 'b'])
async def check_setting(ctx):
    print()


@app.command(aliases=['초기화', 'c'])
async def reset(ctx):
    print()


app.run(os.environ['token'])
