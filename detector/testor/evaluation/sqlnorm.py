import hashlib
import sqlparse


def remove_whitespaces(tree):
    if tree.is_group:
        tree.tokens = [remove_whitespaces(element)
                       for element in tree.tokens
                       if not element.is_whitespace]

    return tree


def remove_rhs_values_sub(element):
    if type(element) is sqlparse.sql.Comparison:
        # delete any value as this might be different
        # to eq queries in diff context
        element.tokens.remove(element.right)
        return element

    if type(element) is sqlparse.sql.Assignment:
        raise NameError('Unexpected assignment operator SQL')

    return element


def remove_rhs_values(tree):
    if tree.is_group:
        tree.tokens = [remove_rhs_values(element)
                       for element in
                       [remove_rhs_values_sub(element)
                        for element in tree.tokens]]
        return tree  # this return just looks pretty

    return tree


def remove_right_side_of_values(tree):
    position = -1
    for element in tree.tokens:
        position = position + 1
        if element.match(sqlparse.tokens.Keyword, ["VALUES"]):
            break

    if position != -1:
        tree.tokens = tree.tokens[0:position + 1]

    return tree


def order_alphabetically(tree):
    if tree.is_group:
        tree.tokens = sorted([order_alphabetically(element)
                              for element in tree.tokens],
                             key=lambda el: el.value)

    return tree


def remove_single_strings(tree):
    if tree.is_group:
        tree.tokens = [remove_single_strings(element)
                       for element in tree.tokens
                       if not element.ttype == sqlparse.tokens.String.Single]
    return tree


def normalize_query_syntax_tree(tree):
    return order_alphabetically(
        remove_single_strings(
            remove_right_side_of_values(
                remove_rhs_values(remove_whitespaces(tree)))))
    # return remove_rhs_values(remove_whitespaces(tree))
    # return remove_rhs_values(tree)


def debug_remove_only_rhs_whitespaces(query_string):
    tree = sqlparse.parse(query_string)[0]
    return remove_single_strings(remove_rhs_values(remove_whitespaces(tree)))


def generate_normalized_query_hash(query_string):
    # query_string = query_string.replace("`", "")
    return hashlib.md5(normalize_query_syntax_tree(
        sqlparse.parse(query_string)[0]).__str__()).hexdigest()


def generate_query_hash(query_string):
    return hashlib.md5(query_string).hexdigest()


# DO FUCKING NOT! I REPEAT DO BLOODY FUCKING NOT CHANGE ANYTHING HERE BEFOR ALSO
# CHANGING IT IN THE INTERCEPTOR AND REBUILDING THE .pex
