import asyncio
import time

from flask import Flask, render_template, redirect
from playwright.async_api import async_playwright

from data import db_session
from data.__all_models import LoginForm
from data.__all_models import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/', methods=['GET', 'POST'])
def check():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User(login=form.login.data, password=form.password.data)
        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        return redirect('/home')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/home')
async def home():
    async with async_playwright() as playwright:
        webkit = playwright.chromium
        browser = await webkit.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://belgorod.vsopen.ru/app/login")
        await page.wait_for_load_state()
        await page.locator("id=login_name").fill("Trikula_AK_3061")
        await page.locator("id=login_password").fill("TrikulaAK3061")
        await page.locator('"Войти"').click()
        await page.wait_for_load_state()
        await page.click('"Дневник"')
        await page.wait_for_load_state()
        time.sleep(1)
        html = await page.content()
        with open('temp.html', 'w') as f:
            f.write(html)
        return html


def main():
    db_session.global_init('db/test')
    app.run(debug=True)


if __name__ == '__main__':
    asyncio.run(main())
