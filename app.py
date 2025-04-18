from routes import app
from db_functions import db_session_handler, advance_time

import threading
import time

@db_session_handler
def time_loop():
    with app.app_context():
        while True:
            time.sleep(5)  # 5 seconds in simulation = 1 min in real world
            advance_time()

threading.Thread(target=time_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
