import json
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import Client, Manager, Order, OrderItem


class OrderItemUpdateCountTests(TestCase):
    def setUp(self):
        manager_group, _ = Group.objects.get_or_create(name='manager')

        self.manager_user = User.objects.create_user(username='manager1', password='pass12345')
        self.manager_user.groups.add(manager_group)
        Manager.objects.create(user=self.manager_user, name='Test Manager', phone='+70000000000')

        client_user = User.objects.create_user(username='client1', password='pass12345')
        self.client_profile = Client.objects.create(user=client_user, name='Test Client', phone='+71111111111')

        self.order = Order.objects.create(client=self.client_profile, status='NEW', initial_requirements='req')
        self.item = OrderItem.objects.create(
            order=self.order,
            article_number='ART1',
            manufacture='ACME',
            name='Brake pad',
            count=2,
            purchase_price=Decimal('100.00'),
            discount=Decimal('0.00'),
            price=Decimal('300.00'),
        )

    def update_count(self, item_id, count):
        return self.client.patch(
            reverse('orders:update_order_item_count', args=[item_id]),
            data=json.dumps({'count': count}),
            content_type='application/json',
        )

    def test_order_detail_renders_editable_count_controls(self):
        self.client.login(username='manager1', password='pass12345')

        response = self.client.get(reverse('orders:detail', args=[self.order.id]))

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('count-input', html)
        self.assertIn('apply-count-btn', html)
        self.assertIn(f'data-item-id="{self.item.id}"', html)

    def test_update_count_recalculates_price(self):
        self.client.login(username='manager1', password='pass12345')

        response = self.update_count(self.item.id, 5)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'success': True,
            'item': {'id': self.item.id, 'count': 5, 'price': '650'},
        })

        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 5)
        self.assertEqual(self.item.price, Decimal('650.00'))

    def test_update_count_without_purchase_price_scales_existing_price(self):
        self.client.login(username='manager1', password='pass12345')
        self.item.purchase_price = None
        self.item.count = 4
        self.item.price = Decimal('400.00')
        self.item.save()

        response = self.update_count(self.item.id, 6)

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 6)
        self.assertEqual(self.item.price, Decimal('600.00'))

    def test_update_count_rejects_non_integer_value(self):
        self.client.login(username='manager1', password='pass12345')

        response = self.update_count(self.item.id, 'abc')

        self.assertEqual(response.status_code, 400)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 2)
        self.assertEqual(self.item.price, Decimal('300.00'))

    def test_update_count_rejects_zero(self):
        self.client.login(username='manager1', password='pass12345')

        response = self.update_count(self.item.id, 0)

        self.assertEqual(response.status_code, 400)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 2)

    def test_update_count_rejects_invalid_json_body(self):
        self.client.login(username='manager1', password='pass12345')

        response = self.client.patch(
            reverse('orders:update_order_item_count', args=[self.item.id]),
            data='not-json',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)

    def test_update_count_returns_404_for_unknown_item(self):
        self.client.login(username='manager1', password='pass12345')

        response = self.update_count(999999, 5)

        self.assertEqual(response.status_code, 404)

    def test_update_count_requires_login(self):
        response = self.update_count(self.item.id, 5)

        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 2)

    def test_update_count_denies_non_manager_user(self):
        User.objects.create_user(username='outsider', password='pass12345')
        self.client.login(username='outsider', password='pass12345')

        response = self.update_count(self.item.id, 5)

        # Authenticated but unauthorized users get 403 (vs. a login redirect for anonymous users).
        self.assertEqual(response.status_code, 403)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 2)
