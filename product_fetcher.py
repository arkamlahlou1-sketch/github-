import os
import json
from datetime import datetime
from aliexpress_api import AliexpressApi, models

# 1. قراءة الأسرار من متغيرات البيئة (من GitHub Action)
APP_KEY = os.getenv('APP_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID') 

# 2. تهيئة عميل API
# ملاحظة: اللغة والعملة مهمان، يمكنك تعديلهما.
aliexpress = AliexpressApi(
    APP_KEY, 
    SECRET_KEY, 
    models.Language.EN, # يمكن استخدام AR إذا كانت مدعومة بالكامل
    models.Currency.USD, 
    TRACKING_ID
)

def fetch_daily_deals():
    """يسحب المنتجات الساخنة (Hot Products) ويولد روابط تتبع لكل منها."""
    
    if not APP_KEY or not SECRET_KEY or not TRACKING_ID:
        print("❌ خطأ: مفاتيح API أو Tracking ID مفقودة. تأكد من إعداد GitHub Secrets.")
        return []

    products_list = []
    
    try:
        # جلب المنتجات الساخنة (مثال: يمكنك استخدام get_products بـ keywords محددة)
        response = aliexpress.get_hotproducts(
            category_id='6',  # يمكنك تغيير هذا لتصفية فئة معينة
            page_size=30      # جلب 30 منتجاً
        )
        
        for product in response.products:
            # 1. توليد رابط التتبع الخاص بالمنتج
            affiliate_link_obj = aliexpress.get_affiliate_links(product.product_url)
            final_link = affiliate_link_obj[0].promotion_link if affiliate_link_obj else product.product_url
            
            # 2. حساب الخصم (إذا كانت البيانات متوفرة)
            try:
                original = float(product.original_price.replace('$', '').replace(',', ''))
                sale = float(product.target_sale_price.replace('$', '').replace(',', ''))
                discount_percent = f"{round(((original - sale) / original) * 100)}%" if original > sale else "0%"
            except (ValueError, AttributeError):
                discount_percent = "N/A"
            
            # 3. حفظ بيانات المنتج النهائية
            products_list.append({
                "id": product.product_id,
                "name": product.product_title,
                "price": f"{product.target_sale_price}", 
                "original_price": f"{product.original_price}",
                "discount": discount_percent,
                "link": final_link, # رابط التتبع الخاص بك
                "image": product.product_main_image_url
            })

        return products_list
        
    except Exception as e:
        print(f"❌ فشل في الاتصال بالـ API: {e}")
        return []

def save_products_to_json(products):
    """يكتب قائمة المنتجات في ملف products.json."""
    try:
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        print(f"✅ تم تحديث {len(products)} منتجاً بنجاح في products.json.")
    except Exception as e:
        print(f"❌ فشل في كتابة ملف JSON: {e}")

if __name__ == "__main__":
    print(f"🔄 بدء جلب عروض AliExpress اليومية...")
    
    deals = fetch_daily_deals()
    
    if deals:
        save_products_to_json(deals)
    else:
        print("⚠️ لم يتم جلب أي عروض. لم يتم تحديث الملف.")
