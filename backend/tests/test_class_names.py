import unittest

from app.utils.class_names import to_display_name


class ClassNamesTestCase(unittest.TestCase):
    def test_to_display_name_translates_crop_and_condition(self):
        self.assertEqual(to_display_name("Tomato___Late_blight"), "番茄 - 晚疫病")
        self.assertEqual(to_display_name("Apple___healthy"), "苹果 - 健康")
        self.assertEqual(
            to_display_name("Tomato___Tomato_Yellow_Leaf_Curl_Virus"),
            "番茄 - 番茄黄化曲叶病毒病",
        )

    def test_to_display_name_handles_crop_only(self):
        self.assertEqual(to_display_name("Corn_(maize)"), "玉米")
        self.assertEqual(to_display_name("Blueberry"), "蓝莓")

    def test_to_display_name_fallback(self):
        self.assertEqual(to_display_name("Custom___Unknown_case"), "Custom - Unknown case")

