from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models import F

from .models import Product, Category, Supplier
from .serializers import ProductSerializers, SupplierSerializers, CategorySerializers
# Create your views here.


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category__name']
    ordering_fields = ['name', 'created_at', 'price', 'quantity']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def current_inventory(self, request):
        """
        Retrieve current inventory levels for all items, with optional filters.
        """
        queryset = self.get_queryset()

        # Apply filters based on query parameters
        category = request.query_params.get('category', None)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        low_stock = request.query_params.get('low_stock', None)

        try:
            if min_price:
                min_price = float(min_price)    
            if max_price:
                max_price = float(max_price)
            if low_stock:
                low_stock = bool(int(low_stock))
        except ValueError as e:
            raise ValidationError({"detail": str(e)})

        if category:
            queryset = queryset.filter(category__name=category)
        if min_price:
            queryset = queryset.filter(unit_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(unit_price__lte=max_price)
        if low_stock:
            queryset = queryset.filter(quantity__lte=F('reorder_level'))

        if not queryset.exists():
            return Response({"detail": "No products match the given criteria."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializers
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['contact_person', 'email', 'name']

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializers
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']