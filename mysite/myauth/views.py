from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView

from .models import Profile


class AboutMeView(TemplateView):
    """
    Представление для отображения страницы "Обо мне".
    
    Отображает информацию о текущем пользователе.
    """
    template_name = "myauth/about-me.html"


class RegisterView(CreateView):
    """
    Представление для регистрации новых пользователей.
    
    Создает нового пользователя и автоматически выполняет вход в систему.
    Также создает профиль пользователя после регистрации.
    """
    form_class = UserCreationForm
    template_name = "myauth/register.html"
    success_url = reverse_lazy("myauth:about-me")

    def form_valid(self, form):
        """
        Обрабатывает корректно заполненную форму регистрации.
        
        Создает профиль пользователя, аутентифицирует и логинит пользователя.
        
        Args:
            form: Форма регистрации пользователя (UserCreationForm).
            
        Returns:
            HttpResponse: Ответ после успешной обработки формы.
        """
        response = super().form_valid(form)
        Profile.objects.create(user=self.object)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


class MyLogoutView(LogoutView):
    """
    Представление для выхода пользователя из системы.
    
    После выхода перенаправляет пользователя на страницу входа.
    """
    next_page = reverse_lazy("myauth:login")


@user_passes_test(lambda u: u.is_superuser)
def set_cookie_view(request: HttpRequest) -> HttpResponse:
    """
    Устанавливает cookie для суперпользователя.
    
    Доступно только для суперпользователей (is_superuser=True).
    Устанавливает cookie с именем 'fizz' и значением 'buzz' на 1 час.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса.
        
    Returns:
        HttpResponse: Ответ с сообщением об успешной установке cookie.
    """
    response = HttpResponse("Cookie set")
    response.set_cookie("fizz", "buzz", max_age=3600)
    return response


def get_cookie_view(request: HttpRequest) -> HttpResponse:
    """
    Получает значение cookie с именем 'fizz'.
    
    Если cookie не найдено, возвращает значение по умолчанию.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса.
        
    Returns:
        HttpResponse: Ответ со значением cookie или значением по умолчанию.
    """
    value = request.COOKIES.get("fizz", "default value")
    return HttpResponse(f"Cookie value: {value!r}")


@permission_required("myauth.view_profile", raise_exception=True)
def set_session_view(request: HttpRequest) -> HttpResponse:
    """
    Устанавливает значение в сессии пользователя.
    
    Требует наличия права 'myauth.view_profile'.
    Устанавливает в сессии ключ 'foobar' со значением 'spameggs'.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса.
        
    Returns:
        HttpResponse: Ответ с сообщением об успешной установке сессии.
    """
    request.session["foobar"] = "spameggs"
    return HttpResponse("Session set!")


@login_required
def get_session_view(request: HttpRequest) -> HttpResponse:
     """
    Получает значение из сессии пользователя.
    
    Требует аутентификации пользователя.
    Получает значение по ключу 'foobar' из сессии или возвращает значение по умолчанию.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса.
        
    Returns:
        HttpResponse: Ответ со значением из сессии или значением по умолчанию.
    """
    value = request.session.get("foobar", "default")
    return HttpResponse(f"Session value: {value!r}")

