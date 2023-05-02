import asyncio
import pprint
import time

from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request
from playwright.async_api import async_playwright

from data import db_session
from data.__all_models import LoginForm
from data.__all_models import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


# Перенаправление на страницу логина
@app.route('/', methods=['GET', 'POST'])
def check():
    return redirect('/login')


# Авторизация пользователя и добавление в базу данных
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User(login=form.login.data, password=form.password.data)
        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        return redirect(url_for('home', login=form.login.data, password=form.password.data))
    return render_template('login.html', title='Авторизация', form=form)


# Отображение расписания на сегодняшний день
@app.route('/home')
async def home():
    async with async_playwright() as playwright:
        log, password = request.args.get('login'), request.args.get('password')
        webkit = playwright.chromium
        browser = await webkit.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://belgorod.vsopen.ru/app/login")
        await page.wait_for_load_state()
        await page.locator("id=login_name").fill(log)  # Ввод логина
        await page.locator("id=login_password").fill(password)  # Ввод пароля
        await page.locator('"Войти"').click()  # Нажатие на кнопку "Войти"
        await page.wait_for_load_state()
        await page.click('"Дневник"')  # Нажатие на кнопку "Дневник"
        await page.wait_for_load_state()
        time.sleep(1)

        html = await page.content()  # Получение HTML-кода страницы

        tables = await page.query_selector_all('table')  # Получение всех таблиц на странице
        dates = await page.query_selector_all('div.b-diary__day-date')  # Получение всех дат на странице
        data = []

        # Обход всех таблиц на странице
        for i, table in enumerate(tables[1:len(tables) - 1]):
            day = {}
            try:
                date = await dates[i].inner_text()
                day_of_week = date[:date.find(' ')]  # Получение дня недели
                date_string = date[date.find('(') + 1:date.find(')')]  # Получение даты
                date_format = "%d.%m.%Y"
                date_obj = datetime.strptime(date_string, date_format)
                day['date'] = date_obj
                day['day_of_week'] = day_of_week
            except IndexError:
                day['date'] = None
            rows = await table.query_selector_all('tr')
            for j, row in enumerate(rows[1:]):
                lesson = await row.query_selector_all('td.diary-day__lessons')
                try:
                    lesson_data = await lesson[0].inner_text()
                except Exception as e:
                    print(f'Произошла неожиданная ошибка:\n{e}')
                if lesson:
                    if '\n' in lesson_data:
                        day[j] = lesson_data[:lesson_data.find('\n')] if lesson_data else 'no lesson'
                    else:
                        day[j] = lesson_data if lesson_data else 'no lesson'
            data.append(day)

        pprint.pprint(data)

        order_dates = {0: 0, 1: 2, 2: 4, 3: 1, 4: 3, 5: 5}

        # сохраняем полученную страницу в файл для дальнейшего использования
        with open('temp.html', 'w') as f:
            f.write(html)

        ind_day_of_week = order_dates[datetime.today().weekday()]
        print(ind_day_of_week)
        lessons = [data[ind_day_of_week][i] for i in range(len(data[ind_day_of_week]) - 2)]
        print(lessons)

        # возвращаем расписание
        return render_template('schedule.html', less=lessons)


def main():
    db_session.global_init('db/test.db')
    app.run(debug=True)


if __name__ == '__main__':
    asyncio.run(main())
