from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from products.models import Product

from .forms import CategoryForm
from .models import Category


@role_required(User.Role.SYSTEM_ADMIN)
def category_list(request):
    tenant_categories = Category.objects.filter(tenant_id=request.user.tenant_id)
    stats = tenant_categories.aggregate(
        total=Count('id'),
        top_level=Count('id', filter=Q(parent__isnull=True)),
        with_products=Count('id', filter=Q(products__status=Product.Status.ACTIVE), distinct=True),
    )
    categories = tenant_categories
    query = request.GET.get('q', '').strip()
    if query:
        categories = categories.filter(Q(category_name__icontains=query))
    paginator = Paginator(categories, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'categories/category_list.html', {
        'page_obj': page_obj, 'query': query, 'show_sidebar': True, 'stats': stats,
    })


@role_required(User.Role.SYSTEM_ADMIN)
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.tenant_id = request.user.tenant_id
        category.save()
        messages.success(request, 'Category created.')
        return redirect('categories:list')
    return render(request, 'categories/category_form.html', {'form': form, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_ADMIN)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, tenant_id=request.user.tenant_id)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('categories:list')
    return render(request, 'categories/category_form.html', {'form': form, 'category': category, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_ADMIN)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, tenant_id=request.user.tenant_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('categories:list')
    return render(request, 'categories/category_delete.html', {'category': category, 'show_sidebar': True})
