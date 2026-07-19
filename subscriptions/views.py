from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import SubscriptionPlanForm
from .models import SubscriptionPlan


def plan_list(request):
    """Public pricing page — anyone can browse plans; only the Owner manages them."""
    plans = SubscriptionPlan.objects.filter(status=SubscriptionPlan.Status.ACTIVE)
    query = request.GET.get('q', '').strip()
    if query:
        plans = plans.filter(Q(plan_name__icontains=query))
    is_owner = request.user.is_authenticated and request.user.role == User.Role.SYSTEM_OWNER
    if is_owner:
        plans = SubscriptionPlan.objects.all()
        if query:
            plans = plans.filter(Q(plan_name__icontains=query))
    paginator = Paginator(plans, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'subscriptions/plan_list.html', {
        'page_obj': page_obj, 'query': query, 'is_owner': is_owner,
        'show_sidebar': is_owner,
    })


@role_required(User.Role.SYSTEM_OWNER)
def plan_create(request):
    form = SubscriptionPlanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subscription plan created.')
        return redirect('subscriptions:list')
    return render(request, 'subscriptions/plan_form.html', {'form': form, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER)
def plan_update(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    form = SubscriptionPlanForm(request.POST or None, instance=plan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subscription plan updated.')
        return redirect('subscriptions:list')
    return render(request, 'subscriptions/plan_form.html', {'form': form, 'plan': plan, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER)
def plan_delete(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Subscription plan deleted.')
        return redirect('subscriptions:list')
    return render(request, 'subscriptions/plan_delete.html', {'plan': plan, 'show_sidebar': True})
