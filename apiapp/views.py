import stripe 
from django.conf import settings
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView # Retrieve single products
from rest_framework import status
from .models import Cart, CartItem, Category, Product, Review, Wishlist, Order, OrderItem, ProductRating
from .serializers import CartItemSerializer, CartSerializer, CategoryDetailSerializer, CategoryListSerializer, ProductListSerializer, ProductDetailSerializer, ProductSerializer, ReviewSerializer, WishlistSerializer
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your views here.

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

endpoint_secret = settings.WEBHOOK_SECRET
stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['GET'])
def product_list(request):
    products = Product.objects.filter(featured=True)
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    serializer = ProductDetailSerializer(product)
    return Response(serializer.data)

class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
User = get_user_model()

@api_view(["GET"])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategoryListSerializer(categories, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def category_detail(request, slug): 
    category = Category.objects.get(slug=slug)
    serializer = CategoryDetailSerializer(category)
    return Response(serializer.data)


# Modified add-to-cart all functionalite
@api_view(["POST"])
def add_to_cart(request):
    """Add a product to the cart"""
    cart_code = request.data.get("cart_code")
    product_id = request.data.get("product_id")
    quantity = request.data.get("quantity", 1)  # Default to 1 if not provided
    
    if not cart_code or not product_id:
        return Response(
            {"error": "cart_code and product_id are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get or create cart
        cart, created = Cart.objects.get_or_create(cart_code=cart_code)
        
        # Get product
        product = Product.objects.get(id=product_id)
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product,
            defaults={'quantity': quantity}
        )
        
        # If item already exists, increase quantity
        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response({
            "message": "Item added to cart successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_cart_items(request):
    """Get cart items by cart_code"""
    cart_code = request.query_params.get('cart_code')
    
    if not cart_code:
        return Response(
            {'error': 'cart_code parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        cart = Cart.objects.get(cart_code=cart_code)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response(
            {'error': 'Cart not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(["PUT"])
def update_cartitem_quantity(request):
    """Update cart item quantity"""
    cartitem_id = request.data.get("item_id")
    quantity = request.data.get("quantity")
    
    if not cartitem_id or not quantity:
        return Response(
            {"error": "item_id and quantity are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return Response(
                {"error": "Quantity must be greater than 0"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cartitem = CartItem.objects.get(id=cartitem_id)
        cartitem.quantity = quantity
        cartitem.save()
        
        serializer = CartItemSerializer(cartitem)
        return Response({
            "data": serializer.data, 
            "message": "Cart item quantity updated successfully"
        })
        
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError:
        return Response(
            {"error": "Invalid quantity value"}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["DELETE"])
def delete_cartitem(request, pk):
    """Delete a cart item"""
    try:
        cartitem = CartItem.objects.get(id=pk)
        cartitem.delete()
        return Response({
            "message": "Cart item deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
def add_review(request):

    product_id = request.data.get("product_id")
    email = request.data.get("email")
    rating = request.data.get("rating")
    review_text = request.data.get("review_text")

    product = Product.objects.get(id=product_id)
    user = User.objects.get(email=email)

    if Review.objects.filter(product=product, user=user).exists():
        return Response({"error": "You have already dropped a review for this product"}, status=400)
    
    review = Review.objects.create(product=product, user=user, rating=rating, review=review_text)
    serializer = ReviewSerializer(review)
    return Response(serializer.data)


@api_view(["PUT"])
def update_review(request, pk):
    review  = Review.objects.get(id=pk)
    rating = request.data.get("rating")
    review_text = request.data.get("review_text")

    review.rating = rating
    review.review = review_text
    review.save()

    serializer = ReviewSerializer(review)
    return Response(serializer.data)



@api_view(["DELETE"])
def delete_review(request, pk):
    review = Review.objects.get(id=pk)
    review.delete()

    return Response("Review deleted successfully!",status=204)




@api_view(['DELETE']) # View to delete a cart item.
def delete_cartitem(request, pk):
    cartitem = CartItem.objects.get(id=pk) 
    cartitem.delete()

    return Response("Cartitem deleted successfully!", status=204)

@api_view(['POST'])
def add_to_wishlist(request):
    email = request.data.get("email")
    product_id = request.data.get("product_id")

    user = User.objects.get(email=email)
    product = Product.objects.get(id=product_id)

    wishlist = Wishlist.objects.filter(user=user,product=product)
    if wishlist:
        wishlist.delete()
        return Response("Wishlist deleted successfully!", status=204)
    
    new_wishlist = Wishlist.objects.create(user=user, product=product)
    serializer = WishlistSerializer(new_wishlist)

    return Response(serializer.data)


@api_view(["GET"])
def product_search(request):
    query = request.query_params.get("query")
    if not query:
        return Response("No query provided", status=400)
    
    products = Product.objects.filter(Q(name__icontains=query) |
                                      Q(description__icontains=query) |
                                      Q(category__name__icontains=query))
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


# Stripe payment view

@api_view(['POST'])
def create_checkout_session(request):
    cart_code = request.data.get("cart_code")
    email = request.data.get("email")
    cart = Cart.objects.get(cart_code=cart_code)
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email= email,
            payment_method_types=['card'],


            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item.product.name},
                        'unit_amount': int(item.product.price * 100),  # Amount in cents
                    },
                    'quantity': item.quantity,
                }
                for item in cart.cartitems.all()
            ] + [
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'VAT Fee'},
                        'unit_amount': 500,  # $5 in cents
                    },
                    'quantity': 1,
                }
            ],


           
            mode='payment',
            # success_url="http://localhost:3000/success",
            # cancel_url="http://localhost:3000/cancel",

            success_url="https://next-shop-self.vercel.app/success",
            cancel_url="https://next-shop-self.vercel.app/failed",
            metadata={
                "cart_code": cart_code,
            }

        )
        return Response({'data': checkout_session})
    except Exception as e:
        return Response({'error': str(e)}, status=400)




# Webhook to handle Stripe events


@csrf_exempt
def my_webhook_view(request):
  payload = request.body
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

  if (
    event['type'] == 'checkout.session.completed'
    or event['type'] == 'checkout.session.async_payment_succeeded'
  ):
    session = event['data']['object']
    cart_code = session.get("metadata", {}).get("cart_code")

    fulfill_checkout(session, cart_code)


  return HttpResponse(status=200)



def fulfill_checkout(session, cart_code):
    
    order = Order.objects.create(stripe_checkout_id=session["id"],
        amount=session["amount_total"],
        currency=session["currency"],
        customer_email=session["customer_email"],
        status="Paid")
    

    print(session)


    cart = Cart.objects.get(cart_code=cart_code)
    cartitems = cart.cartitems.all()

    for item in cartitems:
        orderitem = OrderItem.objects.create(order=order, product=item.product, 
                                             quantity=item.quantity)
    
    cart.delete()

