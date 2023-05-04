
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, state
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3 as sq
import logging

API_TOKEN = '6277595590:AAGTrcUyez8gRZjDdDWI9YFLMRWn_sqFO3k'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = sq.connect("EventBot.sqlite")
cur = db.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS Specialization (
                        id_spec INTEGER NOT NULL UNIQUE,
                        name TEXT NOT NULL UNIQUE,
                        points INTEGER NOT NULL,
                        PRIMARY KEY(id_spec AUTOINCREMENT)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS Student (
                        id_student INTEGER NOT NULL UNIQUE,
                        StudentNumber TEXT NOT NULL UNIQUE,
                        FirstName TEXT NOT NULL,
                        LastName TEXT NOT NULL,
                        Password TEXT NOT NULL,
                        id_spec INTEGER,
                        PRIMARY KEY(id_student AUTOINCREMENT),
                        FOREIGN KEY(id_spec) REFERENCES Specialization(id_spec)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS Teacher (
                    id_teacher INTEGER NOT NULL UNIQUE,
                    FirstName TEXT NOT NULL,
                    LastName TEXT NOT NULL,
                    Specialization TEXT NOT NULL,
                    Description TEXT,
                    ContactData TEXT NOT NULL,
                    PRIMARY KEY(id_teacher AUTOINCREMENT)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS teacher_spec_tkl (
                    id_spec_teacher INTEGER NOT NULL,
                    id_teacher_spec INTEGER NOT NULL,
                    PRIMARY KEY(id_teacher_spec,id_spec_teacher),
                    FOREIGN KEY(id_teacher_spec) REFERENCES Teacher(id_teacher)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS Source (
                    id_source INTEGER NOT NULL UNIQUE,
                    link TEXT NOT NULL,
                    description TEXT,
                    data TEXT NOT NULL,
                    PRIMARY KEY(id_source AUTOINCREMENT)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS source_special_tkl (
                    id_source_spec INTEGER NOT NULL,
                    id_spec_source INTEGER NOT NULL,
                    PRIMARY KEY(id_source_spec,id_spec_source),
                    FOREIGN KEY(id_source_spec) REFERENCES Source(id_source)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS admin (
                    id_admin INTEGER NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    PRIMARY KEY(id_admin AUTOINCREMENT)
                    )''')
cur.execute('''CREATE TABLE IF NOT EXISTS FAQ (
                    id_faq INTEGER NOT NULL UNIQUE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    PRIMARY KEY(id_faq AUTOINCREMENT)
                )''')

db.commit()

@dp.callback_query_handler(lambda c: c.data == 'mentors')
async def process_callback_mentors(callback_query: types.CallbackQuery):
    # Query the database for all questions and answers from the FAQ table
    cur.execute("SELECT id_teacher, FirstName, LastName, Specialization FROM Teacher")
    teach = cur.fetchall()
    # Check if any data was returned
    if teach:
        # Format the FAQ as a string
        for id_teacher, FirstName, LastName, Specialization in teach:
            teach_text = f"Full name :{FirstName} {LastName}\nSpecialization: {Specialization}\n\n"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Show data", callback_data=f"show_teacher_data:{id_teacher}"))
            await bot.send_message(chat_id=callback_query.message.chat.id, text=teach_text, reply_markup=keyboard)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No data found in the Teacher table.")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('show_teacher_data'))
async def process_callback_show_teacher_data(callback_query: types.CallbackQuery):
    # Extract the id_teacher from the callback data
    id_teacher = int(callback_query.data.split(':')[1])

    # Query the database for the data of the chosen teacher
    cur.execute("SELECT FirstName, LastName, Specialization, Description, ContactData FROM Teacher WHERE id_teacher = ?", (id_teacher,))
    teach = cur.fetchone()

    # Check if any data was returned
    if teach:
        # Format the teacher data as a string
        FirstName, LastName, Specialization, Description, ContactData = teach
        teach_text = f"Full name : {FirstName} {LastName}\nSpecialization: {Specialization}\nDescription: {Description}\nContact Data: {ContactData}\n\n"
        await bot.send_message(chat_id=callback_query.message.chat.id, text=teach_text)


@dp.message_handler(Command("start"))
async def start_cmd(message: types.Message):

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Registration", callback_data="register"))
    keyboard.add(types.InlineKeyboardButton("Login", callback_data="login"))
    await message.answer("Welcome! Please choose an option:", reply_markup=keyboard)

@dp.callback_query_handler(text="register")
async def register_callback(callback_query: CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    await callback_query.answer()
    await callback_query.message.answer("Please enter your student number:")
    await state.set_state("student_number")


@dp.message_handler(state="student_number")
async def student_number_cmd(message: types.Message, state: FSMContext):
    student_number = message.text
    await state.update_data(student_number=student_number)
    await message.answer("Please enter your password:")
    await state.set_state("password")

@dp.message_handler(state="password")
async def password_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = message.text
    await state.update_data(password=password)
    await message.answer("Please enter your first name:")
    await state.set_state("first_name")

@dp.message_handler(state="first_name")
async def first_name_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = data.get("password")
    first_name = message.text
    await state.update_data(first_name=first_name)
    await message.answer("Please enter your last name:")
    await state.set_state("last_name")

@dp.message_handler(state="last_name")
async def last_name_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = message.text
    cur.execute(
        "INSERT INTO Student (StudentNumber, FirstName, LastName, Password) VALUES (?, ?, ?, ?)",
        (student_number, first_name, last_name, password)
    )
    db.commit()

    cur.execute(
        "SELECT * FROM Student WHERE StudentNumber=?",
        (student_number,)
    )
    user_data = cur.fetchone()
    if user_data:
        response = f"Registration successful! Here is your information:\n\n"
        response += f"Student Number: {user_data[1]}\n"
        response += f"First Name: {user_data[2]}\n"
        response += f"Last Name: {user_data[3]}\n"
        await message.answer(response)
        keyboard = InlineKeyboardMarkup()
        login_button = InlineKeyboardButton(text="Login", callback_data="login")
        keyboard.add(login_button)
        await message.answer("Click the button below to login:", reply_markup=keyboard)
    else:
        await message.answer("An error occurred while retrieving your information from the database.")
    await state.finish()

@dp.callback_query_handler(text="login")
async def login_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("Please enter your student number:")
    await state.set_state("login_student_number")

@dp.message_handler(state="login_student_number")
async def login_student_number_cmd(message: types.Message, state: FSMContext):
    student_number = message.text
    await state.update_data(student_number=student_number)
    await message.answer("Please enter your password:")
    await state.set_state("login_password")

@dp.callback_query_handler(lambda c: c.data == 'cabinet')
async def process_callback_student_info(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the student number from the state
    data = await state.get_data()
    student_number = data.get("student_number")
    # Query the database for the student's information
    cur.execute("SELECT FirstName, LastName, name FROM Student JOIN Specialization ON Student.id_spec = Specialization.id_spec WHERE StudentNumber = ?", (student_number,))
    student = cur.fetchone()
    # Check if any data was returned
    if student:
        # Format the student information as a string
        FirstName, LastName, spec_name = student
        student_text = f"Full name: {FirstName} {LastName}\nSpecialization: {spec_name}\n\n"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Edit data", callback_data="edit_student_data"))
        await bot.send_message(chat_id=callback_query.message.chat.id, text=student_text, reply_markup=keyboard)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No data found for the logged student.")

@dp.callback_query_handler(lambda c: c.data == 'edit_student_data')
async def process_callback_edit_student_data(callback_query: types.CallbackQuery):
    # Send a message with instructions on how to edit the student data
    await bot.send_message(chat_id=callback_query.message.chat.id, text="To edit your data, please send a message in the following format:\n\n/edit [FirstName] [LastName] [Specialization]\n\nFor example:\n/edit John Doe Math")


@dp.callback_query_handler(lambda c: c.data == 'faq')
async def process_callback_faq(callback_query: types.CallbackQuery):
    # Query the database for all questions and answers from the FAQ table
    cur.execute("SELECT question, answer FROM FAQ")
    faq = cur.fetchall()

    # Check if any data was returned
    if faq:
        # Format the FAQ as a string
        faq_text = "Frequently Asked Questions:\n\n"
        for question, answer in faq:
            faq_text += f"Q: {question}\nA: {answer}\n\n"
        # Send the FAQ to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=faq_text)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No data found in the FAQ table.")


@dp.callback_query_handler(lambda c: c.data == 'all_event')
async def process_callback_event(callback_query: types.CallbackQuery):
    # Query the database for all events from the Source table
    cur.execute("SELECT link, description, data FROM Source")
    source = cur.fetchall()

    # Check if any data was returned
    if source:
        # Format the events as a string
        source_text = "All events:\n\n"
        for link, description, data in source:
            source_text += f"Link: {link}\nDescription: {description}\nData: {data}\n\n"
        # Send the events to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=source_text)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No events found in the Source table.")


# Create a variable to track whether the user is logged in or not
user_logged_in = False
# Create a variable to track whether the bot is active or not
bot_active = True

@dp.callback_query_handler(lambda c: c.data == 'stop')
async def process_callback_stop(callback_query: types.CallbackQuery):
    global bot_active
    # Stop the bot
    bot_active = False
    # Clear the conversation
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

@dp.message_handler(commands=['login'])
async def process_login_command(message: types.Message):
    global user_logged_in
    # TODO: Implement functionality to log the user in
    # Set the user_logged_in variable to True to indicate that the user is logged in
    user_logged_in = True
    # Send a message indicating that the user is logged in
    await message.answer("You are now logged in. Please send the /start command to reactivate the bot.")

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    global bot_active
    # Check if the user is logged in
    if user_logged_in:
        # Reactivate the bot
        bot_active = True
        # Send a welcome message
        await message.answer("Welcome back! The bot is now active again.")
    else:
        # If the user is not logged in, send a message indicating that they need to log in first
        await message.answer("Please log in first by sending the /login command.")

@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery):
    global bot_active
    # Check if the bot is active
    if not bot_active:
        # If the bot is not active, send a message indicating that it is inactive
        await callback_query.answer("The bot is currently inactive. Please log in and send the /start command to reactivate it.")


@dp.message_handler(state="login_password")
async def login_password_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = message.text
    cur.execute(
        "SELECT * FROM Student WHERE StudentNumber=? AND Password=?",
        (student_number, password)
    )
    user_data = cur.fetchone()
    if user_data:
        await state.update_data(student_number=student_number)
        response = f"Login successful!\n\n"
        response += f"Student Number: {user_data[1]}\n"
        response += f"First Name: {user_data[2]}\n"
        response += f"Last Name: {user_data[3]}\n"
        await message.answer(response)

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("All Events", callback_data="all_event"),
            types.InlineKeyboardButton("Spec Event", callback_data="spec_event")
        )
        keyboard.add(
            types.InlineKeyboardButton("Mentors", callback_data="mentors"),
            types.InlineKeyboardButton("Cabinet", callback_data="cabinet")
        )
        keyboard.add(
            types.InlineKeyboardButton("Contact Creator", url="https://t.me/vl_los"),
            types.InlineKeyboardButton("FAQ", callback_data="faq")
        )
        keyboard.add(
            types.InlineKeyboardButton("EXIT", callback_data="stop")
        )

        await message.answer("Please choose an option:", reply_markup=keyboard)
    else:
        await message.answer("Invalid student number or password. Please try again.")
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)