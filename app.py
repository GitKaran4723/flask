import datetime
from flask import Flask, json, redirect, render_template, request, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configuration for MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'newsapp'

mysql = MySQL(app)

@app.route('/')
def home(): 
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM exams")  # Adjust the query to match your schema
    exams = cursor.fetchall()
    cursor.close()
    
    return render_template('index.html', exams=exams)

@app.route('/news')
def news():
    selected_date = datetime.date.today()
    return render_template('news.html', selected_date=selected_date)

import markdown
@app.route('/news', defaults={'date_str': None})
@app.route('/news/<date_str>')
def get_news(date_str):
    if date_str is None:
        selected_date = datetime.date.today()
    else:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format", 400

    cursor = mysql.connection.cursor()

    selected_datetime_start = datetime.datetime.combine(selected_date, datetime.time.min)
    selected_datetime_end = datetime.datetime.combine(selected_date, datetime.time.max)

    cursor.execute("SELECT * FROM news WHERE date_update BETWEEN %s AND %s", 
                   (selected_datetime_start, selected_datetime_end))
    
    news = cursor.fetchall()
    cursor.close()
    
    # Convert news content and summary to markdown
    formatted_news = []
    for news_item in news:
        news_content = news_item[2]  # Assuming the content is in the third column
        news_summary = news_item[6]  # Assuming the summary is in the seventh column
        news_content_md = markdown.markdown(news_content)
        news_summary_md = markdown.markdown(news_summary)
        # Add both the markdown content and summary to the tuple
        formatted_news.append((news_item[0], news_item[1], news_content_md, news_summary_md, *news_item[3:6], *news_item[7:]))

    print(formatted_news)    

    return render_template('news_partial.html', news=formatted_news, selected_date=selected_date)

@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        subjects = request.form['subjects']
        author = request.form['author']
        summary = request.form['summary']
        date_update = request.form['date_update']

        if not date_update:
            date_update = datetime.date.today().strftime('%Y-%m-%d')

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO news (title, content, date_update, subjects, author, summary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, content, date_update, json.dumps(subjects.split(',')), author, summary))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('get_news', date_str=None))  # Redirect to the news page

    return render_template('add_news.html')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
