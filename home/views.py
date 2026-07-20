from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe

from categories.models import Category
from orders.models import Order
from products.models import Product
from subscriptions.models import SubscriptionPlan
from tenants.models import Tenant

from .forms import ContactForm, NewsletterForm

TESTIMONIALS = [
    {
        'name': 'Jean Niyonsenga', 'role': 'Owner, Kigali Electronics Ltd',
        'quote': 'ShopHub let us launch our electronics store in a single afternoon. Order management alone saved us hours every week.',
        'rating': 5,
    },
    {
        'name': 'Eric Habimana', 'role': 'Owner, Rwanda Fashion Store',
        'quote': 'The dashboard gives me a clear view of sales and stock without needing a developer on staff.',
        'rating': 5,
    },
    {
        'name': 'Alice Mukamana', 'role': 'Customer',
        'quote': 'Shopping across different stores on one platform with one account is genuinely convenient.',
        'rating': 4,
    },
]


def _bullets(intro, items):
    lis = ''.join(f'<li>{item}</li>' for item in items)
    intro_html = f'<p>{intro}</p>' if intro else ''
    return mark_safe(f'{intro_html}<ul class="mt-1 list-disc space-y-0.5 pl-5">{lis}</ul>')


def _note(text):
    return mark_safe(f'<p class="mt-1 text-xs text-slate-500 dark:text-slate-500">{text}</p>')


# Grouped like a standard SaaS help-center FAQ (General, Plans & Billing,
# Payments, Security, Features, Integrations, Support, Getting Started)
# instead of one long flat list — much easier to scan at 25 questions.
FAQ_CATEGORIES = [
    ('General', [
        ('What is the Multi-Tenant SaaS E-Commerce Platform?',
         'ShopHub (Multi-Tenant SaaS E-Commerce Platform) is a cloud-based solution that enables multiple businesses to create and manage their own online stores using a single shared application. Each business (tenant) has its own secure, isolated environment for managing products, customers, orders, and sales.'),
        ('Who can use this platform?',
         _bullets('', [
             'Retail businesses', 'Fashion stores', 'Electronics shops', 'Supermarkets', 'Pharmacies',
             'Furniture stores', 'Cosmetic stores', 'Wholesale businesses', 'Multi-branch businesses',
             'Entrepreneurs launching online stores',
         ])),
    ]),
    ('Plans & Billing', [
        ('What subscription plans are available?',
         _bullets('The platform offers three subscription plans, each designed for a different business stage:', ['Basic', 'Professional', 'Enterprise'])),
        ('Can I upgrade my subscription plan?',
         'Yes. You can upgrade your subscription at any time. Your new features become available immediately after successful payment.'),
        ('Can I downgrade my subscription?',
         'Yes. Downgrades are supported and typically take effect at the beginning of your next billing cycle.'),
        ('Is there a free trial?',
         'A free trial may be offered during promotional periods. Contact our sales team for current offers and eligibility.'),
        ('What happens if my subscription expires?',
         _bullets('If your subscription expires:', [
             'Your online store may become temporarily inaccessible.',
             'Administrative access may be restricted.',
             'Your data remains securely stored for a defined retention period.',
             'Service is restored once the subscription is renewed.',
         ])),
    ]),
    ('Payments', [
        ('What payment methods are supported?',
         _bullets('The platform supports multiple payment methods, including:', [
             'Mobile Money', 'Bank Transfer', 'Credit/Debit Cards',
             'Online Payment Gateways', 'Other locally supported payment providers',
         ])),
    ]),
    ('Security & Data', [
        ('Is my business data secure?',
         _bullets('Yes. The platform uses enterprise-grade security measures including:', [
             'SSL encryption', 'Secure cloud hosting', 'Automated backups', 'Data isolation between tenants',
             'Role-based access control', 'Multi-Factor Authentication (Enterprise)', 'Audit logs',
         ])),
        ('Are backups included?',
         'Yes. All plans include automatic cloud backups. Enterprise customers also benefit from advanced disaster recovery services.'),
    ]),
    ('Store Features', [
        ('Can I have multiple branches?',
         _bullets('Yes.', ['Professional Plan supports multi-branch management.', 'Enterprise Plan supports unlimited branches.'])),
        ('Can I manage multiple stores or companies?',
         'Yes. Multi-store and multi-company management are available under the Enterprise Plan.'),
        ('Does the platform support mobile devices?',
         'Yes. The platform is fully responsive and works on desktops, tablets, and smartphones. A dedicated mobile application is also available as an optional add-on.'),
        ('Can I customize my online store?',
         _bullets('Yes. You can customize:', [
             'Store logo', 'Brand colors', 'Store information', 'Homepage banners', 'Product categories', 'Product images',
         ]) + _note('Enterprise customers can also request advanced branding and custom development.')),
        ('Does the platform support inventory management?',
         'Yes. The platform includes inventory management with stock tracking, inventory updates, low-stock alerts, and product availability monitoring.'),
        ('Can customers leave reviews?',
         'Yes. Customers can rate products, write reviews, and manage wishlists after purchasing products.'),
        ('Does the platform provide reports?',
         _bullets('Yes. The platform provides:', [
             'Sales Reports', 'Revenue Reports', 'Order Reports', 'Customer Reports', 'Product Reports', 'Inventory Reports',
         ]) + _note('Professional and Enterprise plans include advanced analytics and dashboards.')),
        ('Does the platform support multiple languages and currencies?',
         'Yes. The platform can be configured to support multiple languages and currencies depending on your business requirements.'),
        ('Can I sell both physical and digital products?',
         _bullets('Yes. The platform supports:', ['Physical products', 'Digital products', 'Downloadable products', 'Service-based offerings'])),
    ]),
    ('Integrations & Migration', [
        ('Can I integrate with other systems?',
         _bullets('Yes. The platform supports integration with:', [
             'Payment gateways', 'Accounting systems', 'ERP systems', 'SMS gateways',
             'WhatsApp', 'REST APIs', 'Third-party applications',
         ]) + _note('Some integrations are available as premium features.')),
        ('Can I migrate data from my existing system?',
         _bullets('Yes. We provide data migration services for:', ['Products', 'Customers', 'Orders', 'Categories', 'Inventory'])
         + _note('Migration may be included or provided as an optional service depending on project scope.')),
        ('Can I use my own domain name?',
         'Yes. You can connect your own custom domain to your online store. Advanced branding and domain configuration are available for Enterprise customers.'),
    ]),
    ('Support & Updates', [
        ('Is technical support included?',
         _bullets('Yes. All plans include:', ['Email support', 'Phone support', 'Remote assistance', 'Knowledge base access'])
         + _note('Professional plans receive priority support; Enterprise customers receive dedicated support and an assigned account manager.')),
        ('Are software updates included?',
         _bullets('Yes. All active subscriptions include:', ['Software updates', 'Security patches', 'Performance improvements', 'New feature releases'])),
    ]),
    ('Getting Started', [
        ('How do I get started?',
         _bullets('Getting started is simple:', [
             'Choose a subscription plan.', 'Register your business.', 'Configure your online store.',
             'Add products and categories.', 'Set up payment methods.', 'Launch your store and begin selling online.',
         ])),
    ]),
]

HOW_IT_WORKS = [
    ('1', 'Choose a subscription plan', 'Pick the plan that matches how many products and staff your store needs.'),
    ('2', 'Register your business', 'Create your store profile with your business details and logo.'),
    ('3', 'Add your products', 'Organize your catalog into categories and list your products.'),
    ('4', 'Start selling', 'Customers discover your store, add to cart, and check out securely.'),
]


def index(request):
    featured_products = Product.objects.filter(status=Product.Status.ACTIVE).select_related('tenant', 'category').order_by('-created_at')[:8]
    # Categories are tenant-owned (each store has its own copy of a name like
    # "T-shirts"), so this shows distinct category *names* that have active
    # products under any tenant, rather than raw Category rows.
    categories = (
        Category.objects.filter(parent__isnull=False, products__status=Product.Status.ACTIVE)
        .values_list('category_name', flat=True).distinct().order_by('category_name')[:6]
    )
    plans = SubscriptionPlan.objects.filter(status=SubscriptionPlan.Status.ACTIVE)[:3]
    stats = {
        'tenant_count': Tenant.objects.filter(status=Tenant.Status.ACTIVE).count(),
        'product_count': Product.objects.filter(status=Product.Status.ACTIVE).count(),
        'order_count': Order.objects.count(),
        'country_count': Tenant.objects.values('country').distinct().count(),
    }
    # Illustrative figures for the hero's dashboard *mockup* only — a stylized
    # preview graphic (matching the brief's "1M+ Orders" style marketing
    # numbers), not a claim about this specific install's live data. The
    # real, honest counts are what the stat tiles below the hero show.
    mockup_stats = {'revenue': 128_500_000, 'orders': 450_000, 'customers': 700_000}
    return render(request, 'home/index.html', {
        'featured_products': featured_products,
        'categories': categories,
        'plans': plans,
        'stats': stats,
        'mockup_stats': mockup_stats,
        'testimonials': TESTIMONIALS,
        'faq_categories': FAQ_CATEGORIES,
        'how_it_works': HOW_IT_WORKS,
        'newsletter_form': NewsletterForm(),
        'contact_form': ContactForm(),
    })


def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks for subscribing to our newsletter!')
        else:
            messages.error(request, 'Please enter a valid, unused email address.')
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(f'{referer.split("#")[0]}#newsletter')
    return redirect('/#newsletter')


def contact_submit(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks for reaching out! We will get back to you soon.')
        else:
            messages.error(request, 'Please check the contact form and try again.')
    return redirect('/#contact')


def privacy_policy(request):
    return render(request, 'home/privacy.html')


def terms_conditions(request):
    return render(request, 'home/terms.html')
