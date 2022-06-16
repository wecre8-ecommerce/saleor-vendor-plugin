import graphene
from saleor.graphql.core.types import SortInputObjectType


class VendorOrderField(graphene.Enum):
    NAME = ["brand_name", "first_name", "last_name"]


class VendorOrder(SortInputObjectType):
    field = graphene.Argument(
        VendorOrderField, description="Sort vendors by the selected field."
    )

    class Meta:
        type_name = "vendors"
        sort_enum = VendorOrderField
