from app.application import Application


def lambda_handler(event, context):
    app = Application()
    return app.handle(event)
