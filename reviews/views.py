from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from products.models import Product

from .forms import ReviewForm
from .models import Review


@role_required(User.Role.USER)
def review_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=Product.Status.ACTIVE)
    existing = Review.objects.filter(user=request.user, product=product).first()
    if existing:
        return redirect('reviews:update', pk=existing.pk)
    form = ReviewForm(request.POST or None, initial={'rating': 5})
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        messages.success(request, 'Review submitted.')
        return redirect('products:detail', pk=product.pk)
    return render(request, 'reviews/review_form.html', {'form': form, 'product': product})


@role_required(User.Role.USER)
def review_update(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Review updated.')
        return redirect('products:detail', pk=review.product_id)
    return render(request, 'reviews/review_form.html', {'form': form, 'product': review.product, 'review': review})


@role_required(User.Role.USER)
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    product_id = review.product_id
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
        return redirect('products:detail', pk=product_id)
    return render(request, 'reviews/review_delete.html', {'review': review})
