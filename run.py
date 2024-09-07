from app import create_app

app = create_app()
print("App created successfully")

if __name__ == '__main__':
    app.run(debug=True)