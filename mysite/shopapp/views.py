from timeit import default_timer

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from .models import Product, Order


class ShopIndexView(View):
    """
    Представление для отображения главной страницы магазина.

    Отображает список продуктов и время работы сервера.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Обрабатывает GET-запрос и отображает главную страницу магазина.

        Args:
            request (HttpRequest): Объект HTTP-запроса.

        Returns:
            HttpResponse: Отрендеренная HTML-страница с контекстом.
        """
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
        }
        return render(request, 'shopapp/shop-index.html', context=context)


class ProductDetailsView(DetailView):
    """
    Представление для отображения детальной информации о продукте.

    Использует шаблон 'shopapp/products-details.html'.
    """
    template_name = "shopapp/products-details.html"
    model = Product
    context_object_name = "product"


class ProductsListView(ListView):
    """
    Представление для отображения списка активных продуктов.

    Отображает только те продукты, которые не помечены как архивные.
    """
    template_name = "shopapp/products-list.html"
    # model = Product
    context_object_name = "products"
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(CreateView):
    """
    Представление для создания нового продукта.

    После успешного создания перенаправляет на список продуктов.
    """
    model = Product
    fields = "name", "price", "description", "discount", 'preview'
    success_url = reverse_lazy("shopapp:products_list")


class ProductUpdateView(UpdateView):
    """
    Представление для обновления информации о продукте.

    После обновления перенаправляет на страницу деталей продукта.
    """
    model = Product
    fields = "name", "price", "description", "discount", 'preview'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        """
        Возвращает URL для перенаправления после успешного обновления.

        Returns:
            str: URL страницы деталей продукта.
        """
        return reverse(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk},
        )


class ProductDeleteView(DeleteView):
    """
    Представление для "удаления" продукта (пометка как архивный).

    Перенаправляет на список продуктов после архивации.
    """
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        """
        Обрабатывает корректную форму: помечает продукт как архивный.

        Args:
            form: Форма, связанная с моделью Product.

        Returns:
            HttpResponseRedirect: Перенаправление на список продуктов.
        """
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class OrdersListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка заказов.

    Требует авторизации пользователя. Загружает связанные данные пользователя и продуктов.
    """
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class OrderDetailView(PermissionRequiredMixin, DetailView):
    """
    Представление для отображения деталей конкретного заказа.

    Требует наличие права 'shopapp.view_order'.
    """
    permission_required = "shopapp.view_order"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )

class OrderCreateView(CreateView):
    """
    Представление для создания нового заказа.

    После успешного создания перенаправляет на список заказов.
    """
    model = Order
    fields = 'user', 'promocode', 'delivery_address', 'products'
    # form_class = GroupForm
    success_url = reverse_lazy('shopapp:orders_list')

class ProductsDataExportView(View):
    """
    Представление для экспорта данных о продуктах в формате JSON.

    Отдает список всех продуктов с полями: pk, name, price, archived.
    """
    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Обрабатывает GET-запрос и возвращает данные о продуктах в формате JSON.

        Args:
            request (HttpRequest): Объект HTTP-запроса.

        Returns:
            JsonResponse: JSON-ответ со списком продуктов.
        """
        products = Product.objects.order_by('pk').all()
        products_data = [
            {
                'pk': product.pk,
                'name': product.name,
                'price': product.price,
                'archived': product.archived,
            }
            for product in products
        ]
        return JsonResponse({'products': products_data})

class OrdersDataExportView(UserPassesTestMixin, View):
    """
    Представление для экспорта данных о заказах в формате JSON.

    Доступно только для пользователей с флагом is_staff.
    """

    def test_func(self):
        """
        Проверяет, имеет ли пользователь доступ к данному представлению.

        Returns:
            bool: True, если пользователь является администратором (is_staff).
        """
        return self.request.user.is_staff

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Обрабатывает GET-запрос и возвращает данные о заказах в формате JSON.

        Args:
            request (HttpRequest): Объект HTTP-запроса.

        Returns:
            JsonResponse: JSON-ответ со списком заказов и связанных с ними продуктов.
        """
        orders = Order.objects.order_by('pk').all()
        products = Product.objects.order_by('pk').all()

        # Создаем словарь, где ключ — ID заказа, значение — список продуктов
        order_product_map = {}
        for order in orders:
            order_product_map[order.pk] = []
            for product in products:
                if product in order.products.all():
                    order_product_map[order.pk].append({
                        'name': product.name,
                        'price': str(product.price),
                    })
        # Формируем окончательную структуру данных
        order_data = [
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

        return JsonResponse({'orders': order_data})
