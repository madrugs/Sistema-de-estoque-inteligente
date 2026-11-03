from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import api, views

router = DefaultRouter()
router.register("produtos", api.ProdutoViewSet, basename="produto")
router.register("movimentacoes", api.MovimentacaoViewSet, basename="movimentacao")
router.register("fornecedores", api.FornecedorViewSet, basename="fornecedor")

urlpatterns = [
    # Páginas
    path("", login_required(RedirectView.as_view(pattern_name="estoque-lista")), name="dashboard"),
    path("estoque/", views.estoque_lista, name="estoque-lista"),
    path("movimentar/", views.movimentar, name="movimentar"),
    path("historico/", views.historico, name="historico"),
    # API REST (JSON)
    path("api/cep/<str:cep>/", api.CepView.as_view(), name="api-cep"),
    path("api/", include(router.urls)),
]
