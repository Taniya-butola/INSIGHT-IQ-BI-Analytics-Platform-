from app import create_app

app = create_app()
print('db uri', app.config['SQLALCHEMY_DATABASE_URI'])
with app.app_context():
    import extensions
    print('db object', extensions.db)
    print('tables', list(extensions.db.metadata.tables.keys()))
