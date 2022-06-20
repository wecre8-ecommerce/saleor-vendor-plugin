import graphene
from graphene_federation import build_schema
from saleor.graphql.core.connection import (
    create_connection_slice,
    filter_connection_queryset,
)
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.utils import from_global_id_or_error
from saleor.product.models import Product

from vendor import models
from vendor.graphql import types
from vendor.graphql.filters import TransactionFilterInput, VendorFilterInput
from vendor.graphql.mutations import (
    BillingInfoCreate,
    BillingInfoDelete,
    BillingInfoUpdate,
    CommissionAddCategory,
    CommissionCreate,
    CommissionDelete,
    CommissionRemoveCategory,
    CommissionUpdate,
    TransactionAddPayment,
    TransactionAddUser,
    TransactionDelete,
    VendorAddAttachment,
    VendorAddProduct,
    VendorAddUser,
    VendorCreate,
    VendorDelete,
    VendorRemoveAttachment,
    VendorRemoveProduct,
    VendorRemoveUser,
    VendorTransactionCreate,
    VendorTransactionUpdate,
    VendorUpdate,
    VendorUpdateHeader,
    VendorUpdateLogo,
)
from vendor.graphql.sorters import VendorOrder


class Query(graphene.ObjectType):
    vendor = graphene.Field(
        types.Vendor,
        id=graphene.Argument(graphene.ID, description="Vendor ID.", required=True),
        description="Look up a vendor by ID",
    )
    vendors = FilterConnectionField(
        types.VendorConnection,
        description="List of the shop's vendors.",
        sort_by=VendorOrder(description="Sort vendors."),
        filter=VendorFilterInput(description="Filtering options for vendors."),
        ids=graphene.List(graphene.ID, description="Filter vendors by given IDs."),
    )
    product_vendors = FilterConnectionField(
        types.VendorConnection,
        product_slug=graphene.Argument(
            graphene.String, description="product slug.", required=True
        ),
        description="Look up a vendor by product id",
    )

    billing_info = graphene.Field(
        types.Billing,
        id=graphene.Argument(graphene.ID, description="ID of Billing", required=True),
        description="Look up billing information by ID",
    )
    billing_infos = FilterConnectionField(types.BillingConnection)

    transaction = graphene.Field(
        types.VendorTransaction,
        id=graphene.Argument(
            graphene.ID, description="ID of the Transaction", required=True
        ),
        description="Look up a Transaction by ID",
    )
    transactions = FilterConnectionField(
        types.VendorTransactionConnection,
        filter=TransactionFilterInput(description="Filtering options for Transaction."),
    )

    commission = graphene.Field(
        types.Commission,
        id=graphene.Argument(
            graphene.ID, description="ID of the commission", required=True
        ),
        description="Look up a commission by ID",
    )
    commissions = FilterConnectionField(types.CommissionConnection)

    def resolve_vendors(self, info, ids=None, **kwargs):
        qs = models.Vendor.objects.all()
        if ids:
            vendor_ids = BaseMutation.get_global_ids_or_error(
                ids, only_type="Vendor", field="vendors"
            )
            qs = models.Vendor.objects.filter(pk__in=vendor_ids)

        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, types.VendorConnection)

    def resolve_vendor(self, info, id, **data):
        _, id = from_global_id_or_error(id, types.Vendor)
        return models.Vendor.objects.get(id=id)

    def resolve_billing_infos(root, info, **kwargs):
        qs = models.BillingInfo.objects.all()
        return create_connection_slice(qs, info, kwargs, types.BillingConnection)

    def resolve_billing_info(root, info, id, **data):
        _, id = from_global_id_or_error(id, types.Billing)
        return models.BillingInfo.objects.get(id=id)

    def resolve_product_vendors(root, info, product_slug, **kwargs):
        product = Product.objects.filter(slug=product_slug).first()
        qs = product.vendor_set.all()
        return create_connection_slice(qs, info, kwargs, types.VendorConnection)

    def resolve_transactions(root, info, **kwargs):
        groups = models.Transaction.objects.all()
        qs = filter_connection_queryset(groups, kwargs)
        return create_connection_slice(
            qs, info, kwargs, types.VendorTransactionConnection
        )

    def resolve_transaction(root, info, id, **data):
        _, id = from_global_id_or_error(id, types.VendorTransaction)
        return models.Transaction.objects.get(id=id)

    def resolve_commissions(root, info, **kwargs):
        qs = models.Commission.objects.all()
        return create_connection_slice(qs, info, kwargs, types.CommissionConnection)

    def resolve_commission(self, info, id, **data):
        _, id = from_global_id_or_error(id, types.Commission)
        return models.Commission.objects.get(id=id)


class Mutation(graphene.ObjectType):
    vendor_create = VendorCreate.Field()
    vendor_update = VendorUpdate.Field()
    vendor_delete = VendorDelete.Field()

    vendor_add_product = VendorAddProduct.Field()
    vendor_remove_product = VendorRemoveProduct.Field()

    vendor_add_user = VendorAddUser.Field()
    vendor_remove_user = VendorRemoveUser.Field()

    vendor_add_attachment = VendorAddAttachment.Field()
    vendor_remove_attachment = VendorRemoveAttachment.Field()

    vendor_update_logo = VendorUpdateLogo.Field()
    vendor_update_header = VendorUpdateHeader.Field()

    billing_info_create = BillingInfoCreate.Field()
    billing_info_update = BillingInfoUpdate.Field()
    billing_info_delete = BillingInfoDelete.Field()

    vendor_transaction_delete = TransactionDelete.Field()
    vendor_transaction_create = VendorTransactionCreate.Field()
    vendor_transaction_update = VendorTransactionUpdate.Field()

    transaction_add_payment = TransactionAddPayment.Field()

    transaction_add_user = TransactionAddUser.Field()

    commission_create = CommissionCreate.Field()
    commission_update = CommissionUpdate.Field()
    commission_delete = CommissionDelete.Field()

    commission_add_category = CommissionAddCategory.Field()
    commission_remove_category = CommissionRemoveCategory.Field()


schema = build_schema(
    query=Query,
    mutation=Mutation,
    types=[types.Vendor],
)
