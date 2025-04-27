from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from werkzeug.utils import secure_filename
import jdatetime

zekrhaye_hafte = {
    'شنبه':'یا رَبِّ الْعالَمِین',
    'یک‌شنبه':'یا ذَالجَلالِ وَ اْلاِکْرام',
    'دوشنبه':'یا قاضیَ الحاجات',
    'سه‌شنبه':'یا أَرْحَمَ الرَّاحِمِین',
    'چهارشنبه':'یا حَیُّ یا قَیّومُ',
    'پنج‌شنبه':'لا إِلهَ إِلَّا اللَّهُ المَلِک الحقّ المُبین',
    'جمعه':'الّلهُمَّ صَلِّ عَلَی مُحَمَّدٍ وَآلِ مُحَمَّدٍ و عجل فرجهم'
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'

number_of_posts = len([f for f in os.listdir('static/images/') if os.path.isfile(os.path.join('static/images/', f))])

def load_db():
    with open('database.json', encoding='utf-8') as file:
        return json.loads(file.read())
    
def write_db(new_data:dict):
    with open('database.json', '+w', encoding='utf-8') as file:
        file.write(json.dumps(new_data))

def load_image(id:int):
    return load_db()['images'][id]

def load_images(start:int=0, load_number:int=0, reverse:bool=True):
    global number_of_posts
    posts = load_db()['images']
    if reverse:
        posts = posts[::-1]
    posts = posts[start: start+load_number if load_number else None]
    return posts , False if start+load_number >= number_of_posts else True

def add_view(id:int):
    db = load_db()
    db['images'][id][4] += 1
    write_db(db)

def add_post(format_:str, title:str='hi', publisher:str='none'):
    global number_of_posts
    jdatetime.set_locale(jdatetime.FA_LOCALE)
    db = load_db()
    db['images'].append(
        [
            str(len(db['images'])),
            format_,
            title,
            publisher,
            0,
            jdatetime.datetime.now().strftime(f'%Y/%B/%d %A %H:%M')
            ]
    )
    write_db(db)
    number_of_posts += 1

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('index'))

        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('index'))
        filename = secure_filename(file.filename)
        format_ = os.path.splitext(filename)[1][1:]
        id_ = str(len(load_db()['images']))
        filename = id_ + '.' + format_
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        title = request.form['title']
        publisher = request.form['publisher']
        add_post(format_, title, publisher)
        return redirect(url_for('index',id=id_))

    post_id = request.args.get("id")
    if post_id:
        post_id = int(post_id)
        add_view(post_id)
        selected_post=load_image(post_id)
        rooz = None
        zekr_rooz = None
    else:
        selected_post=None
        jdatetime.set_locale(jdatetime.FA_LOCALE)
        rooz = jdatetime.date.today().strftime('%A')
        print(rooz)
        zekr_rooz = zekrhaye_hafte[rooz]
    return render_template('index.html', selected_post=selected_post, rooz=rooz, zekr_rooz=zekr_rooz)

@app.route('/load')
def load_posts():
    try:
        last_post = int(request.args.get('last_post'))
        load_post_number = int(request.args.get('number'))
        posts , has_more = load_images(last_post, load_post_number)
        return jsonify({'html': render_template('load.html',posts = posts), 'has_more': has_more})
    except Exception as e:
        return jsonify({'html': e, 'has_more': True})

if __name__ == '__main__':
    app.run(debug=True)