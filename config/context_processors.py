def nav_counts(request):
    """Cart item count and unread notification count for the navbar badges."""
    cart_count = 0
    unread_count = 0
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        cart_count = sum(
            user.cart_items.values_list('quantity', flat=True)
        ) if hasattr(user, 'cart_items') else 0
        unread_count = user.notifications.filter(is_read=False).count() if hasattr(user, 'notifications') else 0
    return {
        'nav_cart_count': cart_count,
        'nav_unread_count': unread_count,
    }


def modal_flag(request):
    """True when the page is being fetched by the AJAX view/edit modal (static/js/modal.js)
    rather than loaded as a normal page — lets templates skip their own redundant heading
    since the modal already shows a title bar."""
    return {'is_modal': request.headers.get('X-Requested-With') == 'XMLHttpRequest'}
