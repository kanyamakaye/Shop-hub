from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from categories.models import Category
from config.csv_utils import csv_response
from config.query_utils import is_decimal_string
from tenants.models import Tenant

from .forms import ProductForm
from .models import Product

SORT_OPTIONS = {
    'newest': '-created_at',
    'price_asc': 'price',
    'price_desc': '-price',
    'name_asc': 'product_name',
    'rating': '-avg_rating',
}


def product_list(request):
    """Public storefront listing across all tenants.

    Categories are tenant-owned (each store has its own "T-shirts" row, etc.),
    so filtering/listing is done by category *name* rather than a single
    category's primary key — otherwise picking "T-shirts" would only match
    one tenant's copy and hide every other store's matching products.
    """
    products = Product.objects.filter(status=Product.Status.ACTIVE).select_related('tenant', 'category')

    query = request.GET.get('q', '').strip()
    category_name = request.GET.get('category', '').strip()
    tenant_id = request.GET.get('store', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    discount_only = request.GET.get('discount', '').strip()
    min_rating = request.GET.get('min_rating', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    if query:
        products = products.filter(Q(product_name__icontains=query) | Q(description__icontains=query) | Q(sku__icontains=query))
    if category_name:
        products = products.filter(category__category_name=category_name)
    if tenant_id.isdigit():
        products = products.filter(tenant_id=tenant_id)
    if is_decimal_string(min_price):
        products = products.filter(price__gte=min_price)
    if is_decimal_string(max_price):
        products = products.filter(price__lte=max_price)
    if discount_only:
        products = products.filter(discount_price__isnull=False)
    if min_rating.isdigit() or sort == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating'))
    if min_rating.isdigit():
        products = products.filter(avg_rating__gte=int(min_rating))

    products = products.order_by(SORT_OPTIONS.get(sort, SORT_OPTIONS['newest']))

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = (
        Category.objects.filter(parent__isnull=False, products__status=Product.Status.ACTIVE)
        .values_list('category_name', flat=True).distinct().order_by('category_name')
    )
    stores = (
        Tenant.objects.filter(status=Tenant.Status.ACTIVE, products__status=Product.Status.ACTIVE)
        .distinct().order_by('business_name')
    )

    # Preserve every active filter except `page` when paginating/sorting links.
    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    return render(request, 'products/product_list.html', {
        'page_obj': page_obj, 'query': query, 'categories': categories, 'category_name': category_name,
        'stores': stores, 'tenant_id': tenant_id, 'min_price': min_price, 'max_price': max_price,
        'discount_only': discount_only, 'min_rating': min_rating, 'sort': sort, 'base_query': base_query,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('tenant', 'category').prefetch_related('reviews__user'),
        pk=pk, status=Product.Status.ACTIVE,
    )
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = product.wishlisted_by.filter(user=request.user).exists()
    return render(request, 'products/product_detail.html', {'product': product, 'in_wishlist': in_wishlist})


@role_required(User.Role.SYSTEM_ADMIN)
def product_manage_list(request):
    tenant_products = Product.objects.filter(tenant_id=request.user.tenant_id)
    stats = tenant_products.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status=Product.Status.ACTIVE)),
        needs_restock=Count('id', filter=Q(stock_quantity__lte=F('low_stock_threshold'))),
    )
    products = tenant_products.select_related('category')
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    status = request.GET.get('status', '').strip()
    stock_level = request.GET.get('stock_level', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()

    if query:
        products = products.filter(Q(product_name__icontains=query) | Q(sku__icontains=query))
    if category_id.isdigit():
        products = products.filter(category_id=category_id)
    if status:
        products = products.filter(status=status)
    if stock_level == 'out':
        products = products.filter(stock_quantity=0)
    elif stock_level == 'low':
        products = products.filter(stock_quantity__gt=0, stock_quantity__lte=F('low_stock_threshold'))
    elif stock_level == 'in':
        products = products.filter(stock_quantity__gt=F('low_stock_threshold'))
    if is_decimal_string(min_price):
        products = products.filter(price__gte=min_price)
    if is_decimal_string(max_price):
        products = products.filter(price__lte=max_price)

    if request.GET.get('export') == 'csv':
        rows = (
            [p.sku, p.product_name, p.category.category_name if p.category else '', p.price,
             p.discount_price or '', p.stock_quantity, p.low_stock_threshold, p.status]
            for p in products
        )
        return csv_response('products.csv', [
            'SKU', 'Name', 'Category', 'Price (RWF)', 'Discount Price (RWF)', 'Stock', 'Low Stock Threshold', 'Status',
        ], rows)

    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'products/product_manage_list.html', {
        'page_obj': page_obj, 'query': query, 'show_sidebar': True, 'base_query': base_query,
        'categories': Category.objects.filter(tenant_id=request.user.tenant_id),
        'category_id': category_id, 'status': status, 'stock_level': stock_level,
        'min_price': min_price, 'max_price': max_price,
        'status_choices': Product.Status.choices, 'stats': stats,
    })


@role_required(User.Role.SYSTEM_ADMIN)
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None, tenant=request.user.tenant)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.tenant_id = request.user.tenant_id
        product.save()
        messages.success(request, 'Product created.')
        return redirect('products:manage_list')
    return render(request, 'products/product_form.html', {'form': form, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_ADMIN)
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, tenant_id=request.user.tenant_id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product, tenant=request.user.tenant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated.')
        return redirect('products:manage_list')
    return render(request, 'products/product_form.html', {'form': form, 'product': product, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_ADMIN)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, tenant_id=request.user.tenant_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('products:manage_list')
    return render(request, 'products/product_delete.html', {'product': product, 'show_sidebar': True})
