import django_filters
from django.db.models import Q
from saleor.graphql.account.enums import CountryCodeEnum
from saleor.graphql.core.filters import EnumFilter
from saleor.graphql.core.types.filter_input import FilterInputObjectType

from vendor import models


def filter_by_query_param(queryset, query, search_fields):
    """Filter queryset according to given parameters.

    Keyword Arguments:
        queryset - queryset to be filtered
        query - search string
        search_fields - fields considered in filtering

    """
    if query:
        query_by = {
            "{0}__{1}".format(field, "icontains"): query for field in search_fields
        }
        query_objects = Q()
        for q in query_by:
            query_objects |= Q(**{q: query_by[q]})
        return queryset.filter(query_objects).distinct()
    return queryset


def filter_vendor_country(qs, _, value):
    return qs.filter(country=value)


def filter_vendor_search(qs, _, value):
    vendor_fields = [
        "brand_name",
    ]
    qs = filter_by_query_param(qs, value, vendor_fields)
    return qs


def filter_transaction_search(qs, _, value):
    transaction_fields = [
        "name",
    ]
    qs = filter_by_query_param(qs, value, transaction_fields)
    return qs


def filter_transaction_date_range(qs, _, value):

    qs = qs.filter(**{f"{_}__range": value.split(",")})
    return qs


class VendorFilter(django_filters.FilterSet):
    country = EnumFilter(input_class=CountryCodeEnum, method=filter_vendor_country)
    search = django_filters.CharFilter(method=filter_vendor_search)

    class Meta:
        model = models.Vendor
        fields = ["country", "search"]


class VendorFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = VendorFilter


class TransactionFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_transaction_search)
    created_at = django_filters.CharFilter(method=filter_transaction_date_range)

    class Meta:
        model = models.Transaction
        fields = ["search", "created_at"]


class TransactionFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = TransactionFilter
