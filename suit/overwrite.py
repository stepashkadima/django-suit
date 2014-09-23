"""
Rewrite base django admin functions to enable integration with hvad translation.
Rewrited lines 30-35
"""
from __future__ import unicode_literals

from django.contrib.admin.views.main import (ORDER_VAR)
from django.utils.safestring import mark_safe

from django.contrib.admin.templatetags.admin_list import result_hidden_fields

from django.db import models
from django.db.models.related import RelatedObject
from django.forms.forms import pretty_name
from django.utils.html import format_html
from django.utils.encoding import force_str, force_text
from django.utils import six
<<<<<<< HEAD
from django.template import Library
import hvad.models

register = Library()

=======
import hvad.models

>>>>>>> e78e9e8a368390e6d8f84ecd8f453e62f4e15a4f
def label_for_field(name, model, model_admin=None, return_attr=False):
    """
    Returns a sensible label for a field name. The name can be a callable,
    property (but not created with @property decorator) or the name of an
    object's attribute, as well as a genuine fields. If return_attr is
    True, the resolved attribute (which could be a callable) is also returned.
    This will be None if (and only if) the name refers to a field.
    """
    attr = None
    try:
        # REWRITE:
        if isinstance(model, hvad.models.TranslatableModelBase):
            field = model._meta.translations_model._meta.get_field_by_name(name)[0]
        else:
            field = model._meta.get_field_by_name(name)[0]
        # REWRITE:
        if isinstance(field, RelatedObject):
            label = field.opts.verbose_name
        else:
            label = field.verbose_name
    except models.FieldDoesNotExist:
        if name == "__unicode__":
            label = force_text(model._meta.verbose_name)
            attr = six.text_type
        elif name == "__str__":
            label = force_str(model._meta.verbose_name)
            attr = bytes
        else:
            if callable(name):
                attr = name
            elif model_admin is not None and hasattr(model_admin, name):
                attr = getattr(model_admin, name)
            elif hasattr(model, name):
                attr = getattr(model, name)
            else:
                message = "Unable to lookup '%s' on %s" % (name, model._meta.object_name)
                if model_admin:
                    message += " or %s" % (model_admin.__class__.__name__,)
                raise AttributeError(message)

            if hasattr(attr, "short_description"):
                label = attr.short_description
            elif (isinstance(attr, property) and
                  hasattr(attr, "fget") and
                  hasattr(attr.fget, "short_description")):
                label = attr.fget.short_description
            elif callable(attr):
                if attr.__name__ == "<lambda>":
                    label = "--"
                else:
                    label = pretty_name(attr.__name__)
            else:
                label = pretty_name(name)
    if return_attr:
        return (label, attr)
    else:
        return label


def result_headers(cl):
    """
    Generates the list column headers.
    """
    ordering_field_columns = cl.get_ordering_field_columns()
    for i, field_name in enumerate(cl.list_display):
        text, attr = label_for_field(field_name, cl.model,
            model_admin = cl.model_admin,
            return_attr = True
        )
        if attr:
            # Potentially not sortable

            # if the field is the action checkbox: no sorting and special class
            if field_name == 'action_checkbox':
                yield {
                    "text": text,
                    "class_attrib": mark_safe(' class="action-checkbox-column"'),
                    "sortable": False,
                }
                continue

            admin_order_field = getattr(attr, "admin_order_field", None)
            if not admin_order_field:
                # Not sortable
                yield {
                    "text": text,
                    "class_attrib": format_html(' class="column-{0}"', field_name),
                    "sortable": False,
                }
                continue

        # OK, it is sortable if we got this far
        th_classes = ['sortable', 'column-{0}'.format(field_name)]
        order_type = ''
        new_order_type = 'asc'
        sort_priority = 0
        sorted = False
        # Is it currently being sorted on?
        if i in ordering_field_columns:
            sorted = True
            order_type = ordering_field_columns.get(i).lower()
            sort_priority = list(ordering_field_columns).index(i) + 1
            th_classes.append('sorted %sending' % order_type)
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]

        # build new ordering param
        o_list_primary = [] # URL for making this field the primary sort
        o_list_remove  = [] # URL for removing this field from sort
        o_list_toggle  = [] # URL for toggling order type for this field
        make_qs_param = lambda t, n: ('-' if t == 'desc' else '') + str(n)

        for j, ot in ordering_field_columns.items():
            if j == i: # Same column
                param = make_qs_param(new_order_type, j)
                # We want clicking on this header to bring the ordering to the
                # front
                o_list_primary.insert(0, param)
                o_list_toggle.append(param)
                # o_list_remove - omit
            else:
                param = make_qs_param(ot, j)
                o_list_primary.append(param)
                o_list_toggle.append(param)
                o_list_remove.append(param)

        if i not in ordering_field_columns:
            o_list_primary.insert(0, make_qs_param(new_order_type, i))


        yield {
            "text": text,
            "sortable": True,
            "sorted": sorted,
            "ascending": order_type == "asc",
            "sort_priority": sort_priority,
            "url_primary": cl.get_query_string({ORDER_VAR: '.'.join(o_list_primary)}),
            "url_remove": cl.get_query_string({ORDER_VAR: '.'.join(o_list_remove)}),
            "url_toggle": cl.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)}),
            "class_attrib": format_html(' class="{0}"', ' '.join(th_classes))
                            if th_classes else '',
        }


@register.inclusion_tag("admin/change_list_results.html")
def result_list(cl):
    """
    Displays the headers and data list together
    """
    headers = list(result_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': list(results(cl))}