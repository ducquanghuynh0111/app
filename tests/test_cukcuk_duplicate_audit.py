import unittest

from audit_cukcuk_duplicates import duplicate_names


class CukcukDuplicateAuditTests(unittest.TestCase):
    def test_groups_case_and_accent_variants_without_merging_other_dishes(self):
        rows = [
            {"Name": "Mì xào hải sản", "Code": "MXHS"},
            {"Name": "MÌ XÀO HẢI SẢN", "Code": "MIXAHASA"},
            {"Name": "Mì xào bò", "Code": "MXB"},
        ]
        duplicates, missing = duplicate_names(rows)
        self.assertEqual(missing, 0)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["codes"], ["MIXAHASA", "MXHS"])


if __name__ == "__main__":
    unittest.main()
