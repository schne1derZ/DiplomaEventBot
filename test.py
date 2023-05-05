    first
    part:
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
                teach_text = f"Full name: {FirstName} {LastName}\nSpecialization: {Specialization}\n\n"
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
        cur.execute(
            "SELECT FirstName, LastName, Specialization, Description, ContactData FROM Teacher WHERE id_teacher = ?",
            (id_teacher,))
        teach = cur.fetchone()
        # Check if any data was returned
        if teach:
            # Format the teacher data as a string
            FirstName, LastName, Specialization, Description, ContactData = teach
            teach_text = f"Full name: {FirstName} {LastName}\nSpecialization: {Specialization}\nDescription: {Description}\nContact Data: {ContactData}\n\n"
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


    logger = logging.getLogger(__name__)

    # Define constants for the states
    STATE_LOGIN_STUDENT_NUMBER = 'login_student_number'
    STATE_LOGIN_PASSWORD = 'login_password'


    # Define the start command handler
    @dp.message_handler(CommandStart())
    async def start_command_handler(message: Message):
        # Check if the user is logged in
        async with dp.current_state(chat=message.chat.id) as state:
            user_data = await state.get_data()
            user_logged_in = user_data.get('user_logged_in', False)

        if user_logged_in:
            # Send a welcome back message
            await message.answer("Welcome back!")
        else:
            # Send a message with login options
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Login", callback_data="login"))
            await message.answer("Please login to access the bot.", reply_markup=keyboard)


    # Define the login callback query handler
    @dp.callback_query_handler(text="login")
    async def login_callback(callback_query: CallbackQuery, state: FSMContext):
        await callback_query.answer()
        await callback_query.message.answer("Please enter your student number:")
        await state.set_state(STATE_LOGIN_STUDENT_NUMBER)


    # Define the login student number handler
    @dp.message_handler(state=STATE_LOGIN_STUDENT_NUMBER)
    async def login_student_number_handler(message: Message, state: FSMContext):
        student_number = message.text
        async with state.proxy() as data:
            data['student_number'] = student_number

        await message.answer("Please enter your password:")
        await state.set_state(STATE_LOGIN_PASSWORD)


    # Define the login password handler
    @dp.message_handler(state=STATE_LOGIN_PASSWORD)
    async def login_password_handler(message: Message, state: FSMContext):
        password = message.text
        async with state.proxy() as data:
            data['password'] = password
            student_number = data['student_number']

        # TODO: Implement authentication logic
        # Query the database to authenticate the user
        try:
            cur.execute(
                "SELECT FirstName, LastName, name FROM Student JOIN Specialization ON Student.id_spec = Specialization.id_spec WHERE StudentNumber = ?",
                (student_number,))
            student = cur.fetchone()
        except Exception as e:
            logger.error(f"Error querying the database: {e}")
            await message.answer("An error occurred. Please try again later.")
            return

        if student:
            # Format the student information as a string
            FirstName, LastName, spec_name = student
            student_text = f"Full name: {FirstName} {LastName}\nSpecialization: {spec_name}\n\n"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Edit data", callback_data="edit_student_data"))
            await message.answer(student_text, reply_markup=keyboard)

            async with state.proxy() as data:
                data['user_logged_in'] = True
        else:
            # Send a message indicating that no data was found
            await message.answer("Sorry, no student data was found for this user. Please try again later.")


    @dp.message_handler(Command("start"))
    async def process_start_command(message: types.Message, state: FSMContext, conn=Depends(get_database_connection)):
        async with state.proxy() as data:
            user_logged_in = data.get("user_logged_in", False)

        if user_logged_in:
            # Reactivate the bot
            async with conn:
                cur.execute("UPDATE Settings SET value=1 WHERE key='bot_active'")
            await message.answer(START_COMMAND_TEXT)
        else:
            await message.answer(LOGIN_COMMAND_TEXT)


    @dp.message_handler(Command("login"))
    async def process_login_command(message: types.Message):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Cancel", callback_data="cancel_login"))

        await message.answer("Please enter your student number:", reply_markup=keyboard)
        await state.set_state("login_number")


    @dp.message_handler(state="login_number")
    async def login_number_cmd(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['student_number'] = message.text

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Cancel", callback_data="cancel_login"))

        await message.answer("Please enter your password:", reply_markup=keyboard)
        await state.set_state("login_password")


    @dp.message_handler(state="login_password")
    async def login_password_cmd(message: types.Message, state: FSMContext, conn=Depends(get_database_connection)):
        data = await state.get_data()
        student_number = data.get("student_number")
        password = message.text

        try:
            async with conn:
                cur.execute(
                    "SELECT * FROM Student WHERE StudentNumber=? AND Password=?",
                    (student_number, password)
                )
                user_data = cur.fetchone()

                if user_data:
                    await state.update_data(user_logged_in=True)
                    response = f"Login successful!\n\n"
                    response += f"Student Number: {user_data[1]}\n"
                    response += f"First Name: {user_data[2]}\n"
                    response += f"Last Name: {user_data[3]}\n"
                    await message.answer(response)

                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton("All Events", callback_data="all_event"))
                    keyboard.add(InlineKeyboardButton("Spec Event", callback_data="spec_event"))
                    keyboard.add(InlineKeyboardButton("Mentors", callback_data="mentors"))


    keyboard.add(InlineKeyboardButton("Cabinet", callback_data="cabinet"))
    keyboard.add(InlineKeyboardButton("Contact Creator", url="https://t.me/vl_los"))
    keyboard.add(InlineKeyboardButton("FAQ", callback_data="faq"))
    keyboard.add(InlineKeyboardButton("Exit", callback_data="exit"))
    await message.answer("Please choose an option:", reply_markup=keyboard)
    elif callback_data == "all_event":
    # Query the database for all events
    cur.execute("SELECT * FROM Event")
    events = cur.fetchall()
    if events:
    # If there are events, format them as a string and send them to the user
    event_text = "All Events:\n\n"
    for event in events:
        event_text += f"{event[1]} ({event[2]}): {event[3]} - {event[4]}\n"
    await message.answer(event_text)
    else:
    # If there are no events, send a message indicating that there are no events
    await message.answer("There are currently no events.")
    elif callback_data == "spec_event":
    # Ask the user to enter the specialization for which they want to see the events
    await message.answer("Please enter the specialization for which you want to see the events:")
    # Set the state to the event_specialization state
    await Form.event_specialization.set()
    elif callback_data == "mentors":
    # Query the database for all mentors
    cur.execute("SELECT * FROM Mentor")
    mentors = cur.fetchall()
    if mentors:
    # If there are mentors, format them as a string and send them to the user
    mentor_text = "Mentors:\n\n"
    for mentor in mentors:
        mentor_text += f"{mentor[1]} {mentor[2]} ({mentor[3]}): {mentor[4]}\n"
    await message.answer(mentor_text)
    else:
    # If there are no mentors, send a message indicating that there are no mentors
    await message.answer("There are currently no mentors.")
    elif callback_data == "cabinet":
    # Query the database for all cabinet members
    cur.execute("SELECT * FROM Cabinet")
    cabinet = cur.fetchall()
    if cabinet:
    # If there are cabinet members, format them as a string and send them to the user
    cabinet_text = "Cabinet Members:\n\n"
    for member in cabinet:
        cabinet_text += f"{member[1]} {member[2]} ({member[3]}): {member[4]}\n"
    await message.answer(cabinet_text)
    else:
    # If there are no cabinet members, send a message indicating that there are no cabinet members
    await message.answer("There are currently no cabinet members.")
    elif callback_data == "faq":
    # Send a message with frequently asked questions and their answers
    faq_text = "Frequently Asked Questions:\n\n"
    faq_text += "Q: What is the purpose of this bot?\n"
    faq_text += "A: The purpose of this bot is to provide information about events, mentors, and cabinet members for students in the Computer Science program at XYZ University.\n\n"
    faq_text += "Q: How do I log in?\n"
    faq_text += "A: Send the /login command and follow the prompts.\n\n"
    faq_text += "Q: How do I see all events?\n"
    faq_text += "A: Choose the 'All Events' option from the menu.\n\n"
    faq_text += "Q: How do I see
    the
    events
    for a specific specialization?\n"
    faq_text += "A: Choose the 'Spec Event' option from the menu and select your specialization.\n\n"
    faq_text += "Q: How do I contact a mentor?\n"
    faq_text += "A: Choose the 'Mentors' option from the menu and select the mentor you want to contact.\n\n"
    faq_text += "Q: How do I access the student cabinet?\n"
    faq_text += "A: Choose the 'Cabinet' option from the menu.\n\n"
    faq_text += "If you have any other questions, please contact the creator by choosing the 'Contact Creator' option from the menu."


    @dp.callback_query_handler(lambda c: c.data and c.data.startswith('all_event'))
    async def all_event(callback_query: types.CallbackQuery):


    # Get all events from the database
    cur.execute("SELECT * FROM Event")
    events = cur.fetchall()
    event_text = ""
    for event in events:
        event_id, event_name, event_date, event_time, event_location, event_description = event
        event_text += f"{event_name} ({event_date} {event_time}) - {event_location}\n{event_description}\n\n"

    # Send the events to the user
    await bot.send_message(callback_query.from_user.id, event_text)


    @dp.callback_query_handler(lambda c: c.data and c.data.startswith('spec_event'))
    async def spec_event(callback_query: types.CallbackQuery):


    # Get the user's specialization
    data = await state.get_data()
    spec_id = data.get("specialization_id")
    # Get the events for the user's specialization from the database
    cur.execute(
        "SELECT Event.EventName, Event.EventDate, Event.EventTime, Event.EventLocation, Event.EventDescription FROM Event JOIN EventSpecialization ON Event.EventID = EventSpecialization.EventID WHERE EventSpecialization.SpecializationID = ?",
        (spec_id,))
    events = cur.fetchall()

    # Format the events as a string
    event_text = ""
    for event in events:
        event_name, event_date, event_time, event_location, event_description = event
        event_text += f"{event_name} ({event_date} {event_time}) - {event_location}\n{event_description}\n\n"

    # Send the events to the user
    await bot.send_message(callback_query.from_user.id, event_text)


    @dp.callback_query_handler(lambda c: c.data and c.data.startswith('mentors'))
    async def mentors(callback_query: types.CallbackQuery):


    # Get all mentors from the database
    cur.execute("SELECT * FROM Mentor")
    mentors = cur.fetchall()
    # Format the mentors as a string
    mentor_text = ""
    for mentor in mentors:
        mentor_id, mentor_name, mentor_email, mentor_phone = mentor
        mentor_text += f"{mentor_name}\nEmail: {mentor_email}\nPhone: {mentor_phone}\n\n"

    # Send the mentors to the user
    await bot.send_message(callback_query.from_user.id, mentor_text)


    @dp.callback_query_handler(lambda c: c.data and c.data.startswith('cabinet'))
    async def cabinet(callback_query: types.CallbackQuery):


    # Get the user's student number
    data = await state.get_data()
    student_number = data.get("student_number")
    # Get the student's information from the database
    cur.execute("SELECT * FROM Student WHERE StudentNumber=?", (student_number,))
    student = cur.fetchone()

    # Check if the student's data was found
    if student:
        # Format the student information as a string
        FirstName, LastName, spec_name = student

        # Check if the student has any upcoming events
        cur.execute(
            "SELECT COUNT(*) FROM EventAttendee WHERE StudentNumber=? AND Date>=date('now')",
            (student_number,)
        )
        upcoming_events = cur.fetchone()[0]
        if upcoming_events > 0:
            events_text = f"You have {upcoming_events} upcoming event{'s' if upcoming_events > 1 else ''}.\n"
        else:
            events_text = "You don't have any upcoming events.\n"

        student_text = f"Full name: {FirstName} {LastName}\nSpecialization: {spec_name}\n{events_text}\n"
        keyboard.add(InlineKeyboardButton("Edit data", callback_data="edit_student_data"))
        await message.answer(student_text, reply_markup=keyboard)

    async with state.proxy() as data:
        data['user_logged_in'] = True


    @dp.callback_query_handler(text='edit_student_data')
    async def edit_student_data(callback_query: types.CallbackQuery, state: FSMContext):


    # Get the student number from the state
    data = await state.get_data()
    student_number = data.get("student_number")
    # Retrieve the student's information from the database
    cur.execute(
        "SELECT * FROM Student WHERE StudentNumber=?",
        (student_number,)
    )
    student = cur.fetchone()
    if student:
    # Send a message to ask the user for the information to update
    await callback_query.message.answer("What information would you like to update?",
                                        reply_markup=types.ReplyKeyboardRemove())
    # Set the state to wait for the user's response
    await EditStudentData.waiting_for_update.set()
    else:
    # Send a message indicating that the student's information was not found
    await callback_query.message.answer("Sorry, your information was not found.")


    @dp.message_handler(state=EditStudentData.waiting_for_update)
    async def process_update(message: types.Message, state: FSMContext):


    # Get the student number from the state
    data = await state.get_data()
    student_number = data.get("student_number")
    # Retrieve the student's information from the database
    cur.execute(
        "SELECT * FROM Student WHERE StudentNumber=?",
        (student_number,)
    )
    student = cur.fetchone()
    if student:
    # Update the appropriate field in the database based on the user's response
    update_field = None
    if message.text.lower() == "first name":
        update_field = "FirstName"
    elif message.text.lower() == "last name":
        update_field = "LastName"
    elif message.text.lower() == "specialization":
    update_field = "Specialization"
    if update_field:
    # Send a message to ask the user for the new value
    await message.answer(f"What is your new {update_field}?", reply_markup=types.ReplyKeyboardRemove())
    # Set the state to wait for the user's response
    await EditStudentData.waiting_for_new_value.set()
    else:
    # If the user entered an invalid field, send a message indicating the error
    await message.answer("Invalid field. Please choose one of the following: First Name, Last Name, Specialization.")
    else:
    # Send a message indicating that the student's information was not found
    await message.answer("Sorry, your information was not found.")
    await state.finish()


    @dp.message_handler(state=EditStudentData.waiting_for_new_value)
    async def process_new_value(message: types.Message, state: FSMContext):


    # Get the student number from the state
    data = await state.get_data()
    student_number = data.get("student_number")
    # Retrieve the student's information from the database
    cur.execute(
        "SELECT * FROM Student WHERE StudentNumber=?",
        (student_number,)
    )
    student = cur.fetchone()
    if student:
    # Update the appropriate field in the database with the new value provided by the user
    update_field = None
    if state.previous_state.lower() == "first name":
        update_field = "FirstName"
    elif state.previous_state.lower() == "last name":
        update_field = "LastName"
    elif state.previous_state.lower() == "specialization":
    update_field = "Specialization"
    if update_field:
        cur.execute(
            f"UPDATE Student SET {update_field}=? WHERE StudentNumber=?",
            (update_value, student_number)
        )
    conn.commit()

    response = f"{update_field} updated to {update_value}"
    await message.answer(response)

