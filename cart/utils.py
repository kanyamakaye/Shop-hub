import itertools


def group_items_by_store(items):
    """Group cart items by their product's tenant, computing each store's
    subtotal/tax/shipping/estimated_total the same way checkout does — so the
    cart page can preview exactly what checkout will charge per store."""
    store_groups = []
    for tenant_id, group in itertools.groupby(
        sorted(items, key=lambda i: i.product.tenant_id),
        key=lambda i: i.product.tenant_id,
    ):
        group_items = list(group)
        tenant = group_items[0].product.tenant
        subtotal = sum((i.subtotal for i in group_items), 0)
        tax = round(subtotal * tenant.tax_rate / 100, 2)
        shipping = tenant.shipping_fee
        store_groups.append({
            'tenant': tenant, 'items': group_items, 'subtotal': subtotal,
            'tax': tax, 'shipping': shipping, 'estimated_total': subtotal + tax + shipping,
        })
    return store_groups
