import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType

from saleor.graphql.core.fields import FilterConnectionField
from vendor.graphql.filters import TransactionFilterInput

from saleor.graphql.account.enums import CountryCodeEnum
from saleor.graphql.core.connection import (
    create_connection_slice,
    filter_connection_queryset,
)
from saleor.graphql.core.types import Upload
from saleor.graphql.core.connection import CountableConnection
from saleor.graphql.core.types.common import Image
from vendor import models
from vendor.graphql import enums

class CountableDjangoObjectType(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__), node=cls
        )
        super().__init_subclass_with_meta__(*args, connection=countable_conn, **kwargs)


class VendorTransaction(CountableDjangoObjectType):
    user = graphene.Field(graphene.ID, description="ID of user .")
    payment = graphene.Field(graphene.ID, description="ID of payment.")

    class Meta:
        model = models.Transaction
        filter_fields = ["id", "currency", "payment"]
        interfaces = (graphene.relay.Node,)

    def resolve_user(root, info):
        return graphene.Node.to_global_id("User", root.user.id)

    def resolve_payment(root, info):
        if root.payment:
            return graphene.Node.to_global_id("Payment", root.payment.id)


class VendorTransactionConnection(relay.Connection):
    class Meta:
        node = VendorTransaction


class Vendor(CountableDjangoObjectType):
    users = graphene.List(graphene.ID, description="List of user IDs.")
    products = graphene.List(graphene.ID, description="List of products IDs.")
    logo = graphene.Field(Image, size=graphene.Int(description="Size of the image."))
    header_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    description = graphene.JSONString(description="Editorjs formatted description.")
    country = CountryCodeEnum(description="Country.")
    target_gender = enums.TargetGender(description="Target gender of the vendor.")
    registration_type = enums.RegistrationType(
        description="Company registration type of the vendor."
    )
    transactions = FilterConnectionField(
        VendorTransactionConnection,
        filter=TransactionFilterInput(description="Filtering options for Transaction."),
    )

    class Meta:
        model = models.Vendor
        filter_fields = ["id", "name", "country"]
        interfaces = (graphene.relay.Node,)
        exclude = ["address"]

    def resolve_users(root, info):
        return [
            graphene.Node.to_global_id("User", id)
            for id in root.users.values_list("id", flat=True)
        ]

    def resolve_products(root, info):
        return [
            graphene.Node.to_global_id("Product", id)
            for id in root.products.values_list("id", flat=True)
        ]

    def resolve_logo(root, info, size=None):
        if root.logo:
            return Image.get_adjusted(
                info=info,
                size=size,
                image=root.logo,
                rendition_key_set="logo",
                alt=f"{root.brand_name}'s logo",
            )

    def resolve_header_image(root, info, size=None):
        if root.header_image:
            return Image.get_adjusted(
                size=size,
                info=info,
                image=root.header_image,
                rendition_key_set="background_images",
                alt=f"{root.brand_name}'s header image",
            )

    def resolve_transactions(root, info, **kwargs):
        groups = models.Transaction.objects.filter(vendor=root)
        qs = filter_connection_queryset(groups, kwargs)

        return create_connection_slice(qs, info, kwargs, VendorTransactionConnection)


class VendorConnection(relay.Connection):
    class Meta:
        node = Vendor


class Billing(CountableDjangoObjectType):
    class Meta:
        model = models.BillingInfo
        filter_fields = ["id", "iban", "bank_name"]
        interfaces = (graphene.relay.Node,)


class BillingConnection(relay.Connection):
    class Meta:
        node = Billing


class Attachment(CountableDjangoObjectType):
    vendor = graphene.Field(Vendor, required=True, description="Vendor.")
    file = Upload(required=True, description="File to be attached.")

    class Meta:
        model = models.Attachment
        interfaces = (graphene.relay.Node,)


class Commission(CountableDjangoObjectType):
    vendor = graphene.Field(Vendor)
    category = graphene.Field(graphene.ID, description="ID of category .")

    class Meta:
        model = models.Commission
        filter_fields = ["id", "name", "type"]
        interfaces = (graphene.relay.Node,)

    def resolve_vendor(root, info):
        return root.vendor

    def resolve_category(root, info):
        return graphene.Node.to_global_id("Category", root.category.id)


class CommissionConnection(relay.Connection):
    class Meta:
        node = Commission
