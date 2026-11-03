from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api

router = DefaultRouter()
router.register("produtos", api.ProdutoViewSet, basename="produto")
router.register("movimentacoes", api.MovimentacaoViewSet, basename="movimentacao")
router.register("fornecedores", api.FornecedorViewSet, basename="fornecedor")

urlpatterns = [
    path("api/cep/<str:cep>/", api.CepView.as_view(), name="api-cep"),
    path("api/", include(router.urls)),
]
