from flask import Flask,jsonify
import sys
sys.path.append('/home/snehal/flaskproject/project')
import models
import traceback
app = Flask(__name__)
print(__name__+' >>>>>>>')
@app.route("/enter")
def enter():
    try :
        r=models.extract(app)
    except:
        print(traceback.format_exc())
    return str(r)

@app.route("/grammar/api/v1/top_lang_errors_for_user/<user_id>")
def top_lang_errors_for_user(user_id):
    print(str(user_id)+' user id')
    try:
        r=models.type_count_for_user(user_id)
        print(str(r))
    except:
        print(traceback.format_exc())
    return jsonify(r)


if __name__ == '__main__':
    app.run()
