from flask_wtf  import FlaskForm
from wtforms import SelectField, FloatField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from cripto_wallet.models import dao, app_coins

coins = [("option","Select an option")]
for value, coin in app_coins:
    coins.append((value, coin))



class NewForm(FlaskForm):
    amount = FloatField("Amount", description="Amount you want to invest", validators = [DataRequired("Must be a number")], render_kw={"placeholder": "0.00"})
    coinFrom = SelectField("From", validators = [DataRequired("Select an option")], choices=coins, description="Coin you want to sell")
    coinTo = SelectField("To", validators = [DataRequired("Select an option")], choices=coins, description="Coin you want to buy")
    submit_button = SubmitField("Calcul")
    purchase_button =  SubmitField("Confirm purchase")
    cancel_button = SubmitField("Cancel")
    

    def validate_amount(self,field):
        if field.data<=0:
            raise ValidationError("Must be positive number")
        dao.get_all_transactions()
        if self.coinFrom.data != "option" and self.coinTo.data != "option":
            amount = dao.wallet_balance[self.coinFrom.data][1] - dao.wallet_balance[self.coinFrom.data][0]
            if self.coinFrom.data != "EUR" and field.data > amount:
                raise ValidationError(f"Not enough balance of {self.coinFrom.data} in your wallet. Your current balance is {amount} {self.coinFrom.data}")
        
    def validate_coinFrom(self, field):
        if field.data == "option":
            raise ValidationError("Select an option")
        
    def validate_coinTo(self, field):
        if field.data == "option":
            raise ValidationError("Select an option")
        if field.data == self.coinFrom.data:
            raise ValidationError("Select a different coin in To than in From")