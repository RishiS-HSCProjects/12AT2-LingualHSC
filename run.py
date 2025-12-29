from lingual import create_app

app = create_app() # Gets app from default config

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Run app
