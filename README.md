# Lingual HSC

Lingual HSC is a Flask-based language learning web application built for HSC students wanting to learn and practice syllabus-focused languages content. While Lingual currently supports only one module (Japanese), the program has been built with scalability in mind to allow Course Developers to add create lessons and courses with little required developmental setup.

# How to run Lingual HSC on your local machine
1. **Download Package**: Download the Lingual repository from this GitHub page

2. **Install Required Dependencies**: Open the directory in your terminal and run the below command to install the required Python packages for this program to run.
	> Note: it is recommended that packages are installed and ran through a virtual environemnt to prevent clashes with other packages on your machine.
	```shell
	pip install -r requirements.txt
	```

3. **Setup environment variables**: Create a `.env` file and locate it in the folder's root (i.e. same folder as the `__init__.py` and `models.py` files). Then, copy the below snippet into the `.env` file. Fill all info variables with valid values. Remove square brackets (included to be placeholders).
	```env
	DEBUG = [BOOL]
	FLASK_ENV = ['production'. 'development']
	SECRET_KEY = ['abc123']
	SQLALCHEMY_DATABASE_URI = 'postgresql://[URI]' # Remove if you choose to use a local database. See below

	# MAIL
	MAIL_USERNAME = ['lingualhsc@gmail.com']
	MAIL_PASSWORD = ['1234 5678 9012 3456']
	MAIL_DEFAULT_SENDER = ('Lingual HSC', 'lingualhsc@gmail.com')
	ALLOW_SEND_EMAILS = True # Switch to false if you do not want to use the mail server.

	# SERVER
	PUBLIC_BASE_URL = ['http://127.0.0.1:5000']

	# API KEYS
	WANIKANI_API_KEY = ['we-pull-from-wanikanis-api']
	# Note: The WANIKANI_API_KEY is optional. The 201 prescribed kanji are cached in the repository. Use the API key only if you need to fetch details for non-prescribed kanji or refresh cached data.
	```

4. **Configure Database**: Choose one of the below.
	- **Local database**: Go to the directory [lingual\core\data](https://github.com/RishiS-HSCProjects/12AT2-LingualHSC/blob/main/lingual/core/data) and create a file called `lingual.db`.
	- **Cloud database**: Setup a basic postgresql database and attach the URI to the aforementioned `.env` file.

	Once your database is created, open the terminal to your directory and paste the following commands.

	**Windows**
	```shell
	set FLASK_APP=run.py
	flask shell
	```

	**macOS**
	```shell
	export FLASK_APP=run.py
	flask shell
	```

	After the shell opens, paste the following:
	```shell
	from lingual import db
	db.drop_all()
	db.create_all()
	db.session.commit()
	```

	This should successfully configure your database.

## Warnings and Prerequisites

- Before running the app, ensure you have the necessary environment variables set in your `.env` file as outlined above. Missing or incorrect values can lead to startup failures or runtime errors.
- Ensure you have Python 3.13 installed (3.14 had some issues with Flask during testing)
- If you want to test email features, you will need valid SMTP credentials and `ALLOW_SEND_EMAILS` set to true in your `.env`. For local testing without email, set `ALLOW_SEND_EMAILS` to false and the app will emulate OTP verification with a default OTP of `123456`. Note that password reset features will not be emulated and require email functionality.
- If you want to use the WaniKani API features for kanji details, you will need a valid `WANIKANI_API_KEY` in your `.env`. The app includes cached data for the 201 prescribed kanji, so the API key is only necessary if you want to fetch details for non-prescribed kanji or refresh cached data.
- After setting up the database, you may want to create a test user account by registering through the app's registration page. This will allow you to explore authenticated features and progress tracking.

You are now ready to explore the features of Lingual HSC!

# Main Features

## Authentication and User Accounts
- Session-based authentication with Flask-Login
- Password complexity verification and hashing
- OTP email verification during registration (Emails sent if `ALLOW_SEND_EMAILS` is enabled in the server's settings. If not, the process is emulated with a default OTP of `123456`.)
- Password reset via timed, one-time-use token links (dependent on `ALLOW_SEND_EMAILS` being enabled. No supplementary emulation.)
- Account settings and multi-language selection support

### Learning Content System
- Markdown/frontmatter lesson content processing
- Quiz JSON loading and quiz session rendering
- Category-based lesson directories (e.g. grammar, tutorials)

### Japanese Module (日本Go!)
- Grammar lesson directory and lesson pages
- Grammar quiz generation and quiz sessions
- Prescribed kanji grid
- Kanji details (WaniKani API integration)
- Particle note tiles and lookup endpoints

### Progress Tracking
- User language selection stored per account
- Per-language stats model with progress tracking
	- For Japanese, tracks learned kanji, practised kanji, and practised grammar lessons
- Recently viewed/completed lessons (for home page and quick access)

# Technology, Programs, and Libraries Used

- Templating: Jinja2
- Backend: Flask (Python)
- Database ORM: SQLAlchemy (Flask-SQLAlchemy)
- Auth/session: Flask-Login
- Forms/validation: Flask-WTF, WTForms
- Mail Engine: Flask-Mail
- Security: Werkzeug + bcrypt
- Database drivers: SQLite or PostgreSQL

Further details on specific libraries and versions can be found in [`requirements.txt`](https://github.com/RishiS-HSCProjects/12AT2-LingualHSC/blob/main/requirements.txt).

## Security Notes
- Passwords are hashed before persistence
- Password reset links are tokenized and time-limited
- Registration OTP is hashed in session storage
- Email reset responses avoid account enumeration patterns
- Route-level auth checks are applied for protected learning features

Please refer to the license file for terms of use and contribution guidelines.
