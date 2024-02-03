from ast import LShift
import shlex
import subprocess
from flask import make_response, render_template_string, Flask, url_for, request, render_template, redirect, session
from markupsafe import escape
import mysql.connector
import re
import requests
import secrets
import base64
import sys
from werkzeug.serving import run_simple
import jinja2, re, hashlib
from jinja2 import Template
import os 
from flask import send_from_directory  
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


app.config['DEBUG'] = True 


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'blog'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Kullanıcı dostu bir imleç

# Bağlantı havuzu oluştur
mysql = MySQL(app)

   

@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/', methods=['GET'])
def promotion():
            return render_template('index.html')

    
    
@app.route('/home', methods=['GET'])
def home():
    try:
        # Bağlantıyı al
        cursor = mysql.connection.cursor()

        # SQL sorgusu
        query = "SELECT * FROM posts"
        cursor.execute(query)

        # Sonuçları al
        posts = cursor.fetchall()

        # Bağlantıyı kapat
        cursor.close()

        if request.method == 'GET':
            return render_template('anasayfa.html', posts=posts, title='Ana Sayfa')
    except Exception as e:
        return str(e)
    
    
    

@app.route('/<id>', methods=['GET'])
def posts(id):
    blacklist = re.search('(sleep|and|or|=)', str(id), re.IGNORECASE)
    if blacklist:
        return render_template('blocklist.html', title='Error Page')
    
    else:
        try:
            # Bağlantıyı al
            cursor = mysql.connection.cursor()

            # SQL sorgusu
            query = "SELECT * FROM posts WHERE id REGEXP %s" % id
            cursor.execute(query)

            # Sonuçları al
            posts = cursor.fetchall()

            # Bağlantıyı kapat
            cursor.close()

            return render_template('anasayfa.html', posts=posts, title='Post')
        except Exception as e:
            return str(e)
     


@app.route('/about/1', methods=['GET', 'POST'])
def about():
    try:
        # Bağlantıyı al
        cursor = mysql.connection.cursor()

        # SQL sorgusu
        query = "SELECT * FROM about WHERE id=1"
        cursor.execute(query)

        # Sonuçları al
        abouts = cursor.fetchall()

        # Bağlantıyı kapat
        cursor.close()

        header = request.headers.get('X-Forwarded-For', '')
        
        if request.method == 'GET':
            return render_template('hakkimda.html', abouts=abouts, title='Kimim ben?')
        elif request.method == 'POST' and header:
            return str(requests.get(header).text)
    except Exception as e:
        return str(e)
    
    

@app.route('/about/<int:id>', methods=['GET'])
def abouts(id):
    blacklist = re.search('(union|and|or|sleep|=)', str(id), re.IGNORECASE)
    if blacklist:
        return render_template('blocklist.html', title='Hooop')
    
    else:
        try:
            # Bağlantıyı havuzdan al
            cursor = mysql.connection.cursor()
            
            # SQL sorgusu
            query = "SELECT * FROM about WHERE id = %s"
            cursor.execute(query, (id,))
            
            # Sonuçları al
            abouts = cursor.fetchall()
            
            # Bağlantıyı kapat
            cursor.close()
            
            return render_template('hakkimda.html', abouts=abouts, title='Hakkımda')
        except Exception as e:
            # Hata durumunda geri bildirim
            return str(e)



@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' in session:
        ping = request.args.get('echo')
        if ping:
            args = shlex.split(ping)
            try:
                result = subprocess.check_output(args, shell=False, text=True, stderr=subprocess.STDOUT)
                return render_template('admin.html', title=result)
            except subprocess.CalledProcessError as e:
                return render_template('admin.html', title=f'Hata: {e.output}')
        else:
            return render_template('admin.html', title='Kabuk komutunun çıktısı:')
    return render_template('anasayfa.html', title='Admin Sayfası')


@app.route('/login', methods=['GET', 'POST'])
def login():
    url = request.args.get('next', '')
    if 'mail' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        if request.form['mail'] and request.form['password']:
            try:
                # Bağlantıyı al
                cursor = mysql.connection.cursor()

                # SQL sorgusu
                query = "SELECT * FROM users WHERE mail = %s AND password = %s"
                cursor.execute(query, (request.form['mail'], request.form['password'],))

                # Sonuçları al
                user = cursor.fetchone()

                # Bağlantıyı kapat
                cursor.close()

                if user:
                    session['user_id'] = user['mail']
                    session['kul_id'] = user['id']
                    return redirect(url_for('admin'))
            except Exception as e:
                return str(e)

    if url:
        return redirect(url)

    return render_template('login.html', title='Login Sayfası')



@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form["search"]
        blacklist = re.search('(script|SCRIPT)', str(search_query))
        if blacklist:
            return render_template('blocklist.html', title='Hooop')
        else:
            try:
                # Bağlantıyı al
                cursor = mysql.connection.cursor()

                # SQL sorgusu
                sql_query = "SELECT * FROM posts WHERE title LIKE %s"
                cursor.execute(sql_query, ('%' + search_query + '%',))

                # Sonuçları al
                results = cursor.fetchall()

                # Bağlantıyı kapat
                cursor.close()

                if results:
                    return render_template("search.html", posts=results)
                else:
                    return render_template("search.html", search_query=search_query, template=render_template_string(search_query))
            except Exception as e:
                return str(e)

    return render_template("search.html", posts=[])
    

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


tweets = []
@app.route('/xss', methods=['GET', 'POST'])
def xss():
    global tweets  
    if request.method == 'POST':
        tweet = request.form['tweet']
        tweets.append(tweet)

    elif request.method == 'GET':
        tweets = []

    return render_template('xss.html', title='XSS Sayfası', tweets=tweets)


    

@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')




@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6619,debug=True)