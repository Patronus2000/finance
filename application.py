import decimal
import os
import hashlib
import binascii
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import null
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Democracy97#@localhost:3306/stocks'
# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# We are giving ourselves access to a database stored in finance.db This web app uses a paradigm called Model View Control
db = SQLAlchemy(app)
# Model keeps track of the data in tables, View which determines what user sees, Controller, application.py that connects M & V
# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Query infos from database
    rows = db.engine.execute(
        "SELECT * FROM stocks WHERE user_id = %s", session["user_id"])
    cash = db.engine.execute(
        "SELECT cash FROM users WHERE id = %s", session["user_id"])
    # Create a list of dictionaries to store the data
    stocks = []
    total = 0

    for row in rows:
        # Lookup the stock
        stock = lookup(row["symbol"])
        total += row["amount"]
        stock['amount'] = (row["amount"])

        # Add the stock to the list
        stocks.append(stock)
    # Calculate the total value of the stocks
    # Loop through the stocks

    # Calculate the total value of the cash
    c = 0
    for cash in cash:
        total += cash["cash"]
        c += cash["cash"]
    # Render the index.html template with the stocks and cash
    print(stocks)
    print(c)
    print(total)
    return render_template("index.html", stocks=stocks, cash=c, total=10000)

    # # pass a list of lists to the template page, template is going to iterate it to extract the data into a table
    # total = cash
    # stocks = []
    # for index, row in enumerate(rows):
    #     stock_info = lookup(row['symbol'])

    #     # create a list with all the info about the stock and append it to a list of every stock owned by the user
    #     stocks.append(list((stock_info['symbol'], stock_info['name'], row['amount'],
    #                   stock_info['price'], round(stock_info['price'] * row['amount'], 2))))
    #     total += stocks[index][4]

    # return render_template("index.html", stocks=stocks, cash=round(cash, 2), total=round(total, 2))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():  # This function handles a form which user needs to buy and handles the logic of buying the stock
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = lookup(request.form.get("symbol"))['symbol']
        if not symbol:
            return apology("Not a valid symbol")
        price = (lookup(symbol)['price'])
        amount = int(request.form.get("shares"))
        cash = db.engine.execute(
            "Select cash FROM users WHERE id = %s", session["user_id"])
        for row in cash:
            cash = row[0]
        cash_after = cash - (price*decimal.Decimal(amount))
        if cash_after < 0:
            return apology("Amount insufficent")
        rows = db.engine.execute(
            "SELECT amount FROM stocks WHERE user_id = %s AND symbol = %s", (session["user_id"], symbol))
        c = None
        for row in rows:
            print(row)
            c = row[0]
        print(c)
        if not c:
            db.engine.execute("INSERT INTO stocks(user_id, symbol, amount) values (%s, %s, %s)",
                              (session["user_id"], symbol, amount))

        else:
            stock_after = int(c)
            amount += stock_after
            db.engine.execute("UPDATE stocks SET amount = %s WHERE user_id = %s AND symbol = %s",
                              (amount, session["user_id"], symbol))

        db.engine.execute("UPDATE users SET cash = %s WHERE id = %s",
                          (cash_after, session["user_id"]))
        db.engine.execute("INSERT INTO transactions(user_id,symbol,amount,value) values (%s, %s, %s,%s)",
                          (session["user_id"], symbol, amount, price*amount))
        flash("Bought!")
        return redirect("/")


@app.route("/history")
@login_required
def history():
    # Histroy of transactions
    rows = db.engine.execute(
        "SELECT * FROM transactions WHERE user_id = %s", (session["user_id"]))

    # pass a list of lists to the template page, template is going to iterate it to extract the data into a table
    transactions = []
    for row in rows:
        stock_info = lookup(row['symbol'])
        print(row)

        # create a list with all the info about the transaction and append it to a list of every stock transaction
        transactions.append(list(
            (stock_info['symbol'], stock_info['name'], row['amount'], row['value'], row['date'])))
    print(transactions)

    # redirect user to index page
    return render_template("history.html", transactions=transactions)


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.engine.execute(
            "SELECT * FROM users WHERE username = %s", (request.form.get("username")))

        # Ensure username exists and password is correct

        c = 0
        for user in rows:
            print(user)
            c = c+1
            session["user_id"] = user[0]
        if c == 0 or not check_password_hash(user[2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
        #     return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        # This basically says take the first row and get the value of the id column

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        # Query database for username
        rows = db.engine.execute(
            "SELECT * FROM stock_price WHERE symbol = %s", (symbol))

        # Ensure username exists and password is correct

        c = 0
        name = ""
        price = ""
        for row in rows:
            print(row)
            c = c+1
            name = row[0]
            price = row[1]
        if c == 0:
            return None
        return {"name": name, "price": price, "symbol": symbol}
    except:
        return None


@ app.route("/quote", methods=["GET", "POST"])
@ login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html")
    else:
        # If symbol not present
        if not request.form.get("symbol"):
            return apology("MISSING SYMBOL", 400)
        # Looking up the symbol
        stock = lookup(request.form.get("symbol"))
        # If lookup returns none
        if not stock:
            return apology("INVALID SYMBOL", 400)
        # Passing variable stock to our quoted.html file
        return render_template("quoted.html", stock=stock)


@ app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check for username
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Check for password if typed in
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Check if confirmation typed in
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)
        # Check if password = confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("PASSWORDS DO NOT MATCH", 403)
        # checking if username exists
        row = db.engine.execute(
            "SELECT * FROM users WHERE username = %s", (request.form.get("username")))
        c = 0
        for user in row:
            c = c+1
        if c != 0:
            return apology("username exists", 403)
        # inserting the values into the database
        db.engine.execute("INSERT INTO users (username,hash) values (%s,%s)",
                          (request.form.get("username"), generate_password_hash(request.form.get("password"))))
        # getting the id
        rows = db.engine.execute("SELECT * FROM users WHERE username = %s",
                                 (request.form.get("username")))
        for row in rows:
            session["user_id"] = row[0]
        return redirect("/")
    else:
        return render_template("register.html")


@ app.route("/sell", methods=["GET", "POST"])
@ login_required
def sell():
    if request.method == "GET":
        # query database with the transactions history
        # rows = db.engine.execute("SELECT symbol, amount FROM stocks WHERE user_id = :user",
        #                          user=session["user_id"])
        rows = db.engine.execute("SELECT symbol, amount FROM stocks WHERE user_id = %s",
                                 session["user_id"])

        # create a dictionary with the availability of the stocks
        stocks = {}
        for row in rows:
            stocks[row['symbol']] = row['amount']

        return render_template("sell.html", stocks=stocks)
    else:
        symbol = request.form.get("symbol")
        amount = int(request.form.get("amount"))
        amount_beforeRow = db.engine.execute("SELECT amount FROM stocks WHERE user_id = %s AND symbol = %s",
                                             session["user_id"], symbol)
        value = round(decimal.Decimal(amount) * lookup(symbol)["price"])
        amount_before = None
        # loop amount_before to get the amount of stocks
        for row in amount_beforeRow:
            amount_before = row['amount']
        if amount_before is not None:
            amount_after = amount_before - amount
        if amount_after < 0:
            return apology("Invalid amount", 403)

        elif amount_after == 0:
            db.engine.execute("DELETE FROM stocks WHERE user_id = %s AND symbol = %s",
                              session["user_id"], symbol)
        else:
            db.engine.execute("UPDATE stocks SET amount = %s WHERE user_id = %s AND symbol = %s",
                              amount_after, session["user_id"], symbol)
        cash = db.engine.execute("SELECT cash FROM users WHERE id = %s",
                                 session["user_id"])
        cash_before = None
        for row in cash:
            cash_before = row['cash']
        if cash_before is not None:
            cash_after = cash_before + value
        db.engine.execute("UPDATE users SET cash = %s WHERE id = %s",
                          cash_after, session["user_id"])
        db.engine.execute("INSERT INTO transactions(user_id,symbol,amount,value) VALUES (%s, %s, %s,%s)",
                          session["user_id"], symbol, amount, value)
        flash("Sold!")
        return redirect("/")


@ app.route("/wishlist/<symbol>", methods=["GET", "POST"])
@ login_required
def wishlist(symbol):
    print(symbol)
    if request.method == "POST":
        # check if record exists
        rows = db.engine.execute("SELECT * FROM wishlist WHERE user_id = %s AND symbol = %s",
                                 session["user_id"], symbol)
        c = 0
        for row in rows:
            c = c+1
        if c == 0:
            db.engine.execute("INSERT INTO wishlist(user_id,symbol) VALUES (%s, %s)",
                              session["user_id"], symbol)
            flash("Added to wishlist!")
            return redirect("/wishlist")
        else:
            flash("Already in wishlist!")
            return redirect("/wishlist")


@app.route("/wishlist", methods=["GET"])
@login_required
def wishlisted():
   # select from wishlist
    rows = db.engine.execute("SELECT s.* FROM stock_price s inner join wishlist w on s.symbol = w.symbol  WHERE w.user_id = %s",
                             session["user_id"])
    stocks = []
    for row in rows:
        stocks.append(row)
    print(stocks)

    return render_template("wishlisted.html", stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
