import markdown
import datetime
from flask import Flask, json, redirect, render_template, request, url_for, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
from flask_cors import cross_origin

load_dotenv()
app = Flask(__name__)


# Configuration for MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)


@app.route('/')
def home():
    cursor = mysql.connection.cursor()
    # Adjust the query to match your schema
    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()
    cursor.close()

    return render_template('index.html', exams=exams)


@app.route('/news')
def news():
    selected_date = datetime.date.today()
    return render_template('news.html', selected_date=selected_date)


@app.route('/news', defaults={'date_str': None})
@app.route('/news/<date_str>')
def get_news(date_str):
    print(date_str)
    if date_str is None:
        selected_date = datetime.date.today()
    else:
        try:
            selected_date = datetime.datetime.strptime(
                date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format", 400

    cursor = mysql.connection.cursor()

    selected_datetime_start = datetime.datetime.combine(
        selected_date, datetime.time.min)
    selected_datetime_end = datetime.datetime.combine(
        selected_date, datetime.time.max)

    cursor.execute("SELECT * FROM news WHERE date_update BETWEEN %s AND %s",
                   (selected_datetime_start, selected_datetime_end))

    news = cursor.fetchall()
    cursor.close()

    # Convert news content and summary to markdown
    formatted_news = []
    for news_item in news:
        # Assuming the content is in the third column
        news_content = news_item[2]
        # Assuming the summary is in the seventh column
        news_summary = news_item[6]
        news_content_md = markdown.markdown(news_content)
        news_summary_md = markdown.markdown(news_summary)
        # Add both the markdown content and summary to the tuple
        formatted_news.append(
            (news_item[0], news_item[1], news_content_md, news_summary_md, *news_item[3:6], *news_item[7:]))

    return render_template('news_partial.html', news=formatted_news, selected_date=selected_date)


@app.route('/add_news45', methods=['GET', 'POST'])
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

        # Redirect to the news page
        return redirect(url_for('get_news', date_str=None))

    return render_template('add_news.html')


@app.route('/add_exam45', methods=['GET', 'POST'])
def add_exam():
    if request.method == 'POST':
        name = request.form['name']
        exam_date = request.form['exam_date']
        notification_date = request.form['notification_date']
        application_start_date = request.form['application_start_date']
        application_end_date = request.form['application_end_date']
        notification_link = request.form['notification_link']
        tag = request.form['tag']
        summary = request.form['summary']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO exams (name, exam_date, notification_date, application_start_date, application_end_date, notification_link, tag, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, exam_date, notification_date, application_start_date, application_end_date, notification_link, tag, summary))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('/'))  # Redirect to the exams page

    return render_template('add_exam.html')


@app.route('/study_material/computer_science',methods=['POST','GET'])
def computer_science():
    return render_template('computer_science.html')

# api for different applications
@app.route('/api/fetch-news')
@cross_origin()
def api_fetch_news():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM news")
    news = cursor.fetchall()
    cursor.close()

 
    news_list = []
    for item in news:
        news_item = {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "date": item[3]
            # Add other fields as needed
        }
        news_list.append(news_item)

    return jsonify(news_list)

@app.route('/api/news', defaults={'date_str': None})
@app.route('/api/news/<date_str>')
@cross_origin()
def get_news_api(date_str):
    if date_str is None:
        selected_date = datetime.date.today()
    else:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    cursor = mysql.connection.cursor()

    selected_datetime_start = datetime.datetime.combine(selected_date, datetime.time.min)
    selected_datetime_end = datetime.datetime.combine(selected_date, datetime.time.max)

    cursor.execute("SELECT * FROM news WHERE date_update BETWEEN %s AND %s",
                   (selected_datetime_start, selected_datetime_end))

    news = cursor.fetchall()
    cursor.close()

    news_list = []
    for row in news:
        news_item = {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "date": row[3],
            "categories":row[4]
        }
        news_list.append(news_item)

    return jsonify(news_list)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
