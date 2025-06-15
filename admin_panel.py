from flask import Flask, render_template_string
from questions import fetch_all_questions

app = Flask(__name__)

TEMPLATE = """
<html>
<head>
    <title>قاعدة المعرفة - لوحة مدير البوت</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>جميع الأسئلة والأجوبة</h1>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th>
            <th>القسم</th>
            <th>السؤال</th>
            <th>الإجابة</th>
        </tr>
        {% for q in questions %}
        <tr>
            <td>{{q[0]}}</td>
            <td>{{q[1]}}</td>
            <td>{{q[2]}}</td>
            <td>{{q[3]}}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def index():
    questions = fetch_all_questions()
    return render_template_string(TEMPLATE, questions=questions)

if __name__ == "__main__":
    app.run(debug=True, port=5001)