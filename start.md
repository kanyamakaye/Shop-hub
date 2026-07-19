Django Implementation Documentation
SaaS Multi-Tenant E-Commerce Platform
________________________________________
1. Subscription Plans Module
Model
Model Name: SubscriptionPlan
Field	Type
plan_name	CharField
monthly_price	DecimalField
yearly_price	DecimalField
max_products	IntegerField
max_users	IntegerField
status	CharField
views.py
SubscriptionPlanListView
SubscriptionPlanCreateView
SubscriptionPlanUpdateView
SubscriptionPlanDeleteView
or
plan_list()
plan_create()
plan_update()
plan_delete()
urls.py
plans/
plans/create/
plans/<id>/edit/
plans/<id>/delete/
Templates
templates/plans/

plan_list.html
plan_form.html
plan_delete.html
Technologies
•	HTML 
•	Tailwind CSS 
•	JavaScript 
Functions
•	Search 
•	Pagination 
•	Confirmation dialog before delete 
________________________________________
2. Tenants Module
Model
Tenant
Fields
•	plan (ForeignKey) 
•	business_name 
•	email 
•	phone 
•	country 
•	address 
•	logo 
•	status 
Views
tenant_list()

tenant_create()

tenant_update()

tenant_delete()

tenant_detail()
URLs
tenants/

tenants/create/

tenants/<id>/

tenants/<id>/edit/

tenants/<id>/delete/
Templates
tenant_list.html

tenant_form.html

tenant_detail.html

tenant_delete.html
________________________________________
3. Users Module
Model
Use
AbstractUser
or
AbstractBaseUser
Additional fields
•	tenant 
•	phone 
•	role 
•	province 
•	district 
•	sector 
•	cell 
•	village 
•	postal_address 
•	status 
Views
user_list

user_create

user_update

user_delete

user_profile
URLs
users/

users/create/

users/<id>/

users/<id>/edit/

users/<id>/delete/
Templates
user_list.html

user_form.html

user_profile.html

user_delete.html
________________________________________
4. Categories Module
Model
Category
Fields
•	tenant 
•	category_name 
•	description 
Views
category_list

category_create

category_update

category_delete
URLs
categories/

categories/create/

categories/edit/<id>/

categories/delete/<id>/
Templates
category_list.html

category_form.html

category_delete.html
________________________________________
5. Products Module
Model
Product
Fields
•	tenant 
•	category 
•	sku 
•	product_name 
•	description 
•	image 
•	price 
•	discount_price 
•	status 
Views
product_list

product_detail

product_create

product_update

product_delete
URLs
products/

products/create/

products/<id>/

products/edit/<id>/

products/delete/<id>/
Templates
product_list.html

product_detail.html

product_form.html

product_delete.html
JavaScript
•	Image preview 
•	Product search 
•	Price validation 
________________________________________
6. Cart Module
Model
Cart
Fields
•	user 
•	product 
•	quantity 
•	added_date 
Views
cart_list

add_to_cart

update_cart

remove_cart
URLs
cart/

cart/add/<product_id>/

cart/update/<id>/

cart/delete/<id>/
Templates
cart.html
JavaScript
•	Quantity increase 
•	Quantity decrease 
•	Total calculation 
________________________________________
7. Orders Module
Model
Order
Fields
•	tenant 
•	user 
•	order_date 
•	total_amount 
•	payment_method 
•	payment_status 
•	order_status 
•	shipping_address 
•	transaction_reference 
Views
order_list

order_detail

checkout

order_update
URLs
orders/

orders/<id>/

checkout/
Templates
order_list.html

order_detail.html

checkout.html
JavaScript
•	Checkout validation 
•	Payment selection 
________________________________________
8. Order Items Module
Model
OrderItem
Fields
•	order 
•	product 
•	quantity 
•	unit_price 
•	subtotal 
Views
order_item_list

order_item_detail
Templates
order_items.html
________________________________________
9. Reviews Module
Model
Review
Fields
•	user 
•	product 
•	rating 
•	comment 
•	review_date 
Views
review_create

review_update

review_delete
URLs
reviews/add/<product_id>/

reviews/edit/<id>/

reviews/delete/<id>/
Templates
review_form.html
JavaScript
•	Star rating 
________________________________________
10. Wishlist Module
Model
Wishlist
Fields
•	user 
•	product 
Views
wishlist

wishlist_add

wishlist_remove
URLs
wishlist/

wishlist/add/<product_id>/

wishlist/remove/<id>/
Templates
wishlist.html
________________________________________
11. Notifications Module
Model
Notification
Fields
•	tenant 
•	user 
•	title 
•	message 
•	notification_type 
•	is_read 
•	created_at 
Views
notification_list

notification_read

notification_delete
URLs
notifications/

notifications/read/<id>/

notifications/delete/<id>/
Templates
notification_list.html
________________________________________
Authentication Module
Views
login

logout

register

forgot_password

change_password
Templates
login.html

register.html

forgot_password.html

change_password.html
________________________________________
Dashboard Module
Views
owner_dashboard

tenant_dashboard

customer_dashboard
Templates
owner_dashboard.html

tenant_dashboard.html

customer_dashboard.html
Dashboard widgets
Owner Dashboard
•	Total Tenants 
•	Total Revenue 
•	Active Plans 
•	Active Users 
Tenant Dashboard
•	Products 
•	Orders 
•	Customers 
•	Sales 
•	Revenue 
Customer Dashboard
•	Orders 
•	Wishlist 
•	Reviews 
•	Notifications 
________________________________________
Suggested Django Project Structure
saas_ecommerce/
│
├── accounts/
│     models.py
│     views.py
│     urls.py
│
├── subscriptions/
│
├── tenants/
│
├── products/
│
├── categories/
│
├── cart/
│
├── orders/
│
├── reviews/
│
├── wishlist/
│
├── notifications/
│
├── dashboard/
│
├── templates/
│
│    base.html
│    navbar.html
│    sidebar.html
│    footer.html
│
│    accounts/
│    products/
│    categories/
│    cart/
│    orders/
│    reviews/
│    wishlist/
│    notifications/
│    dashboard/
│
├── static/
│
│    css/
│        tailwind.css
│
│    js/
│        app.js
│        cart.js
│        dashboard.js
│        search.js
│
│    images/
│
├── media/
│
└── manage.py
Template Design Guidelines (HTML + Tailwind CSS + JavaScript)
Create a consistent layout with:
•	base.html: Common layout including Tailwind CSS, navigation, sidebar, footer, and script imports. 
•	navbar.html: Logo, search bar, notifications dropdown, user profile menu, and logout. 
•	sidebar.html: Role-based navigation (System Owner, Tenant Admin, Customer). 
•	footer.html: Copyright and quick links. 
Each feature page (e.g., Products, Orders, Categories) should:
•	Extend base.html. 
•	Use Tailwind CSS cards, tables, forms, badges, and modals. 
•	Use JavaScript for client-side validation, dynamic search/filtering, confirmation dialogs, image previews, and interactive UI elements. 
This structure is scalable, follows Django best practices, and clearly maps each business entity in your sample data to its corresponding Model, View, URL, and Template, making it suitable for both implementation and academic or project documentation.


sample data

1. SubscriptionPlans
plan_id	plan_name	monthly_price	yearly_price	max_products	max_users	status
1	Basic	20.00	200.00	100	5	Active
2	Professional	50.00	500.00	1000	20	Active
3	Enterprise	150.00	1500.00	Unlimited	Unlimited	Active

2. Tenants
tenant_id	plan_id	business_name	email	phone	country	address	logo	status
1	2	Kigali Electronics Ltd	info@kigalielectronics.rw	+250788111111	Rwanda	Kigali City	kigali_logo.png	Active
2	1	Rwanda Fashion Store	sales@rwfashion.rw	+250788222222	Rwanda	Musanze	fashion_logo.png	Active








3. Users
user_id	tenant_id	first_name	last_name	email	phone	password	role	country	province	district	sector	cell	village	postal_address	status	created_at
1	NULL	James	Smith	owner@eshop.com	+250788000001	********	System Owner	Rwanda	Kigali City	Gasabo	Remera	Rukiri II	Nyabisindu	NULL	Active	2026-01-01
2	1	Jean	Niyonsenga	admin@kigalielectronics.rw	+250788100001	********	System Admin	Rwanda	Kigali City	Gasabo	Kimironko	Bibare	Kibagabaga	NULL	Active	2026-01-05
3	2	Eric	Habimana	admin@rwfashion.rw	+250788100002	********	System Admin	Rwanda	Northern	Musanze	Muhoza	Cyabararika	Kabazungu	NULL	Active	2026-01-06
4	1	Patrick	Uwimana	patrick@gmail.com	+250788100003	********	User	Rwanda	Kigali City	Kicukiro	Kagarama	Kanserege	Nyenyeri	NULL	Active	2026-02-10
5	1	Alice	Mukamana	alice@gmail.com	+250788100004	********	User	Rwanda	Eastern	Rwamagana	Kigabiro	Sovu	Cyanya	NULL	Active	2026-02-15
6	2	Diane	Uwase	diane@gmail.com	+250788100005	********	User	Rwanda	Western	Rubavu	Gisenyi	Amahoro	Bugoyi	NULL	Active	2026-03-01
7	2	Peter	Otieno	peter@gmail.com	+254712345678	********	User	Kenya	NULL	NULL	NULL	NULL	NULL	Nairobi	Active	2026-03-15

4. Categories
category_id	tenant_id	category_name	description
1	1	Smartphones	Mobile phones
2	1	Laptops	Computers and laptops
3	1	Accessories	Electronic accessories
4	2	Shoes	Men's and Women's shoes
5	2	Clothing	Clothes and fashion
6	2	Bags	Fashion bags


5. Products
product_id	tenant_id	category_id	sku	product_name	description	image	price	discount_price	status
1	1	1	IP15	Apple iPhone 15	128GB Black	iphone15.jpg	1200	1100	Active
2	1	1	SGS24	Samsung Galaxy S24	256GB Gray	s24.jpg	950	900	Active
3	1	2	DELL15	Dell Inspiron 15	Intel Core i7 Laptop	dell15.jpg	800	760	Active
4	1	3	AIRP01	Apple AirPods Pro	Wireless Earbuds	airpods.jpg	250	220	Active
5	2	4	NK001	Nike Air Max	Running Shoes	nike.jpg	150	130	Active
6	2	5	TS001	Cotton T-Shirt	Blue Cotton Shirt	tshirt.jpg	25	20	Active
7	2	6	BG001	Leather Backpack	Brown Backpack	bag.jpg	80	70	Active





6. Cart
cart_id	user_id	product_id	quantity	added_date
1	4	2	1	2026-07-10
2	4	4	2	2026-07-10
3	5	3	1	2026-07-11
4	6	5	2	2026-07-12
5	7	7	1	2026-07-13

7. Orders
order_id	tenant_id	user_id	order_date	total_amount	payment_method	payment_status	order_status	shipping_address	transaction_reference
1	1	4	2026-07-12	1100	Visa Card	Paid	Delivered	Kagarama, Kicukiro	TXN100001
2	1	5	2026-07-13	760	Mobile Money	Paid	Processing	Kigabiro, Rwamagana	TXN100002
3	2	6	2026-07-14	260	Bank Transfer	Pending	Pending	Gisenyi, Rubavu	TXN100003
4	2	7	2026-07-15	70	Credit Card	Paid	Shipped	Nairobi, Kenya	TXN100004



8. OrderItems
order_item_id	order_id	product_id	quantity	unit_price	subtotal
1	1	1	1	1100	1100
2	2	3	1	760	760
3	3	5	2	130	260
4	4	7	1	70	70

9. Reviews
review_id	user_id	product_id	rating	comment	review_date
1	4	1	5	Excellent phone with great battery life.	2026-07-15
2	5	3	4	Very good laptop for office work.	2026-07-16
3	6	5	5	Comfortable shoes.	2026-07-17
4	7	7	4	Nice quality backpack.	2026-07-18

10. Wishlist
wishlist_id	user_id	product_id
1	4	2
2	4	4
3	5	1
4	6	6
5	7	5

11. Notifications
notification_id	tenant_id	user_id	title	message	notification_type	is_read	created_at
1	1	2	New Order	Order #1 has been placed by Patrick Uwimana.	Order	No	2026-07-12 09:30
2	1	4	Payment Successful	Your payment for Order #1 was successful.	Payment	Yes	2026-07-12 09:35
3	1	5	Order Processing	Your laptop order is being processed.	Order	No	2026-07-13 14:00
4	2	3	New Order	Order #3 has been received.	Order	No	2026-07-14 11:20
5	2	6	Payment Pending	Please complete your payment to process the order.	Payment	No	2026-07-14 11:25
6	2	7	Order Shipped	Your backpack has been shipped.	Shipping	Yes	2026-07-15 16:40



This sample data represents a realistic workflow where:
•	James Smith is the System Owner of the SaaS platform. 
•	Two businesses (Kigali Electronics Ltd and Rwanda Fashion Store) are tenants. 
•	Each tenant has its own System Admin. 
•	Registered Users purchase products from their tenant's store. 
•	Products are organized into categories, added to carts, purchased through orders, reviewed, and saved in wishlists. 
•	Notifications keep both customers and administrators informed about orders and payments.

