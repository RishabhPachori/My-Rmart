from django.shortcuts import render
from django.http import HttpResponse
from .models import Product, Contact, Order, OrderUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from .paytm import checksum
# Create your views here.
MERCHANT_KEY = 'qusdT%qBbLnDEvjZ'

def index(request):

   # products=Product.objects.all()
    #print(products)
    #n=len(products)
    #nslides=n//4+ceil((n/4)-(n//4))
    
    #params={'no_of_slides':nslides,'range':range(1,nslides),'product':products}
    #allProducts=[
     #   [products,range(1,nslides),nslides],
     #   [products,range(1,nslides),nslides]
      #  ]
    allProducts=[]
    category_prod=Product.objects.values('category','id')
    category_item={item['category'] for item in category_prod}
    for i in category_item:
        prod=Product.objects.filter(category=i)
        n=len(prod)
        nslides=n // 4 + ceil((n / 4) - (n // 4))
        allProducts.append([prod,range(1,nslides),nslides])

    params={'allProducts':allProducts}
    return render(request,'shop/index.html',params)

def about(request):
    return render(request,'shop/about.html')

def contact(request):
    thank=False
    if request.method=="POST":
        name=request.POST.get('name','')
        email=request.POST.get('email','')
        phone=request.POST.get('phone','')
        desc=request.POST.get('desc','')
        contact=Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
        thank=True
    return render(request,'shop/contact.html',{'thank':thank})

def tracker(request):
    if request.method=="POST":
        orderId=request.POST.get('orderId','')
        email=request.POST.get('email','')
        try:
            order=Order.objects.filter(order_id=orderId,email=email)
            if len(order)>0:
                update=OrderUpdate.objects.filter(order_id=orderId)
                updates=[]
                for item in update:
                    updates.append({'text':item.update_desc,'time':item.timestamp})
                    response = json.dumps({"status":"success", "updates": updates, "itemsJson": order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')
    
def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False


def search(request):
    query=request.GET.get('search')
    allProducts=[]
    category_prod=Product.objects.values('category','id')
    category_item={item['category'] for item in category_prod}
    for i in category_item:
        prodtemp=Product.objects.filter(category=i)
        prod=[item for item in prodtemp if searchMatch(query,item)]

        n=len(prod)
        nslides=n // 4 + ceil((n / 4) - (n // 4))
        if len(prod)!=0:
            allProducts.append([prod,range(1,nslides),nslides])
    
    params={'allProducts':allProducts,'msg':""}
    if len(allProducts)==0 or len(query)<4:
        params={'msg':"Please make sure to enter relevant search query"}
    return render(request,'shop/search.html',params)

def productview(request,myid):
    #fetch products through id
    product=Product.objects.filter(id=myid)
    #print(product)
    return render(request,'shop/prodView.html',{'product':product[0]})

def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Order(items_json=items_json,name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone,amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank=True
        id=order.order_id
        #return render(request,'shop/checkout.html',{'thank':thank,'id':id})
        # Request paytm to transfer the amount to your account after payment by user
        param_dict = {

                'MID': 'NOCbRM04545621976740',
                'ORDER_ID': str(order.order_id),
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')

@csrf_exempt   #csrf_exempt will help us to bypass this endpoint
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum1 = form[i]

    verify = checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum1)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})






