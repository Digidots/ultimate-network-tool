"""
Absolute minimal Flask test to verify Flask works
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Main page works!</h1>"

@app.route('/test')
def test():
    return "<h1>Test page works!</h1>"

@app.route('/mtu-test')
def mtu_test():
    return "<h1>MTU test page works!</h1>"

if __name__ == '__main__':
    print("=" * 60)
    print("SIMPLE FLASK TEST")
    print("Try: http://localhost:5001/")
    print("Try: http://localhost:5001/test")
    print("Try: http://localhost:5001/mtu-test")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)
