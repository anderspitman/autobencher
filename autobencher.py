import os
from autobencher.server import app
from tornado.ioloop import IOLoop

if __name__ == "__main__":
    app.listen(int(os.environ['PORT']))
    IOLoop.current().start()
