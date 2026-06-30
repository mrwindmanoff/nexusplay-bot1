import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# ================= FLASK-СЕРВЕР ДЛЯ KEEP-ALIVE =================
app = Flask('')

@app.route('/')
def home():
    return "✅ NexusPlay Bot is running 24/7!"

def run():
    # Railway сам назначает порт через переменную PORT
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
# ===============================================================

# ================= НАСТРОЙКИ =================
# Токен берём из переменных окружения Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден! Добавь его в Variables на Railway.")
    exit(1)

# ID каналов
WELCOME_CHANNEL_ID = 1521167174238998599  # #👋-привет
LOG_CHANNEL_ID = 1521168750559363162      # #🔐-лог-действий
RULES_CHANNEL_ID = 1521167009600114828    # #📜-правила
TICKET_CHANNEL_ID = 1521168530308071614   # #🎫-тикет

# ID ролей
GUEST_ROLE_ID = 1521169957537320971       # 👤 Гость
MEMBER_ROLE_ID = 1521169839069204632      # ✅ Участник
# =============================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} запущен и готов к работе!')
    print(f'ID бота: {bot.user.id}')
    print('─' * 50)


@bot.event
async def on_member_join(member):
    """Когда новый участник заходит на сервер"""

    # 1. Выдаем роль "Гость"
    guest_role = member.guild.get_role(GUEST_ROLE_ID)
    if guest_role:
        try:
            await member.add_roles(guest_role)
            print(f'✅ Выдана роль Гость для {member.name}')
        except Exception as e:
            print(f'❌ Ошибка выдачи роли: {e}')

    # 2. Отправляем приветствие
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel:
        embed = discord.Embed(
            title='🎮 Добро пожаловать в NexusPlay Community!',
            description=(
                f'Привет, {member.mention}! Рады видеть тебя!\n\n'
                f'📊 **Нас уже:** {member.guild.member_count} участников\n\n'
                f'**Что делать дальше:**\n'
                f'1️⃣ Прочитай <#{RULES_CHANNEL_ID}>\n'
                f'2️⃣ Напиши `!verify` в любом канале для верификации\n'
                f'3️⃣ Получи доступ ко всем каналам!\n\n'
                f'🎮 **Игры нашего комьюнити:**\n'
                f'• Counter-Strike 2\n'
                f'• Valorant\n'
                f'• Dota 2\n'
                f'• Minecraft\n\n'
                f'💬 Вопросы? Создай тикет в <#{TICKET_CHANNEL_ID}>'
            ),
            color=0x00ff00
        )
        avatar = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar)
        embed.set_footer(text=f'ID: {member.id} • Присоединился')
        await welcome_channel.send(embed=embed)

    # 3. Пишем в лог
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title='📥 Новый участник',
            description=f'{member.mention} ({member.name}) присоединился',
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        log_embed.add_field(
            name='Аккаунт создан',
            value=member.created_at.strftime('%d.%m.%Y'),
            inline=True
        )
        log_embed.add_field(
            name='Всего участников',
            value=str(member.guild.member_count),
            inline=True
        )
        avatar = member.avatar.url if member.avatar else member.default_avatar.url
        log_embed.set_thumbnail(url=avatar)
        await log_channel.send(embed=log_embed)


@bot.event
async def on_member_remove(member):
    """Когда участник покидает сервер"""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title='📤 Участник вышел',
            description=f'{member.name} покинул сервер',
            color=0xff0000,
            timestamp=discord.utils.utcnow()
        )
        avatar = member.avatar.url if member.avatar else member.default_avatar.url
        log_embed.set_thumbnail(url=avatar)
        await log_channel.send(embed=log_embed)


@bot.command(name='verify')
async def verify(ctx):
    """Команда для верификации (Гость → Участник)"""
    guest_role = ctx.guild.get_role(GUEST_ROLE_ID)
    member_role = ctx.guild.get_role(MEMBER_ROLE_ID)

    if not guest_role or not member_role:
        await ctx.send('❌ Ошибка: роли не найдены.', delete_after=5)
        return

    if guest_role not in ctx.author.roles:
        error_embed = discord.Embed(
            title='⚠️ Ошибка',
            description='Ты уже верифицирован или не имеешь роли Гость!',
            color=0xff0000
        )
        await ctx.send(embed=error_embed, delete_after=5)
        try:
            await ctx.message.delete()
        except:
            pass
        return

    # Убираем Гость, выдаём Участник
    await ctx.author.remove_roles(guest_role)
    await ctx.author.add_roles(member_role)

    success_embed = discord.Embed(
        title='✅ Верификация пройдена!',
        description=(
            f'{ctx.author.mention}, добро пожаловать!\n'
            f'Теперь у тебя есть доступ ко всем каналам.\n\n'
            f'🎮 Приятной игры в NexusPlay Community!'
        ),
        color=0x00ff00
    )
    await ctx.send(embed=success_embed, delete_after=10)

    # Лог
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title='✅ Верификация',
            description=f'{ctx.author.mention} ({ctx.author.name}) прошёл верификацию',
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        await log_channel.send(embed=log_embed)

    try:
        await ctx.message.delete()
    except:
        pass


# ================= ЗАПУСК БОТА =================
bot.run(BOT_TOKEN)
