import unittest
from sqlanalyzer import SqlQuery, InteractedSchemaElement


class TestAnalyzerUpdate(unittest.TestCase):

    def test_update_I(self):
        query_string = "UPDATE oc_user SET ip = '192.168.56.1 ' WHERE user_id = '1 '"
        query = SqlQuery(query_string)
        self.assertEqual(query._defines, [InteractedSchemaElement("oc_user", "ip", "attribute")])
        self.assertEqual(query._uses, [InteractedSchemaElement("oc_user", "user_id", "attribute")])

    def test_update_II(self):
        query_string = " UPDATE oc_product SET quantity = (quantity - 1) WHERE product_id = '41 ' AND subtract = '1 '"
        query = SqlQuery(query_string)
        self.assertEqual(query._defines,
                         [InteractedSchemaElement("oc_product", "quantity", "attribute")])
        self.assertEqual(query._uses,
                         [InteractedSchemaElement("oc_product", "product_id", "attribute"),
                          InteractedSchemaElement("oc_product", "subtract", "attribute")])


class TestAnalyzerInsert(unittest.TestCase):

    def test_insert_I(self):
        query_string = "INSERT INTO oc_product_description SET product_id = '42 ', language_id = '1 ',\
 name = 'Apple Cinema 30&quot; ', description = 'stuff', tag = ' ', meta_title = 'Bla ',\
 meta_description = ' ', meta_keyword = ' '"
        query = SqlQuery(query_string)
        self.assertEqual(query._defines, [InteractedSchemaElement("oc_product_description", "*", "relation")])
        self.assertEqual(query._uses, [])


class TestAnalyzerDelete(unittest.TestCase):

    def test_delete_I(self):
        query_string = "DELETE FROM oc_product_recurring WHERE product_id = 42"
        query = SqlQuery(query_string)
        self.assertEqual(query._defines, [InteractedSchemaElement("oc_product_recurring", "*", "relation")])
        self.assertEqual(query._uses, [InteractedSchemaElement("oc_product_recurring", "product_id", "attribute")])


class TestAnalyzerSelect(unittest.TestCase):

    def test_select_I(self):
        query_string = "SELECT * FROM oc_length_class mc LEFT JOIN oc_length_class_description mcd ON (mc.length_class_id = mcd.length_class_id) WHERE mcd.language_id = '1 '"
        query = SqlQuery(query_string)
        self.assertEqual(query._defines, [])
        self.assertEqual(query._uses, [InteractedSchemaElement("oc_length_class", "*", "attribute"),
                                       InteractedSchemaElement("oc_length_class", "length_class_id", "attribute"),
                                       InteractedSchemaElement("oc_length_class", "language_id", "attribute"),
                                       InteractedSchemaElement("oc_length_class_description", "length_class_id",
                                                               "attribute")])

    def test_select_II(self):
        query_string = "SELECT COUNT(*) AS total FROM oc_customer WHERE approved = '0 '"
        query = SqlQuery(query_string)
        self.assertEqual(query._defines, [])
        self.assertEqual(query._uses, [InteractedSchemaElement("oc_customer", "*", "attribute"),
                                       InteractedSchemaElement("oc_customer", "approved", "attribute")])
                
    def test_select_III(self):
        query_string = "SELECT permission FROM oc_user_group WHERE user_group_id = '1 '"
        query = SqlQuery(query_string)
        query = SqlQuery(query_string)
        self.assertEqual(query._defines, [])
        self.assertEqual(query._uses, [InteractedSchemaElement("oc_user_group", "permission", "attribute"),
                                       InteractedSchemaElement("oc_user_group", "user_group_id", "attribute")])
