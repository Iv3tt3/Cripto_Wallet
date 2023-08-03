from cripto_wallet import app
from flask import render_template, request, redirect, url_for, flash
from cripto_wallet.models import dao, calculator
from cripto_wallet.forms import NewForm
import sqlite3

@app.route("/")
def index():
    js_path = (app.config.get("JAVASCRIPT_PATH"))
    if js_path == "/static/js/app_v1.js" or js_path == "/static/js/app_v2.js": 
        return render_template("index.html", js_path = js_path, actual_page="index")
    else:
        dao.main_error = "Error info: JS path is not well format in the env file"
        return redirect("/fatalerror", actual_page="fatalerror")
    
@app.route("/fatalerror")
def fatal_error():
    return render_template("fatalerror.html", error = dao.main_error)

@app.route("/api/v1/transactions")
def all_transactions():
    try:
        transactions = dao.get_all_transactions()
        coin_options = app.config.get("COIN_OPTIONS_LIST")
        wallet_balance = dao.wallet_balance
        response = {
            "ok": True,
            "data": transactions,
            "coin_options": coin_options,
            "wallet_balance": wallet_balance
        }
        return response
    except sqlite3.Error as e:
        response = {
            "ok": False,
            "data": "Database error. Please, contact support\nerror info: " + str(e)
        }
        return response, 400
    except ValueError as e:
        response = {
            "ok": False,
            "data": "Please, contact support\nerror info: " + str(e)
        }
        return response, 400

@app.route("/api/v1/rate/<From_Coin>/<To_Coin>/<Amount_From>")
def get_rate(From_Coin, To_Coin, Amount_From):
    try:
        status, data = calculator.get_rate(From_Coin, To_Coin, Amount_From)
        if status:
            calculator.save_data(data)
            response = {
                "ok": True,
                "data": data
            }
            return response
        else:
            response = {
                "ok": False,
                "data": "Calculator is not avaliable at this moment.\nPlease contact support.\n\nError in CoinAPI.io request.\nMore info: " + data
            }
            return response, 400
    except Exception as e:
        response = {
                "ok": False,
                "data": "Please, contact support\nError Exception type in get rate route\n" + str(e)
            }
        return response, 400

@app.route("/api/v1/insert", methods=["POST"])
def insert_transaction():
    try:
        data_validation, error_info = calculator.validate_data(
            request.json.get("Amount_From"), 
            request.json.get("From_Coin"),
            request.json.get("To_Coin"),
            request.json.get("Amount_To"),
            )
        if data_validation:
            dao.insert_transaction(calculator)
            response = {
                "ok": True,
                "data": "SUCCESSFUL!\n\nYour purchase order has been completed successfully.\nPlease refresh website page"
            }
            return response, 201
        else:
            response = {
                    "ok": False,
                    "data": error_info
                }
            return response, 400
        
    except sqlite3.Error as e:
        response = {
            "ok": False,
            "data": "Your purchase has NOT been completed.\nPlease contact support\n\nMore info: DB is currently not available.\n" + str(e)
        }
        return response, 400
    
    except ValueError as e:
        response = {
                    "ok": False,
                    "data": "Your purchase has NOT been completed.\nPlease contact support\n\nMore info: " + str(e)
                }
        return response, 400
    
    except Exception as e:
        response = {
                "ok": False,
                "data": "Your purchase has NOT been completed.\nPlease contact support\n\nMore info: Exception type in insert trasaction route\n" + str(e)
            }
        return response, 400
    
@app.route("/api/v1/status")
def investment_status():
    try:
        data = dao.wallet_status()
        response = {
            "ok": True, 
            "data": data
        }
        return response
        
    except ValueError as e:
        response = {
            "ok": False, 
            "data": "Your wallet status is not available. Please, contact support\nMore info: ValueError in status route"
        }
        return response, 400
        
    except Exception as e:
        response = {
                "ok": False,
                "data": "Your wallet status is not available. Please, contact support\nMore info: Exception type in status route\n" + str(e)
            }
        return response, 400
    
@app.route("/alltransactions")
def alltransactions():
    try:
        info_msg = ""
        transaction_list = dao.get_all_transactions()
        if len(transaction_list)==0:
            info_msg = "No transactions in your wallet yet"
        return render_template("alltransactions.html", page="- Transactions", transactions=transaction_list, info_msg=info_msg, actual_page="alltransactions")
    except ValueError as e:
        flash("Problems with our data file")
        flash(str(e))
        info_msg = "Currently not available <br> Sorry for the inconvenience <br> Please, contact support"
        return render_template("alltransactions.html",page="- Transactions", transactions=[], info_msg=info_msg, actual_page="alltransactions")
    except Exception as e:
        flash(f"Fatal error {str(e)}")
        return render_template("fatalerror.html",page="- Fatal Error", actual_page="fatalerror")

@app.route("/new_transaction", methods=["GET", "POST"])
def new_transaction():
    try:
        form = NewForm()
        if request.method == 'GET':
            return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new")
        else:
            if form.validate():
                if form.purchase_button.data:
                    data_validation, error_info = calculator.validate_data(
                        form.amount.data, 
                        form.coinFrom.data,
                        form.coinTo.data,
                        calculator.Amount_To,
                    )
                    if data_validation or calculator.click == 1:
                        dao.insert_transaction(calculator)
                        calculator.click = 0
                        return redirect(url_for("alltransactions"))
                    else:
                        info_msg = "The data in calculator is different from the purchase resume. Please check your Purchase Resume.\nIf it is correct press again Purchase.\nIf it is not correct press Calcul"
                        form.submit_button.data = True
                        calculator.click = 1
                        return render_template("form_new.html",page="- New transaction", form=form, info_msg=info_msg, actual_page="form_new", calculator=calculator)
                elif form.cancel_button.data:
                    calculator.reset_data()
                    return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new", calculator=calculator)
                else:
                    try:
                        status, data = calculator.get_rate(form.coinFrom.data, form.coinTo.data, form.amount.data)
                        if status:
                            calculator.save_data(data)
                            return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new", calculator=calculator)
                        else:
                            flash(f"There is a problem with the query server, please try again later {data}")
                            return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new", calculator=calculator)
                    except ValueError as e:
                        flash(f"There is a problem with the query server:{str(e)}")
                        return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new", calculator=calculator)
            else:
                form.submit_button.data = False 
                return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new", calculator=calculator)
    except ValueError as e:
        flash(str(e))
        return render_template("form_new.html",page="- New transaction", form=form, actual_page="form_new", calculator=calculator)

@app.route("/status")
def status():
    try:
        data = dao.wallet_status()
        transactions = dao.get_all_transactions()
        if len(transactions)>0:
            return render_template("status.html",page="- Wallet Status", data=data, info_msg='', actual_page="status")
        else:
            info_msg = "No transactions in your wallet yet"
            return render_template("status.html",page="- Wallet Status", data=data, info_msg=info_msg, actual_page="status")
    except ValueError as e:
        flash(str(e))
        return render_template("status.html",page="- Wallet Status", data=data, info_msg='', actual_page="status")
    except Exception as e:
        flash(f"Fatal error {str(e)}")
        return render_template("fatalerror.html",page="- Fatal Error", actual_page="fatal_error")
