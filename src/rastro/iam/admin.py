from typing import TYPE_CHECKING, Any

from django import forms
from django.contrib import admin
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    ReadOnlyPasswordHashWidget,
)
from django.http import HttpRequest

from rastro.common.fields import parse_value_object
from rastro.iam import deps, services
from rastro.iam.models import Identity
from rastro.iam.values import RawPassword

if TYPE_CHECKING:
    _IdentityForm = forms.ModelForm[Identity]
    _IdentityAdmin = admin.ModelAdmin[Identity]
else:
    # django-stubs-ext is a dev dependency, so the runtime classes take no type argument.
    _IdentityForm = forms.ModelForm
    _IdentityAdmin = admin.ModelAdmin


class IdentityAddForm(_IdentityForm):
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    class Meta:
        model = Identity
        fields = ["email", "display_name"]

    def clean_password(self) -> RawPassword:
        password: RawPassword = parse_value_object(
            RawPassword, self.cleaned_data["password"]
        )
        return password


class PasswordHashWidget(ReadOnlyPasswordHashWidget):
    # The admin has no password change view, so the widget drops Django's reset button.
    template_name = "iam/widgets/password_hash.html"


class IdentityChangeForm(_IdentityForm):
    password = ReadOnlyPasswordHashField(widget=PasswordHashWidget)

    class Meta:
        model = Identity
        fields = [
            "email",
            "display_name",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
        ]


@admin.register(Identity)
class IdentityAdmin(_IdentityAdmin):
    form = IdentityChangeForm
    add_fieldsets = ((None, {"fields": ("email", "display_name", "password")}),)

    def get_fieldsets(self, request: HttpRequest, obj: Identity | None = None) -> Any:
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(
        self,
        request: HttpRequest,
        obj: Identity | None = None,
        change: bool = False,
        **kwargs: Any,
    ) -> Any:
        if obj is None:
            # fields=None keeps the add form's Meta.fields, so the raw password never reaches the instance.
            kwargs.update(form=IdentityAddForm, fields=None)
        return super().get_form(request, obj, change, **kwargs)

    def save_model(
        self, request: HttpRequest, obj: Identity, form: Any, change: bool
    ) -> None:
        if change:
            super().save_model(request, obj, form, change)
            return
        # The ModelForm's full_clean put the parsed value objects on obj.
        services.identity_register(
            email=obj.email,
            display_name=obj.display_name,
            password=form.cleaned_data["password"],
            password_hasher=deps.PASSWORD_HASHER,
        )
        # The admin needs the pk for its log entry and its redirect.
        obj.pk = Identity.objects.get(email=obj.email).pk
        obj.refresh_from_db()
