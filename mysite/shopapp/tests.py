from string import ascii_letters
from random import choices

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from shopapp.utils import add_two_numbers
from shopapp.models import Product, Order


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(2, 3)
        self.assertEqual(result, 5)

class ProductCreateViewTestCase(TestCase):
    def setUp(self):
        self.product_name = ''.join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()

    def test_create_product(self):
       response = self.client.post(
            reverse('shopapp:product_create'),
            {
                'name': self.product_name,
                'price': '123.45',
                'description': 'A good table',
                'discount': '10',

            },
           follow=True
        )
       self.assertRedirects(response, reverse('shopapp:products_list'))
       self.assertTrue(
           Product.objects.filter(name=self.product_name).exists()
       )

class ProductDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.product = Product.objects.create(name='Best product')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.product.delete()

    def test_get_product(self):
        response = self.client.get(
            reverse('shopapp:product_details', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_product_and_check_content(self):
        response = self.client.get(
            reverse('shopapp:product_details', kwargs={'pk': self.product.pk})
        )
        self.assertContains(response, self.product.name)


import json

class ProductsListViewTestCase(TestCase):
    fixtures = [
        'products-fixtures.json',
    ]

    def test_products(self):
        response = self.client.get(reverse('shopapp:products_list'))
        self.assertQuerysetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context['products']),
            transform=lambda p: p.pk
        )
        self.assertTemplateUsed(response, 'shopapp/products-list.html')

class OrdersListViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.credentials = dict
        cls.user = User.objects.create_user(username='testuser', password='qwerty')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_orders_view(self):
        response = self.client.get(reverse('shopapp:orders_list'))
        self.assertContains(response, 'Orders')

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse('shopapp:orders_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)

class OrderDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='testuser', password='qwerty')
        cls.order = Order.objects.create(user_id=1, id=1)

    @classmethod
    def tearDownClass(cls):
        cls.order.delete()
        cls.user.delete()


    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.user.user_permissions.add(32)


    def test_get_order(self):
        response = self.client.get(
            reverse('shopapp:order_details', kwargs={'pk': self.order.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_order_and_check_promocode(self):
        response = self.client.get(
            reverse('shopapp:order_details', kwargs={'pk': self.order.pk})
        )
        self.assertContains(response, self.order.promocode)

    def test_order_detail_contains_correct_data(self):
        response = self.client.get(reverse('shopapp:order_details', kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Order #{self.order.pk}')


class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'products-fixtures.json'
    ]

    def test_get_products_view(self):
        response = self.client.get(reverse(
            'shopapp:products_export'
        ))
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by('pk').all()
        expected_data = [
            {
                'pk': product.pk,
                'name': product.name,
                'price': str(product.price),
                'archived': product.archived,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data['products'],
            expected_data,
        )


class OrdersExportTestCase(TestCase):
    fixtures = [
        'user-fixtures.json',
        'orders-fixtures.json',
        'products-fixtures.json',

    ]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser', password='qwerty', is_staff=True)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_get_orders_view(self):

        response = self.client.get(
            reverse('shopapp:orders_export')
        )
        self.assertEqual(response.status_code, 200)
        orders = Order.objects.order_by('pk').all()
        products = Product.objects.order_by('pk').all()

        order_product_map = {}
        for order in orders:
            order_product_map[order.pk] = []
            for product in products:
                if product in order.products.all():
                    order_product_map[order.pk].append({
                        'name': product.name,
                        'price': str(product.price),
                    })


        expected_data = [
            {
                'pk': order.pk,
                'delivery_address': order.delivery_address,
                'created_at': str(order.created_at),
                'user_id': order.user_id,
                'promocode': str(order.promocode),
                'products': order_product_map[order.pk],
            }
            for order in orders
        ]
        orders_data = response.json()
        self.assertEqual(
            orders_data['orders'],
            expected_data,
        )
