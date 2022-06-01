from setuptools import setup

setup(
    name="vendor",
    version="0.1.0",
    packages=["vendor"],
    package_dir={"vendor": "vendor"},
    description="OTP plugin",
    install_requires=["django_iban", "graphene_federation"],
    entry_points={
        "saleor.plugins": ["vendor = vendor.plugin:VendorPlugin"],
    },
)
