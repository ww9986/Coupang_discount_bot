import Main
import pymysql

import discord
from discord.ext import commands

import os

app = commands.Bot(command_prefix='/')

discord_db = pymysql.Connect(
    user='be05a28bb488d3',
    passwd=os.environ['db_passwd'],
    host='us-cdbr-east-04.cleardb.com',
    db='heroku_d34b09251865c7f',
    charset='utf8'
)
cursor = discord_db.cursor(pymysql.cursors.DictCursor)
sql = 'SELECT * FROM discord'
cursor.execute(sql)


@app.event
async def on_ready():
    print(f'{app.user.name} 연결성공')
    await app.change_presence(status=discord.Status.online, activity=None)


@app.command(aliases=['설정', 'a'])
async def setting(ctx, arg):
    member = ctx.author
    sql = f'SELECT keyword FROM discord WHERE name = {member}'
    cursor.execute(sql)
    keyword_list = cursor.fetchall()

    for keyword in keyword_list:
        if keyword['keyword'] == arg:
            await ctx.send('이미 설정된 키워드 입니다.다른 키워드를 입력하주세요.')

    sql = f'INSERT INTO discord(name, keyword) values({member},{ctx})'
    cursor.execute(sql)
    discord_db.commit()


@app.command(aliases=['설정확인', 'b'])
async def check_setting(ctx):
    member = ctx.author
    sql = f'SELECT keyword FROM discord WHERE name = {member}'
    cursor.execute(sql)
    keyword_list = cursor.fetchall()

    for keyword in keyword_list:
        await ctx.send(keyword['keyword'])


@app.command(aliases=['초기화', 'c'])
async def reset(ctx):
    member = ctx.author
    sql = f'DELETE FROM discord where name = {member}'
    cursor.execute(sql)
    discord_db.commit()


app.run(os.environ['token'])
