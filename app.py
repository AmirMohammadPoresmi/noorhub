from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import jdatetime
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from io import BytesIO
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()
# CLOUDINARY_CLOUD_NAME
# CLOUDINARY_API_KEY
# CLOUDINARY_API_SECRET
# CLOUDINARY_DB_NAME

# power by cloudinary.com
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"), 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"), 
    secure = True
)

app = Flask(__name__)

zekrhaye_hafte = {
    'شنبه':'یا رَبِّ الْعالَمِین',
    'یک‌شنبه':'یا ذَالجَلالِ وَ اْلاِکْرام',
    'دوشنبه':'یا قاضیَ الحاجات',
    'سه‌شنبه':'یا أَرْحَمَ الرَّاحِمِین',
    'چهارشنبه':'یا حَیُّ یا قَیّومُ',
    'پنج‌شنبه':'لا إِلهَ إِلَّا اللَّهُ المَلِک الحقّ المُبین',
    'جمعه':'الّلهُمَّ صَلِّ عَلَی مُحَمَّدٍ وَآلِ مُحَمَّدٍ و عجل فرجهم'
}

db_version = None
def get_url_db():
    return f"http://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/raw/upload/{'v'+str(db_version)+'/' if db_version else ''}{os.getenv('CLOUDINARY_DB_NAME')}.json"

def load_db():
    response = requests.get(get_url_db())
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code

def write_db(new_data:dict):
    global db_version
    file = BytesIO(json.dumps(new_data).encode('utf-8'))
    result = cloudinary.uploader.upload(
        file,
        resource_type="raw",
        public_id="database",
        format='json'
    )
    db_version = result['version']
    return result

number_of_posts = 0
try:
    number_of_posts = len(load_db()['images'])
except:
    write_db({'images':[]})
if not db_version:
    response = requests.get(
        f"https://api.cloudinary.com/v1_1/{os.getenv('CLOUDINARY_CLOUD_NAME')}/resources/raw/upload/{os.getenv('CLOUDINARY_DB_NAME')}.json",
        auth=HTTPBasicAuth(os.getenv("CLOUDINARY_API_KEY"), os.getenv("CLOUDINARY_API_SECRET"))
    )
    if response.status_code == 200:
        db_version = response.json()['version']
    else:
        print('error to found db version :'+str(response.status_code))

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

def add_post(title:str, publisher:str, file):
    global number_of_posts
    jdatetime.set_locale(jdatetime.FA_LOCALE)
    db = load_db()
    result = cloudinary.uploader.upload(
        file,
        public_id = str(number_of_posts)
    )
    db['images'].append(
        [
            number_of_posts,
            result['secure_url'],
            title,
            publisher,
            0,
            jdatetime.datetime.now().strftime(f'%Y/%B/%d %A %H:%M')
            ]
    )
    write_db(db)
    number_of_posts += 1
    return number_of_posts - 1

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('index'))
        title = request.form['title']
        publisher = request.form['publisher']
        return redirect(url_for('index',id=add_post(title, publisher, file)))

    post_id = request.args.get("id")
    if post_id:
        post_id = int(post_id)
        add_view(post_id)
        selected_post=load_image(post_id)
        rooz = None
        zekr_rooz = None
    else:
        jdatetime.set_locale(jdatetime.FA_LOCALE)
        rooz = jdatetime.date.today().strftime('%A')
        zekr_rooz = zekrhaye_hafte[rooz]
        selected_post=None
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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)