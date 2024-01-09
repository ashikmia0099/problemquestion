from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from transactions.models import Transaction
from transactions.constants import DEPOSIT,WITHDRAWAL,LOAN,LOAN_PAID
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime    
from django.db.models import Sum
from django.views import View
from django.urls import reverse_lazy
from django.utils import timezone
from transactions.forms import(
    DepositForm,
    WithdrawForm, 
    LoanRequestForm,
)


# ai view ke inharit kore depositel, withdraw, loan ar kaj golo korbo
class TransactionCreateMixin(LoginRequiredMixin, CreateView):  #LoginRequiredMixin use kora hoice kono login user sara ai class kew use korte parbe na
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')
    
    
    def get_form_kwargs(self):  # jokon form ar kono boject nia koj korbo tokon get_form_kwargs used kora lage
         kwargs = super().get_form_kwargs()
         kwargs.update({
             'account': self.request.user.account
         })
         return kwargs
     
     
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title' : self.title
        })
        return context
     
class DepositMoneyView(TransactionCreateMixin):
    from_class = DepositForm
    title = 'Deposit'
    
    
    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account # ai line ar mane holo user ar kas theke tar account nilam
        account.balance += amount
        account.save(
            update_fields = [
                'balance'
                ]
        )
        messages.success(self.request, f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully')
        return super().form_valid(form)



class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'
    
    
    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        # account = self.request.user.account # ai line ar mane holo user ar kas theke tar account nilam
        # account.balance -= amount
        
        # account.save(
        #     update_fields = ['balance']
        # )
        # messages.success(self.request, f'Successfully withdrow {amount} $ ')
        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )

        return super().form_valid(form)



class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'
    
    
    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(account = self.request.user.account,transaction_type =3, loan_approve = True).count()
        
        if current_loan_count >= 3:
            return HttpResponse("You have crossed your loan")
        messages.success(self.request, f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully')

        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin,ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0
    
    def get_queryset(self):
        
        queryset = super().get_queryset().filter(account = self.request.user.account) # ai line ar mane holo jodi user kono type filter na kore tahole take all transactions dakabo
        
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:  # ar mana holo jodi start_date_str and end_date_str thake tahole filter kora hobe
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp_date_gte = start_date,timestamp_date_lte = end_date ) ## ai line a get mane holo gretherthen and let mane holo lesthen
            
            self.balance = Transaction.objects.filter(timestamp_date_gte = start_date, timestamp_date_lte = end_date).aggregate(Sum('amount'))['amount_sum']
            
        else:
            self.balance = self.request.user.account.balance
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account' : self.request.user.account
        })
        
        return context
    
    
class PayLoanView(LoginRequiredMixin, View):
    
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id = loan_id)  # get_object_or_404 ar mane holo jodi ami ai id ar loan pai tahola dakabo na hole bolbo nai 

        if loan.loan_approve: # ar mane lone jodi ture hoi tahol bitorer kaj jola kora hobe
            user_account = loan.account  # loan. account ar account ta ana hoice Transaction model theke 
            
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect()
            
            else:
                messages.error(self.request, f'Loan amount is gretherthen availavle blance')
                return redirect()
            
class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account, transaction_type = LOAN)
        print(queryset)
        return queryset
    
    
    