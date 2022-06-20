from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django_countries.fields import CountryField
from django_iban.fields import IBANField
from django_prices.models import MoneyField
from phonenumber_field.modelfields import PhoneNumberField
from saleor.account.models import Address
from saleor.account.validators import validate_possible_number
from saleor.core.db.fields import SanitizedJSONField
from saleor.core.utils.editorjs import clean_editor_js
from saleor.payment.models import Payment
from saleor.product.models import Product

User = get_user_model()


class PossiblePhoneNumberField(PhoneNumberField):
    # """Less strict field for phone numbers written to database"""

    default_validators = [validate_possible_number]


class Vendor(models.Model):
    class RegistrationType(models.IntegerChoices):
        COMPANY = 1
        MAROOF = 2

    class TargetGender(models.IntegerChoices):
        MEN = 1
        WOMEN = 2
        UNISEX = 3

    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)

    brand_name = models.CharField(max_length=256, unique=True, db_index=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    slug = models.SlugField(max_length=256, unique=True, db_index=True)

    users = models.ManyToManyField(User)
    products = models.ManyToManyField(Product)

    country = CountryField()

    phone_number = PossiblePhoneNumberField(
        db_index=True, unique=False, blank=True, null=True
    )
    email = models.EmailField(db_index=True, unique=True, null=True)

    national_id = models.CharField(max_length=256, null=True, blank=True)
    residence_id = models.CharField(max_length=256, null=True, blank=True)

    is_active = models.BooleanField()
    registration_type = models.IntegerField(
        choices=RegistrationType.choices, default=RegistrationType.COMPANY
    )
    registration_number = models.CharField(max_length=256)
    vat_number = models.CharField(max_length=256, blank=True, null=True)

    target_gender = models.IntegerField(
        choices=TargetGender.choices, default=TargetGender.UNISEX
    )

    logo = models.ImageField(blank=True, null=True)
    header_image = models.ImageField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)

    address = models.OneToOneField(
        Address, on_delete=models.SET_NULL, blank=True, null=True
    )

    def __str__(self):
        return self.brand_name


class BillingInfo(models.Model):
    iban = IBANField()
    bank_name = models.CharField(max_length=256)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="billing_info"
    )
    account_holder_name = models.CharField(max_length=256, blank=True, null=True)
    bank_address = models.CharField(max_length=256, blank=True, null=True)
    bank_country = CountryField(default=[])
    bank_city = models.CharField(max_length=256, blank=True, null=True)
    bank_zipcode = models.CharField(max_length=256, blank=True, null=True)
    bank_area = models.CharField(max_length=256, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Attachment(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField()

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1
        ACAILABLE = 2
        COMPLETED = 3
        CANCELLED = 4

    class Reason(models.IntegerChoices):
        ORDER_PLACEMENT = 1
        ADJUSTMENT = 2
        WITHDRAW = 3
        PENALTY = 4

    name = models.CharField(max_length=256, db_index=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="transaction",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transaction",
        blank=True,
        null=True,
    )
    transaction_status = models.IntegerField(
        choices=Status.choices, default=Status.PENDING
    )
    description = models.TextField(blank=True, default="")
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH, default="SAR"
    )
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    value = MoneyField(amount_field="price_amount", currency_field="currency")
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="transaction",
        blank=True,
        null=True,
    )
    note = models.TextField(blank=True, default="")
    reason = models.IntegerField(choices=Status.choices, default=Reason.ORDER_PLACEMENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Commission(models.Model):
    class Type(models.IntegerChoices):
        FIXED = 1
        PERCENTAGE = 2

    name = models.CharField(max_length=256, db_index=True)
    description = models.TextField(blank=True, default="")
    type = models.IntegerField(choices=Type.choices, default=Type.FIXED)
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH, default="SAR"
    )
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    value = MoneyField(amount_field="price_amount", currency_field="currency")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    category = models.ForeignKey(
        "product.Category", blank=True, null=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
