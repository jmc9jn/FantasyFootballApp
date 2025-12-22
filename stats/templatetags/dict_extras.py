from django import template
register = template.Library()

@register.filter
def getattr_custom(obj, attr_name):
    """Safely get attribute from object in template"""
    return getattr(obj, attr_name, None)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def zip(a, b):
    return zip(a, b)

@register.tag(name="set")
def do_set(parser, token):
    """
    Usage: {% set var = value %}
    """
    bits = token.split_contents()

    if len(bits) != 4 or bits[2] != "=":
        raise template.TemplateSyntaxError(
            "Usage: {% set variable = value %}"
        )

    var_name = bits[1]
    value = parser.compile_filter(bits[3])
    return SetVarNode(var_name, value)


class SetVarNode(template.Node):
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

    def render(self, context):
        # Evaluate the value expression
        resolved_value = self.value.resolve(context)

        # Store it in context
        context[self.var_name] = resolved_value

        # Output nothing (this prevents recursion!)
        return ""