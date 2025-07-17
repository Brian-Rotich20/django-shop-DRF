import json
import stripe 
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem, Category, CustomerAddress, Order, OrderItem, PaymentRequest, Product, Review, Wishlist
from .serializers import CartItemSerializer, CartSerializer, CategoryDetailSerializer, CategoryListSerializer, CustomerAddressSerializer, OrderSerializer, ProductListSerializer, ProductDetailSerializer, ProductSerializer, ReviewSerializer, SimpleCartSerializer, UserLoginSerializer, UserRegistrationSerializer, UserSerializer, WishlistSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
import base64
import requests
from datetime import datetime
from django.utils import timezone


key = settings.MPESA_CONSUMER_KEY
secret = settings.MPESA_CONSUMER_SECRET
# etc.


from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.WEBHOOK_SECRET


User = get_user_model()

@api_view(['GET'])
def product_list(request):
    products = Product.objects.filter(featured=True)
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    serializer = ProductDetailSerializer(product)
    return Response(serializer.data)


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


@api_view(["POST"])
def add_to_cart(request):
    cart_code = request.data.get("cart_code")
    product_id = request.data.get("product_id")

    cart, created = Cart.objects.get_or_create(cart_code=cart_code)
    product = Product.objects.get(id=product_id)

    cartitem, created = CartItem.objects.get_or_create(product=product, cart=cart)
    cartitem.quantity = 1 
    cartitem.save() 

    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['PUT'])
def update_cartitem_quantity(request):
    cartitem_id = request.data.get("item_id")
    quantity = request.data.get("quantity")

    quantity = int(quantity)

    cartitem = CartItem.objects.get(id=cartitem_id)
    cartitem.quantity = quantity 
    cartitem.save()

    serializer = CartItemSerializer(cartitem)
    return Response({"data": serializer.data, "message": "Cartitem updated successfully!"})


@api_view(["POST"])
def add_review(request):
    product_id = request.data.get("product_id")
    email = request.data.get("email")
    rating = request.data.get("rating")
    review_text = request.data.get("review")

    if not all([product_id, email, rating, review_text]):
        return Response({"error": "Missing required fields."}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)

    if Review.objects.filter(product=product, user=user).exists():
        return Response({"error": "You already submitted a review."}, status=400)

    Review.objects.create(
        product=product,
        user=user,
        rating=rating,
        review=review_text
    )

    return Response({"success": "Review added."}, status=201)

@api_view(['PUT'])
def update_review(request, pk):
    review = Review.objects.get(id=pk) 
    rating = request.data.get("rating")
    review_text = request.data.get("review")

    review.rating = rating 
    review.review = review_text
    review.save()

    serializer = ReviewSerializer(review)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_review(request, pk):
    review = Review.objects.get(id=pk) 
    review.delete()

    return Response("Review deleted successfully!", status=204)

@api_view(['DELETE'])
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

    wishlist = Wishlist.objects.filter(user=user, product=product)
    if wishlist:
        wishlist.delete()
        return Response("Wishlist deleted successfully!", status=204)

    new_wishlist = Wishlist.objects.create(user=user, product=product)
    serializer = WishlistSerializer(new_wishlist)
    return Response(serializer.data)

@api_view(['GET'])
def product_search(request):
    query = request.query_params.get("query") 
    if not query:
        return Response("No query provided", status=400)
    
    products = Product.objects.filter(Q(name__icontains=query) | 
                                      Q(description__icontains=query) |
                                       Q(category__name__icontains=query) )
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)
    






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
            metadata = {"cart_code": cart_code}
        )
        return Response({'data': checkout_session})
    except Exception as e:
        return Response({'error': str(e)}, status=400)




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




# Newly Added


@api_view(["POST"])
def create_user(request):
    username = request.data.get("username")
    email = request.data.get("email")
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    profile_picture_url = request.data.get("profile_picture_url")

    new_user = User.objects.create(username=username, email=email,
                                       first_name=first_name, last_name=last_name, profile_picture_url=profile_picture_url)
    serializer = UserSerializer(new_user)
    return Response(serializer.data)


@api_view(["GET"])
def existing_user(request, email):
    try:
        User.objects.get(email=email)
        return Response({"exists": True}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_orders(request):
    try:
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        orders = Order.objects.filter(customer_email__iexact=email)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("Error in get_orders:", error_trace)
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
def add_address(request):
    email = request.data.get("email")
    street = request.data.get("street")
    city = request.data.get("city")
    state = request.data.get("state")
    phone = request.data.get("phone")

    if not email:
        return Response({"error": "Email is required"}, status=400)
    
    customer = User.objects.get(email=email)

    address, created = CustomerAddress.objects.get_or_create(
        customer=customer)
    address.email = email 
    address.street = street 
    address.city = city 
    address.state = state
    address.phone = phone 
    address.save()

    serializer = CustomerAddressSerializer(address)
    return Response(serializer.data)


@api_view(["GET"])
def get_address(request):
    email = request.query_params.get("email") 
    address = CustomerAddress.objects.filter(customer__email=email)
    if address.exists():
        address = address.last()
        serializer = CustomerAddressSerializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"error": "Address not found"}, status=200)


@api_view(["GET"])
def my_wishlists(request):
    email = request.query_params.get("email")
    wishlists = Wishlist.objects.filter(user__email=email)
    serializer = WishlistSerializer(wishlists, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def product_in_wishlist(request):
    email = request.query_params.get("email")
    product_id = request.query_params.get("product_id")

    if Wishlist.objects.filter(product__id=product_id, user__email=email).exists():
        return Response({"product_in_wishlist": True})
    return Response({"product_in_wishlist": False})



@api_view(['GET'])
def get_cart(request, cart_code):
    cart = Cart.objects.filter(cart_code=cart_code).first()
    
    if cart:
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)




@api_view(['GET'])
def get_cart_stat(request):
    cart_code = request.query_params.get("cart_code")
    cart = Cart.objects.filter(cart_code=cart_code).first()

    if cart:
        serializer = SimpleCartSerializer(cart)
        return Response(serializer.data)
    return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def product_in_cart(request):
    cart_code = request.query_params.get("cart_code")
    product_id = request.query_params.get("product_id")
    
    cart = Cart.objects.filter(cart_code=cart_code).first()
    product = Product.objects.get(id=product_id)
    
    product_exists_in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

    return Response({'product_in_cart': product_exists_in_cart})


# Added product details page
@api_view(['GET'])
def product_detail_by_id(request, id):
    product = get_object_or_404(Product, id=id)
    serializer = ProductSerializer(product)
    return Response(serializer.data)

# Added user authentication views

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user with email or phone number
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response({
            'message': 'User registered successfully',
            'user': user_serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user with email/phone and password
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response({
            'message': 'Login successful',
            'user': user_serializer.data,
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_user(request):
    """
    Logout user by deleting their token
    """
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except:
        return Response({
            'message': 'Logout failed'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_user_profile(request):
    """
    Get current user's profile
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# Mpesa integration
def generate_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    auth = (consumer_key, consumer_secret)

    res = requests.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        auth=auth
    )

    try:
        return res.json()["access_token"]
    except Exception as e:
        print(" Failed to get access token")
        print("Status:", res.status_code)
        print("Response:", res.text)
        raise e
    
def get_lipa_na_mpesa_password():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    encoded = base64.b64encode(data_to_encode.encode())
    return encoded.decode('utf-8'), timestamp


@api_view(['POST'])
def lipa_na_mpesa(request):  
    phone = request.data.get("phone")
    cart_code = request.data.get("cart_code")
    email = request.data.get("email")

    if not phone or not cart_code or not email:
        return Response({"error": "Phone, email and cart_code are required"}, status=400)

    try:
        cart = Cart.objects.get(cart_code=cart_code)
    except Cart.DoesNotExist:
        return Response({"error": "Invalid cart code"}, status=404)

    PaymentRequest.objects.update_or_create(
        cart_code=cart_code,
        defaults={"email": email}
    )

    USD_TO_KES = 140
    amount_usd = sum(item.product.price * item.quantity for item in cart.cartitems.all())
    amount_kes = int(amount_usd * USD_TO_KES)

    try:
        access_token = generate_mpesa_access_token()
        password, timestamp = get_lipa_na_mpesa_password()
    except Exception as e:
        print("Failed generating M-Pesa credentials:", str(e))
        return Response({"error": "M-Pesa credentials error", "details": str(e)}, status=500)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount_kes,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": cart_code,
        "TransactionDesc": "Payment for cart",
    }

    print("📤 Sending STK Push Payload:", json.dumps(payload, indent=2))

    res = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload
    )

    print("Safaricom response:")
    print("Status Code:", res.status_code)
    print("Response:", res.text)

    try:
        return Response(res.json(), status=res.status_code)
    except Exception as e:
        print("Error decoding Safaricom response:", e)
        return Response({
            "error": "Failed to decode Safaricom response",
            "details": res.text
        }, status=500)
@csrf_exempt
@api_view(["POST"])
def mpesa_callback(request):
    data = request.data
    print("M-Pesa Callback Data:", data)

    try:
        result_code = data["Body"]["stkCallback"]["ResultCode"]
        metadata = data["Body"]["stkCallback"].get("CallbackMetadata", {})
        cart_code = data["Body"]["stkCallback"]["AccountReference"]

        if result_code == 0:
            cart = Cart.objects.get(cart_code=cart_code)
            payment_request = PaymentRequest.objects.get(cart_code=cart_code)
            email = payment_request.email

            # ✅ Create the order
            order = Order.objects.create(
                amount=sum(item.product.price * item.quantity for item in cart.cartitems.all()),
                currency="KES",
                customer_email=email,
                status="Paid"
            )

            for item in cart.cartitems.all():
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)

            # ✅ Update payment status instead of deleting
            payment_request.status = "Paid"
            payment_request.save()

            cart.delete()

        else:
            PaymentRequest.objects.filter(cart_code=cart_code).update(status="Declined")

    except Exception as e:
        print("Error processing callback:", e)

    return Response({"message": "Callback received"}, status=200)

#Added payment status view
@api_view(["GET"])
def payment_status(request):
    cart_code = request.GET.get("cart_code")
    try:
        pr = PaymentRequest.objects.get(cart_code=cart_code)
        return Response({"status": pr.status})
    except PaymentRequest.DoesNotExist:
        return Response({"status": "NotFound"}, status=404)
    

#Added get_reviews view
@api_view(['GET'])
def get_reviews(request, product_id):
    try:
        # product = Product.objects.get(id=product_id)
        reviews = Review.objects.filter(product_id=product_id)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)