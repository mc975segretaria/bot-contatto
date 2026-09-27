import  os 
from  telegram  import  Update ,  InlineKeyboardButton ,  InlineKeyboardMarkup 
from  telegram . ext  import  ( 
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from datetime import datetime

# ==== CONFIGURAZIONE ====
TOKEN = "8826166311:AAHTHKV2ARzqh9K3kQK6OuZNl3Qrb8_0uCg"
ADMIN_ID = 5055246527
INFO_TESTO = (
    "ℹ️ *Informazioni*\n\n"
    "Al momento sono impegnato e non posso rispondere subito.\n"
    "Puoi:\n"
    "• lasciarmi un messaggio qui\n"
    "• chiedermi di essere richiamato\n"
    "• segnalare un'urgenza\n\n"
    "Ti risponderò il prima possibile. Grazie!"
)
# ========================

contatti = {}

def menu():
    keyboard = [
        [InlineKeyboardButton("📞 Richiamami", callback_data="richiamami")],
        [InlineKeyboardButton("⏰ È urgente", callback_data="urgente")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
    ]
    return InlineKeyboardMarkup(keyboard)

def pulsante_priorita():
    keyboard = [
        [InlineKeyboardButton("✅ Preso in carico", callback_data="preso_in_carico")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "Sei l'admin. Comandi:\n"
            "/rispondi <id> <testo> — rispondi a un contatto\n"
            "/lista — mostra gli ultimi contatti"
        )
        return
    await update.message.reply_text(
        "Ciao! Al momento sono impegnato, ma ho ricevuto il tuo messaggio. "
        "Ti risponderò il prima possibile.",
        reply_markup=menu()
    )
    if ADMIN_ID:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Nuovo messaggio da {user.full_name} (id: {user.id}):\n\n{update.message.text or '[non testo]'}"
        )

async def ricevi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    testo = update.message.text or "[messaggio non testuale]"

    if user.id == ADMIN_ID:
        await update.message.reply_text("Comando non riconosciuto. Usa /start per l'elenco.")
        return

    contatti[user.id] = user.full_name

    await update.message.reply_text(
        "Ciao! Al momento sono impegnato, ma ho ricevuto il tuo messaggio. "
        "Ti risponderò il prima possibile.",
        reply_markup=menu()
    )

    if ADMIN_ID:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 {user.full_name} (id: {user.id}) scrive:\n\n{testo}"
        )

async def pulsante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    scelta = query.data

    if scelta == "richiamami":
        if ADMIN_ID:
            adesso = datetime.now().strftime("%d/%m/%Y, %H:%M")
            messaggio_priorita = (
                "🔴🔴🔴 [PRIORITÀ] 🔴🔴🔴\n\n"
                "📞 RICHIAMATA RICHIESTA\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 {user.full_name}\n"
                f"🆔 ID: {user.id}\n"
                f"🕐 {adesso}\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ Questo contatto vuole essere richiamato."
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=messaggio_priorita,
                reply_markup=pulsante_priorita()
            )
        await query.edit_message_text(
            "Ok, ho segnalato che vuoi essere richiamato. Ti risponderò il prima possibile."
        )

    elif scelta == "preso_in_carico":
        if user.id != ADMIN_ID:
            await query.answer("Questo pulsante è solo per l'admin.", show_alert=True)
            return
        await query.edit_message_text(
            "✅ Richiesta presa in carico. Puoi procedere con la chiamata."
        )

    elif scelta == "urgente":
        if ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 URGENTE\nDa: {user.full_name} (id: {user.id})"
            )
        await query.edit_message_text(
            "Ok, ho segnalato l'urgenza. Cercherò di risponderti al più presto."
        )

    elif scelta == "info":
        await query.edit_message_text(
            INFO_TESTO,
            parse_mode="Markdown"
        )

async def rispondi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /rispondi <id> <testo>")
        return
    destinatario = int(context.args[0])
    testo = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=destinatario, text=testo)
        await update.message.reply_text("✅ Inviato.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {e}")

async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not contatti:
        await update.message.reply_text("Nessun contatto ancora.")
        return
    righe = [f"{nome} — id: {uid}" for uid, nome in contatti.items()]
    await update.message.reply_text("Contatti:\n" + "\n".join(righe))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rispondi", rispondi))
    app.add_handler(CommandHandler("lista", lista))
    app.add_handler(CallbackQueryHandler(pulsante))
    app.add_handler(MessageHandler(filters.ALL, ricevi))

    # ==== AVVIO: webhook se online, polling se in locale ====
    PORT = int(os.environ.get("PORT", 8443))
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if RENDER_URL:
        # Siamo su Render: usa il webhook
        print(f"Avvio in modalità WEBHOOK su {RENDER_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_URL}/{TOKEN}"
        )
    else:
        # Siamo in locale (il tuo PC): usa il polling
        print("Bot avviato in locale (polling). Premi Ctrl+C per fermarlo.")
        app.run_polling()

if __name__ == "__main__":
    main()
