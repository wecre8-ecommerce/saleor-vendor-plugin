import graphene
from saleor.graphql.core.types.common import Error

from vendor.graphql import enums

VendorErrorCode = graphene.Enum.from_enum(enums.VendorErrorCode)
BillingErrorCode = graphene.Enum.from_enum(enums.BillingErrorCode)
AppErrorCodeTransaction = graphene.Enum.from_enum(enums.TransactionErrorCode)
AppErrorCodeCommission = graphene.Enum.from_enum(enums.CommissionErrorCode)


class VendorError(Error):
    code = VendorErrorCode(description="The error code.", required=True)


class BillingError(Error):
    code = BillingErrorCode(description="The error code.", required=True)


class TransactionError(Error):
    code = AppErrorCodeTransaction(description="The error code.", required=True)


class CommissionError(Error):
    code = AppErrorCodeCommission(description="The error code.", required=True)
