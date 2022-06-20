import mimetypes
import os.path
import re
import secrets
import urllib.request

import graphene
import phonenumbers
import requests
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import validate_email
from phonenumber_field.phonenumber import PhoneNumber
from saleor.graphql.account.enums import CountryCodeEnum
from saleor.graphql.core.mutations import ModelDeleteMutation, ModelMutation
from saleor.graphql.core.types import Upload
from saleor.graphql.core.utils import (
    from_global_id_or_error,
    validate_slug_and_generate_if_needed,
)

from vendor import models
from vendor.graphql import enums, types
from vendor.graphql.errors import (
    BillingError,
    CommissionError,
    TransactionError,
    VendorError,
)

numbers_only = re.compile("[0-9]+")


def get_filename_from_url(url: str):
    """Prepare unique filename for file from URL to avoid overwritting."""
    file_name = os.path.basename(url)
    name, format = os.path.splitext(file_name)
    hash = secrets.token_hex(nbytes=4)
    return f"{name}_{hash}{format}"


def is_image_url(url: str):
    """Check if file URL seems to be an image."""
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"}
    )
    r = urllib.request.urlopen(req)
    if "image" in r.getheader("Content-Type"):
        return True
    filetype = mimetypes.guess_type(url)[0]
    return filetype is not None


def upload_image(image_data, image_name):
    image_file = File(image_data.raw, image_name)
    errors = {}
    if image_file:
        return image_file
    else:
        errors["image_url"] = ValidationError(
            "Invalid  image url.",
            code=enums.VendorErrorCode.INVALID_IMAGE_URL,
        )
        raise ValidationError(errors)


def is_numbers_only(s):
    return numbers_only.match(s)


class VendorInput(graphene.InputObjectType):
    brand_name = graphene.String(description="The name of the brand.", required=True)
    first_name = graphene.String(description="First Name.", required=True)
    last_name = graphene.String(description="Last Name.", required=True)

    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )

    is_active = graphene.Boolean(
        description="Active status of the vendor.", default_value=True
    )

    description = graphene.JSONString(
        description="Description of the vendor.", required=False
    )

    country = CountryCodeEnum(description="Country code.", required=True)
    users = graphene.List(
        graphene.ID,
        description="Users IDs to add to the vendor.",
    )

    target_gender = enums.TargetGender(
        description="The target gender of the vendor, defaults to UNISEX.",
        default=models.Vendor.TargetGender.UNISEX,  # TODO
        required=False,
    )

    national_id = graphene.String(description="National ID.", required=False)
    residence_id = graphene.String(description="Residence ID.", required=False)

    vat_number = graphene.String(required=False)

    logo = Upload(description="Vendor logo")
    header_image = Upload(required=False, description="Header image.")

    facebook_url = graphene.String(description="Facebook page URL.", required=False)
    instagram_url = graphene.String(description="Instagram page URL.", required=False)
    youtube_url = graphene.String(description="YouTube channel URL.", required=False)
    twitter_url = graphene.String(description="Twitter profile URL.", required=False)


class VendorCreateInput(VendorInput):
    brand_name = graphene.String(description="The name of the brand.", required=True)
    first_name = graphene.String(description="First Name.", required=True)
    last_name = graphene.String(description="Last Name.", required=True)

    phone_number = graphene.String(description="Contact phone number.", required=True)
    email = graphene.String(description="Contact email.", required=True)

    registration_type = enums.RegistrationType(
        description="The registration type of the company.", required=True
    )

    registration_number = graphene.String(
        required=True, description="The registration number."
    )


class VendorCreate(ModelMutation):
    class Arguments:
        input = VendorCreateInput(
            required=True, description="Fields required to create a vendor."
        )

    class Meta:
        description = "Create a new vendor."
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        errors = {}

        brand_name = data["brand_name"]
        if len(brand_name) == 0:
            errors["brand_name"] = ValidationError(
                "Invalid brand name.",
                code=enums.VendorErrorCode.INVALID_BRAND_NAME,
            )

        else:
            try:
                models.Vendor.objects.get(brand_name=brand_name)
                errors["brand_name"] = ValidationError(
                    message="A vendor with the same name already exists.",
                    code=enums.VendorErrorCode.EXISTING_VENDOR,
                )
            except models.Vendor.DoesNotExist:
                pass

        if len(data["first_name"]) == 0:
            errors["first_name"] = ValidationError(
                "Invalid first name.",
                code=enums.VendorErrorCode.INVALID_FIRST_NAME,
            )

        if len(data["last_name"]) == 0:
            errors["last_name"] = (
                ValidationError(
                    message="Invalid last name.",
                    code=enums.VendorErrorCode.INVALID_LAST_NAME,
                ),
            )

        if email := data.get("email"):
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = ValidationError(
                    "Provided email is invalid.",
                    code=enums.VendorErrorCode.INVALID_EMAIL,
                )

        try:
            phone_number = data["phone_number"]
            PhoneNumber.from_string(phone_number).is_valid()
        except phonenumbers.phonenumberutil.NumberParseException as e:
            errors["phone_number"] = ValidationError(
                str(e), code=enums.VendorErrorCode.INVALID_PHONE_NUMBER
            )

        residence_id = data.get("residence_id")
        national_id = data.get("national_id")

        if residence_id and national_id:
            raise ValidationError(
                message="You must only provide one of residence ID and national ID.",
                code=enums.VendorErrorCode.ONLY_ONE_ALLOWED,
            )

        if not residence_id and not national_id:
            raise ValidationError(
                message="You must provider either residence ID or national ID.",
                code=enums.VendorErrorCode.ONLY_ONE_ALLOWED,
            )

        if residence_id and not is_numbers_only(residence_id):
            errors["residence_id"] = ValidationError(
                message=f"Residence ID must contain only numbers, found: {residence_id}.",  # noqa: E501
                code=enums.VendorErrorCode.INVALID_RESIDENCE_ID,
            )

        if national_id and not is_numbers_only(national_id):
            errors["national_id"] = ValidationError(
                message=f"National ID must contain only numbers, found: {national_id}.",  # noqa: E501
                code=enums.VendorErrorCode.INVALID_NATIONAL_ID,
            )

        registration_type = data["registration_type"]
        if registration_type == enums.RegistrationType.COMPANY:
            vat_number = data.get("vat_number")

            if not vat_number:
                errors["vat_number"] = ValidationError(
                    message="You must provide a VAT for companies.",
                    code=enums.VendorErrorCode.MISSING_VAT,
                )

            elif not is_numbers_only(vat_number):
                errors["vat_number"] = ValidationError(
                    message=f"VAT number must contain only numbers, found: {vat_number}.",  # noqa: E501
                    code=enums.VendorErrorCode.INVALID_VAT,
                )

        registration_number = data["registration_number"]
        if len(registration_number) == 0:
            errors["registration_number"] = ValidationError(
                "Invalid registration number.",
                code=enums.VendorErrorCode.INVALID_REGISTRATION_NUMBER,
            )

        try:
            validate_slug_and_generate_if_needed(instance, "brand_name", cleaned_input)
        except ValidationError as error:
            error.code = enums.VendorErrorCode.INVALID_SLUG
            errors["slug"] = error

        if errors:
            raise ValidationError(errors)

        return cleaned_input


class VendorUpdateInput(VendorInput):
    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )

    phone_number = graphene.String(description="Contact phone number.", required=False)
    email = graphene.String(description="Contact email.", required=False)

    registration_type = enums.RegistrationType(
        description="The registration type of the company.", required=False
    )
    registration_number = graphene.String(
        description="The registration number.", required=False
    )
    country = CountryCodeEnum(description="Country code.", required=False)


class VendorUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        input = VendorUpdateInput(
            description="Fields required to update the vendor.", required=True
        )

    class Meta:
        description = "Update a vendor."
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor


class VendorDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")

    class Meta:
        description = "Delete the vendor."
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor


class BillingInfoCreateInput(graphene.InputObjectType):
    iban = graphene.String(description="IBAN number of the vendor.", required=True)
    bank_name = graphene.String(description="The bank name.", required=True)
    account_holder_name = graphene.String(description="The account holder name.")
    bank_address = graphene.String(description="The bank address.", required=True)
    bank_country = CountryCodeEnum(description="Country code.", required=True)
    bank_city = graphene.String(description="The bank city.")
    bank_zipcode = graphene.String(description="The bank zipcode.")
    bank_area = graphene.String(description="The bank area.")


class BillingInfoCreate(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(required=True, description="Vendor ID.")
        input = BillingInfoCreateInput(
            required=True,
            description="Fields required to add billing information to the vendor.",
        )

    class Meta:
        description = "Create a new billing information for a vendor."
        model = models.BillingInfo
        error_type_class = BillingError
        object_type = types.Billing

    @classmethod
    def clean_input(cls, info, instance, data):
        validation_errors = {}
        if len(data["input"]["iban"]) == 0:
            validation_errors["iban"] = ValidationError(
                "Invalid first name.",
                code=enums.BillingErrorCode.INVALID_IBAN,
            )

        if len(data["input"]["bank_name"]) == 0:
            validation_errors["bank_name"] = (
                ValidationError(
                    message="Invalid last name.",
                    code=enums.BillingErrorCode.INVALID_BANK_NAME,
                ),
            )
        if validation_errors:
            raise ValidationError(validation_errors)
        return data["input"]

    @classmethod
    def perform_mutation(cls, root, info, **data):
        vendor = cls.get_node_or_error(info, data["vendor_id"], only_type=types.Vendor)
        billing_info = models.BillingInfo.objects.create(**data["input"], vendor=vendor)

        return cls(**{cls._meta.return_field_name: billing_info})


class BillingInfoUpdateInput(graphene.InputObjectType):
    iban = graphene.String(description="IBAN number of the vendor.")
    bank_name = graphene.String(description="The bank name.")
    account_holder_name = graphene.String(description="The account holder name.")
    bank_address = graphene.String(description="The bank address.")
    bank_country = CountryCodeEnum(description="Country code.")
    bank_city = graphene.String(description="The bank city.")
    bank_zipcode = graphene.String(description="The bank zipcode.")
    bank_area = graphene.String(description="The bank area.")


class BillingInfoUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")
        input = BillingInfoUpdateInput(
            description="Fields required to update billing information.", required=True
        )

    class Meta:
        description = "Update billing information."
        model = models.BillingInfo
        error_type_class = VendorError
        object_type = types.Billing

    @classmethod
    def perform_mutation(cls, root, info, **data):
        _, id = from_global_id_or_error(data["id"], types.Billing)
        billing_info = models.BillingInfo.objects.get(id=id)
        for k, v in data.items():
            billing_info.k = v
        billing_info.save()
        return cls(**{cls._meta.return_field_name: billing_info})


class BillingInfoDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")

    class Meta:
        description = "Delete billing information for a vendor."
        model = models.BillingInfo
        error_type_class = VendorError
        object_type = types.Billing


class VendorAddAttachment(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(required=True, description="Vendor ID.")
        file = Upload(required=True, description="File to be attached")

    class Meta:
        description = "Add an attachment file to the vendor"
        model = models.Attachment
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, vendor_id, file):
        vendor = cls.get_node_or_error(info, "vendor_id", only_type="Vendor")
        attachment = models.Attachment.objects.create(
            vendor=vendor, file=file
        )  # can be optimized

        return cls(attachment=attachment)


class VendorRemoveAttachment(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID()

    class Meta:
        description = "Remove an attachment from a vendor"
        model = models.Attachment
        error_type_class = VendorError
        object_type = types.Vendor


class VendorUpdateLogo(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        image_url = graphene.String(required=True, description="Logo image.")

    class Meta:
        description = "Update vendor logo image"
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, id, image_url):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        errors = {}
        if is_image_url(image_url) and vendor:
            logo_name = get_filename_from_url(image_url)
            try:
                image_data = requests.get(image_url, stream=True)
                image_file = upload_image(image_data, logo_name)
                vendor.logo = image_file
                vendor.save()

            except Exception:
                errors["image_url"] = ValidationError(
                    "Invalid  image url.",
                    code=enums.VendorErrorCode.INVALID_IMAGE_URL,
                )

        else:
            errors["image_url"] = ValidationError(
                "Invalid  image url.",
                code=enums.VendorErrorCode.INVALID_IMAGE_URL,
            )

        if errors:
            raise ValidationError(errors)

        return cls(vendor=vendor)


class VendorUpdateHeader(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        image_url = graphene.String(required=True, description="Header image.")

    class Meta:
        description = "Update vendor header image"
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, id, image_url):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        errors = {}
        if is_image_url(image_url) and vendor:
            header_name = get_filename_from_url(image_url)
            try:
                image_data = requests.get(image_url, stream=True)
                image_file = upload_image(image_data, header_name)
                vendor.header_image = image_file
                vendor.save()

            except Exception:
                errors["image_url"] = ValidationError(
                    "Invalid  image url.",
                    code=enums.VendorErrorCode.INVALID_IMAGE_URL,
                )

        else:
            errors["image_url"] = ValidationError(
                "Invalid  image url.",
                code=enums.VendorErrorCode.INVALID_IMAGE_URL,
            )

        if errors:
            raise ValidationError(errors)

        return cls(vendor=vendor)


class VendorAddProduct(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        product_id = graphene.ID(required=True, description="Product ID.")

    class Meta:
        description = "Add a product to vendor catalogue"
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, id, product_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        product = cls.get_node_or_error(info, product_id, only_type="Product")
        vendor.products.add(product)
        info.context.plugins.product_updated(product)
        return cls(vendor=vendor)


class VendorRemoveProduct(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        product_id = graphene.ID(required=True, description="Product ID.")

    class Meta:
        description = "Add a product to vendor catalogue"
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, id, product_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        product = cls.get_node_or_error(info, product_id, only_type="Product")
        vendor.products.remove(product)
        info.context.plugins.product_updated(product)
        return cls(vendor=vendor)


class VendorAddUser(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        user_id = graphene.ID(required=True, description="User ID.")

    class Meta:
        description = "Add a user to a vendor."
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, id, user_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        user = cls.get_node_or_error(info, user_id, only_type="User")
        vendor.users.add(user)
        return cls(vendor=vendor)


class VendorRemoveUser(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        user_id = graphene.ID(required=True, description="User ID.")

    class Meta:
        description = "Remove a user from a vendor."
        model = models.Vendor
        error_type_class = VendorError
        object_type = types.Vendor

    @classmethod
    def perform_mutation(cls, _root, info, id, user_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        user = cls.get_node_or_error(info, user_id, only_type="User")
        vendor.users.remove(user)
        return cls(vendor=vendor)


class TransactionInput(graphene.InputObjectType):
    description = graphene.String(
        description="description of the Transaction", required=False
    )
    note = graphene.String(description="note of the Transaction", required=False)
    transaction_status = graphene.Int(description="enter the choice for you")
    reason = graphene.Int(description="enter the choice for you")
    currency = graphene.String(description="the currency for your ammoutn")
    price_amount = graphene.Int(description="ammout of Transaction")


class VendorTransactionCreateInput(TransactionInput):
    name = graphene.String(description="name of the Commission", required=True)


class VendorTransactionCreate(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(required=True, description="Vendor ID.")
        input = VendorTransactionCreateInput(
            required=True, description="Fields required to create Transaction"
        )

    class Meta:
        description = "create new Transaction"
        model = models.Transaction
        error_type_class = TransactionError
        object_type = types.VendorTransaction

    @classmethod
    def perform_mutation(cls, root, info, **data):
        vendor = cls.get_node_or_error(info, data["vendor_id"], only_type=types.Vendor)
        transaction = models.Transaction.objects.create(**data["input"], vendor=vendor)

        return cls(**{cls._meta.return_field_name: transaction})


class VendorTransactionUpdateInput(TransactionInput):
    name = graphene.String(description="name of the Commission", required=False)


class VendorTransactionUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="id of Transaction to update")
        input = VendorTransactionUpdateInput(
            description="Fields to update a transaction", required=True
        )

    class Meta:
        description = "Update a Transaction"
        model = models.Transaction
        error_type_class = TransactionError
        object_type = types.VendorTransaction


class TransactionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="id of transaction to delete")

    class Meta:
        description = "Delete the Transaction"
        model = models.Transaction
        error_type_class = TransactionError
        object_type = types.VendorTransaction


class TransactionAddPayment(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Transaction ID.")
        payment_id = graphene.ID(required=True, description="Payment ID.")

    class Meta:
        description = "Add a payment to transaction catalogue"
        model = models.Transaction
        error_type_class = TransactionError
        object_type = types.VendorTransaction

    @classmethod
    def perform_mutation(cls, _root, info, id, payment_id):
        transaction = cls.get_node_or_error(info, id, only_type="VendorTransaction")
        payment = cls.get_node_or_error(info, payment_id, only_type="Payment")
        transaction.payment = payment
        transaction.save()
        return cls(transaction=transaction)


class TransactionAddUser(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Transaction ID.")
        user_id = graphene.ID(required=True, description="User ID.")

    class Meta:
        description = "Add a user to transaction catalogue"
        model = models.Transaction
        error_type_class = TransactionError
        object_type = types.VendorTransaction

    @classmethod
    def perform_mutation(cls, _root, info, id, user_id):
        transaction = cls.get_node_or_error(info, id, only_type="Transaction")
        user = cls.get_node_or_error(info, user_id, only_type="User")
        transaction.user = user
        transaction.save()
        return cls(transaction=transaction)


class CommissionInput(graphene.InputObjectType):
    name = graphene.String(description="name of the Commission")
    description = graphene.String(
        description="description of the Commission", required=False
    )
    type = graphene.Int(description="enter the choice for you")
    currency = graphene.String(description="the currency for your ammoutn")
    price_amount = graphene.Int(description="ammout of commission")


class CommissionCreateInput(CommissionInput):
    name = graphene.String(description="name of the Commission", required=True)


class CommissionCreate(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(
            required=True, description="ID of the vendor related to Commission"
        )
        input = CommissionCreateInput(
            required=True, description="Fields required to create Commission"
        )

    class Meta:
        description = "create new Commission"
        model = models.Commission
        error_type_class = CommissionError
        object_type = types.Commission

    @classmethod
    def clean_input(cls, info, instance, data):
        validation_errors = {}
        for field in ["name", "type", "currency", "price_amount"]:
            if data["input"][field] == "":
                validation_errors[field] = ValidationError(
                    f"{field} cannot be empty.",
                    code=enums.CommissionErrorCode.COMMISSION_ERROR,
                )
        if validation_errors:
            raise ValidationError(validation_errors)
        return data["input"]

    @classmethod
    def perform_mutation(cls, root, info, **data):

        vendor = cls.get_node_or_error(
            info, data["vendor_id"], only_type=types.Vendor, field="vendorId"
        )
        cleaned_input = cls.clean_input(info, vendor, data)
        commission = models.Commission(**cleaned_input)

        commission.vendor = vendor
        commission.save()
        return CommissionCreate(commission=commission)


class CommissionUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a Commission to update")
        input = CommissionInput(
            description="Fields required to update a Commission", required=True
        )

    class Meta:
        description = "Update a Commission"
        model = models.Commission
        error_type_class = CommissionError
        object_type = types.Commission


class CommissionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of Commission to delete")

    class Meta:
        description = "delete the Commission"
        model = models.Commission
        error_type_class = CommissionError
        object_type = types.Commission


class CommissionAddCategory(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Commission ID.")
        category_id = graphene.ID(required=True, description="Category ID.")

    class Meta:
        description = "Add a category to category "
        model = models.Commission
        error_type_class = CommissionError
        object_type = types.Commission

    @classmethod
    def perform_mutation(cls, _root, info, id, category_id):
        commission = cls.get_node_or_error(info, id, only_type="Commission")
        category = cls.get_node_or_error(info, category_id, only_type="Category")
        commission.category = category
        commission.save()
        return cls(commission=commission)


class CommissionRemoveCategory(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Commission ID.")

    class Meta:
        description = "Add a category to commission "
        model = models.Commission
        error_type_class = CommissionError
        object_type = types.Commission

    @classmethod
    def perform_mutation(cls, _root, info, id):
        commission = cls.get_node_or_error(info, id, only_type="Commission")
        commission.category = None
        commission.save()
        return cls(commission=commission)
