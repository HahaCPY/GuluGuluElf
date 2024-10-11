from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# the dictionary that recorded the finance data
user_states = {}

# defined ConversationHandler state
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

def load_data_from_file():
    try:
        with open('finance_data.txt', 'r') as f:
            lines = f.readlines()
        
        data = []
        for line in lines:
            date, payer, category, amount = line.strip().split()
            data.append({
                'date': date,
                'payer': payer,
                'category': category,
                'amount': float(amount)
            })
        return data
    except FileNotFoundError:
        return []

# initial user_states
initial_data = load_data_from_file()
for record in initial_data:
    user_id = hash(record['payer'])
    if user_id not in user_states:
        user_states[user_id] = []
    user_states[user_id].append(record)

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("💰 Charge", callback_data='charge')],
        [InlineKeyboardButton("📊 View Records", callback_data='view_records')],
        [InlineKeyboardButton("💸 Calculate Debts", callback_data='calculate_debts')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('😽 Welcome to the GoluGlu Elf!', reply_markup=reply_markup)
    return CHOOSING

async def button(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'charge':
        keyboard = [
            [InlineKeyboardButton("🐱 Rassss", callback_data='Rassss_paid')],
            [InlineKeyboardButton("🐶 CPY", callback_data='CPY_paid')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Who paid for the money?", reply_markup=reply_markup)
    
    elif query.data in ['Rassss_paid', 'CPY_paid']:
        payer = 'Rassss' if query.data == 'Rassss_paid' else 'CPY'
        if user_id not in user_states:
            user_states[user_id] = []
        user_states[user_id].append({'payer': payer})
        keyboard = [
            [InlineKeyboardButton("🍽️ Eat", callback_data='eat')],
            [InlineKeyboardButton("🎮 Play", callback_data='play')],
            [InlineKeyboardButton("🐣 Else", callback_data='else')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"{payer} paid. What's the category?", reply_markup=reply_markup)
    
    elif query.data in ['eat', 'play', 'else']:
        user_states[user_id][-1]['category'] = query.data
        await query.edit_message_text(text=f"Category: {query.data}. Please enter the amount:")
        return TYPING_REPLY
    
    elif query.data == 'view_records':
        records = load_data_from_file()
        if records:
            message = "📝 Here are the recent records:\n\n"
            for i, record in enumerate(records[-10:], 1):  # only display the nearly 10 recorded data
                message += f"{i}. {record['date']} - {record['payer']} paid {record['amount']} for {record['category']}\n"
            message += "\n 🖊️ Type 'modify X' to edit the record."
            message += "\n 🗑 Type 'delete X' to delete the record."
        else:
            message = "No records found."
        await query.edit_message_text(text=message)
        return TYPING_CHOICE
    
    elif query.data == 'calculate_debts':
        records = load_data_from_file()
        total_spent = {'Rassss': 0, 'CPY': 0}
        for record in records:
            total_spent[record['payer']] += record['amount']
        
        total = sum(total_spent.values())
        each_should_pay = total / 2
        
        if total_spent['Rassss'] > total_spent['CPY']:
            debt = total_spent['Rassss'] - each_should_pay
            message = f"CPY owes Rassss {debt:.2f}"
        else:
            debt = total_spent['CPY'] - each_should_pay
            message = f"Rassss owes CPY {debt:.2f}"
        
        await query.edit_message_text(text=f"💰 Debt Calculation:\n\n{message}")
    
    return CHOOSING

async def handle_amount(update, context):
    user_id = update.message.from_user.id
    if user_id in user_states and user_states[user_id] and 'category' in user_states[user_id][-1]:
        try:
            amount = float(update.message.text)
            current_record = user_states[user_id][-1]
            current_record['amount'] = amount
            current_record['date'] = datetime.now().strftime("%Y-%m-%d")
            
            # 寫入 data.txt
            with open('data.txt', 'a') as f:
                f.write(f"{current_record['date']} {current_record['payer']} {current_record['category']} {current_record['amount']}\n")
            
            await update.message.reply_text(f"✅ Record added: {current_record['date']} {current_record['payer']} {current_record['category']} {current_record['amount']}")
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number for the amount.")
    else:
        await update.message.reply_text("⚠️ Please start the process by clicking the Charge button.")
    return CHOOSING

async def handle_modify_or_delete(update, context):
    text = update.message.text.lower()
    if text.startswith('modify ') or text.startswith('delete '):
        try:
            action, index = text.split()
            index = int(index) - 1
            records = load_data_from_file()
            if 0 <= index < len(records):
                record = records[index]
                context.user_data['action'] = action
                context.user_data['modify_index'] = index
                if action == 'modify':
                    await update.message.reply_text(f"You're modifying this record:\n"
                                                    f"{record['date']} - {record['payer']} paid {record['amount']} for {record['category']}\n"
                                                    f"What would you like to change? (date/payer/category/amount)")
                    return TYPING_REPLY
                else:  # delete
                    del records[index]
                    with open('data.txt', 'w') as f:
                        for record in records:
                            f.write(f"{record['date']} {record['payer']} {record['category']} {record['amount']}\n")
                    await update.message.reply_text(f"✅ Record deleted successfully.")
            else:
                await update.message.reply_text("Invalid record number. Please try again.")
        except ValueError:
            await update.message.reply_text("Invalid input. Please use 'modify X' or 'delete X' where X is the record number.")
    else:
        await update.message.reply_text("I didn't understand that command. Please try again.")
    return CHOOSING

async def handle_modify_field(update, context):
    text = update.message.text.lower()
    if 'modify_index' in context.user_data:
        records = load_data_from_file()
        index = context.user_data['modify_index']
        record = records[index]
        
        if text in ['date', 'payer', 'category', 'amount']:
            context.user_data['modify_field'] = text
            await update.message.reply_text(f"Current {text}: {record[text]}\nPlease enter the new {text}:")
            return TYPING_REPLY
        else:
            await update.message.reply_text("Invalid field. Please choose date, payer, category, or amount.")
            return CHOOSING

async def handle_modify_value(update, context):
    text = update.message.text
    if 'modify_index' in context.user_data and 'modify_field' in context.user_data:
        records = load_data_from_file()
        index = context.user_data['modify_index']
        field = context.user_data['modify_field']
        
        if field == 'amount':
            try:
                value = float(text)
            except ValueError:
                await update.message.reply_text("Invalid amount. Please enter a number.")
                return TYPING_REPLY
        else:
            value = text
        
        records[index][field] = value
        
        # 重新寫入所有記錄
        with open('data.txt', 'w') as f:
            for record in records:
                f.write(f"{record['date']} {record['payer']} {record['category']} {record['amount']}\n")
        
        await update.message.reply_text(f"✅ Record updated: {records[index]['date']} {records[index]['payer']} {records[index]['category']} {records[index]['amount']}")
        
        del context.user_data['modify_index']
        del context.user_data['modify_field']
    else:
        await update.message.reply_text("Something went wrong. Please start over.")
    return CHOOSING

def main():
    with open("token.txt", "r") as token_file:
        token = token_file.read().strip()

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                CallbackQueryHandler(button),
                MessageHandler(filters.Regex('^(modify|delete)'), handle_modify_or_delete),
            ],
            TYPING_CHOICE: [
                MessageHandler(filters.Regex('^(modify|delete)'), handle_modify_or_delete),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_modify_field),
            ],
            TYPING_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_modify_value),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()