from .models import Transaction
from django import forms

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']
        
    # function ta bujlam na 
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True # ai field disabled thakbe 
        self.fields['transaction_type'].widget = forms.HiddenInput # user ar theke hide kora thakbe
        
        
    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance # ai balance alo kotha kheke
        return super().save()
        
        
    
class DepositForm(TransactionForm):
    
    def clean_amount(self): # akine clean_amount akta build in function  clean _ dawar pore ja kono model ar object nia ja kono validition ar kaj kora jai
        min_deposit_amount = 100
        amount  = self.cleaned_data.get('amount') # cleaned_data ar madhome user ar fill up kora form ar data nia aslam
        
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at last {min_deposit_amount} $'
                
            )
        return amount
    
    
    
class WithdrawForm(TransactionForm):
    
    def clean_amount(self):
        account = self.account # ai account ta holo models ar account 
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance # ai balance holo models ar balance
        amount = self.cleaned_data.get('amount')
        
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )
            
        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )
            
        if amount > balance:
            raise forms.ValidationError(
                f'You have { balance} $ in your account'
                'You can not withdraw more then your account balance'
            )
        return amount
    
    

class LoanRequestForm(TransactionForm):
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        return amount
    
    