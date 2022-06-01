from enum import Enum

import graphene

from .. import models


class VendorErrorCode(Enum):
    UNKNOWN_ERROR = "unknown_error"
    EXISTING_VENDOR = "existing_vendor"
    INVALID_BRAND_NAME = "invalid_brand_name"
    INVALID_FIRST_NAME = "invalid_first_name"
    INVALID_LAST_NAME = "invalid_last_name"
    INVALID_VENDOR = "invalid_vendor"
    INVALID_SLUG = "invalid_slug"
    INVALID_PHONE_NUMBER = "invalid_phone_number"
    INVALID_EMAIL = "invalid_email"
    INVALID_REGISTRATION_NUMBER = "invalid_registration_number"
    INVALID_VAT = "invalid_vat"
    INVALID_RESIDENCE_ID = "invalid_residence_id"
    INVALID_NATIONAL_ID = "invalid_national_id"
    MISSING_VAT = "missing_vat"
    INVALID_FIELD_VALUE = "invalid_field_value"
    ONLY_ONE_ALLOWED = "only_one_allowed"
    INVALID_IMAGE_URL = "image_url"
    REQUIRED = "required"


class BillingErrorCode(Enum):

    BILLING_ERROR = "invalid_billing_info"
    INVALID_IBAN = "invalid_iban"
    INVALID_BANK_NAME = "invalid_bank_name"
    REQUIRED = "required"


TargetGender = graphene.Enum.from_enum(models.Vendor.TargetGender)
RegistrationType = graphene.Enum.from_enum(models.Vendor.RegistrationType)


class TransactionErrorCode(Enum):
    TRANSACTION_NOT_FOUND = "Transaction_not_found"
    TRANSACTION_ERROR = "Transaction_error"
    REQUIRED = "required"


class TransactionTypeEnum(graphene.Enum):
    PENDING = 1
    ACAILABLE = 2
    COMPLETED = 3
    CANCELLED = 4


class TransactionReasonEnum(graphene.Enum):
    ORDER_PLACEMENT = 1
    ADJUSTMENT = 2
    WITHDRAW = 3
    PENALTY = 4


class CommissionErrorCode(Enum):
    COMMISSION_NOT_FOUND = "Commission_not_found"
    COMMISSION_ERROR = "Commission_error"
    REQUIRED = "required"


class CommissionTypeEnum(graphene.Enum):
    FIXED = 1
    PERCENTAGE = 2
